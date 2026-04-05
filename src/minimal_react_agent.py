from __future__ import annotations

import ast
import operator
import os
import time

import google.generativeai as genai

GEMINI_API_KEY_INLINE = ""


def get_api_key(name: str) -> str | None:
    try:
        from google.colab import userdata
    except ImportError:
        return os.environ.get(name)
    try:
        return userdata.get(name)
    except Exception as e:
        if type(e).__name__ in ("SecretNotFoundError", "NotebookAccessError"):
            return None
        raise


def _prompt_gemini_key_in_colab() -> str | None:
    try:
        import google.colab  # noqa: F401
    except ImportError:
        return None
    print(
        "No Gemini API key found. Paste below (session only) or use Colab GEMINI_API_KEY secret / GEMINI_API_KEY_INLINE."
    )
    k = input("GEMINI_API_KEY: ").strip()
    if k:
        os.environ["GEMINI_API_KEY"] = k
    return k or None


def setup():
    key = (
        get_api_key("GEMINI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or (GEMINI_API_KEY_INLINE.strip() or None)
    )
    if not key:
        key = _prompt_gemini_key_in_colab()
    if not key:
        raise RuntimeError(
            "Set GEMINI_API_KEY (Colab Secret, env, or GEMINI_API_KEY_INLINE in this file)."
        )
    genai.configure(api_key=key)
    # gemini-1.5-flash was removed from v1beta for many keys; use current stable Flash.
    model_id = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    return genai.GenerativeModel(model_id)


def calculator(expr: str) -> str:
    expr = expr.strip()
    if not expr:
        return "Error: empty"
    binops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }
    uops = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.BinOp):
            return binops[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp):
            return uops[type(n.op)](ev(n.operand))
        raise ValueError("not allowed")

    try:
        return str(ev(ast.parse(expr, mode="eval").body))
    except Exception as e:
        return f"Error: {e}"


def _format_ddgs_rows(rows: list) -> str:
    parts = []
    for i, r in enumerate(rows, 1):
        t = r.get("title", "")
        b = (r.get("body") or "")[:350]
        u = r.get("href", "")
        parts.append(f"{i}. {t}\n{b}\nURL: {u}")
    return "DDGS:\n" + "\n\n".join(parts)


def web_search(query: str) -> str:
    query = query.strip()
    if not query:
        return "Error: empty query"

    try:
        from ddgs import DDGS

        rows = DDGS(timeout=20).text(query, max_results=4)
        if not rows:
            return "Error: web_search returned no results. Try a shorter or different query."
        return _format_ddgs_rows(rows)
    except Exception as e:
        return f"Error: web_search failed: {e}"


def run_tool(action_line: str, action_input: str) -> str:
    a = action_line.lower()
    if "web_search" in a:
        return web_search(action_input)
    if "calculator" in a:
        return calculator(action_input)
    return "Unknown Action (use web_search or calculator)"


PROMPT = """You are a ReAct agent.

Tools:
- web_search — Action Input: short search query for current facts / news.
- calculator — Action Input: one math expression.

Question: {q}

Thought: ...
Action: web_search OR calculator
Action Input: ...

One Action per turn. After Observation, continue until you can answer, then:

Final Answer: ...

Do not invent Observation text; use tools when you lack facts.
"""


def _is_transient_api_error(exc: BaseException) -> bool:
    """Colab / REST transport sometimes drops the connection between calls."""
    n = type(exc).__name__.lower()
    if n in (
        "connectionerror",
        "protocolerror",
        "remotedisconnected",
        "chunkedencodingerror",
        "readtimeout",
        "connecttimeout",
        "serviceunavailable",
        "internalservererror",
        "gatewaytimeout",
        "deadlineexceeded",
    ):
        return True
    s = str(exc).lower()
    return any(
        x in s
        for x in (
            "remote end closed",
            "connection aborted",
            "connection reset",
            "timed out",
            "timeout",
            "temporarily unavailable",
            "500",
            "503",
            "504",
        )
    )


def ask_model(model, text: str, max_retries: int = 5) -> str:
    cfg = genai.types.GenerationConfig(stop_sequences=["Observation:"])
    last: BaseException | None = None
    for attempt in range(max_retries):
        try:
            r = model.generate_content(
                text,
                generation_config=cfg,
                request_options={"timeout": 180},
            )
            return (r.text or "").strip()
        except Exception as e:
            last = e
            if _is_transient_api_error(e) and attempt < max_retries - 1:
                wait = min(30.0, 2.0**attempt)
                print(
                    f"\n[System] Gemini request failed ({type(e).__name__}), "
                    f"retry {attempt + 1}/{max_retries} in {wait:.0f}s…"
                )
                time.sleep(wait)
                continue
            raise
    assert last is not None
    raise last


def parse_action(block: str):
    act, inp = None, None
    for line in block.splitlines():
        low = line.lower()
        if low.startswith("action:"):
            act = line.split(":", 1)[1].strip()
        if low.startswith("action input:"):
            inp = line.split(":", 1)[1].strip()
    return act, inp


def react(question: str, model=None, max_steps: int = 8, sleep: float = 1.0):
    if model is None:
        model = setup()

    full_prompt = PROMPT.format(q=question)
    trace: list[tuple[str, str | None]] = []

    for i in range(1, max_steps + 1):
        out = ask_model(model, full_prompt)
        print(f"\n--- Step {i} ---\n{out}")

        if "final answer:" in out.lower():
            ans = ""
            for line in out.splitlines():
                if line.strip().lower().startswith("final answer:"):
                    ans = line.split(":", 1)[1].strip()
            if not ans:
                ans = out.split("final answer:", 1)[-1].strip()
            print("\n" + "=" * 20 + " RESULT " + "=" * 20)
            print(ans)
            print("=" * 20 + " SUMMARY " + "=" * 19)
            for j, (t, ob) in enumerate(trace, 1):
                print(f"\nStep {j} (model):\n{t[:1200]}")
                if ob:
                    o = ob if len(ob) < 500 else ob[:500] + "..."
                    print(f"Observation: {o}")
            print("=" * 50)
            return ans

        act, a_in = parse_action(out)
        if not act or not a_in:
            print("Stopped: could not parse Action / Action Input.")
            return None

        obs = run_tool(act, a_in)
        clip = 1500
        print(f"\n[System] Observation:\n{obs[:clip]}{'...' if len(obs) > clip else ''}\n")
        trace.append((out, obs))
        full_prompt = full_prompt + "\n" + out + "\nObservation: " + obs + "\n"
        time.sleep(sleep)

    print("Stopped: max steps.")
    return None


if __name__ == "__main__":
    react("What is 121 * 160? Use the calculator tool.")
