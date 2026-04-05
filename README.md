# # Roushath- Frontend Dev-ReAct Agent - Minimal Python ReAct Agent

This repository is documented around a single module: **`src/minimal_react_agent.py`**.

It implements a **ReAct** loop with **Gemini**: the model writes **Thought → Action → Action Input**, Python runs a **tool** and feeds back **Observation**, until the model outputs **Final Answer**. Works **locally** or in **Google Colab**.

---

## What you need (`requirements.txt`)

```bash
pip install -r requirements.txt
```

| Package | Role |
|--------|------|
| **google-generativeai** | Gemini API (`generate_content`), with a stop sequence so the model does not write its own `Observation`. |
| **ddgs** | DuckDuckGo search (`DDGS`) for the **web_search** tool. |

Upgrading on Colab if the client misbehaves:

```text
pip install -q -U google-generativeai google-api-core ddgs
```

---

## Tools (in `src/minimal_react_agent.py`)

| Tool | Role |
|------|------|
| **web_search** | DuckDuckGo text results (title, snippet, URL). |
| **calculator** | Safe math via `ast` (not `eval`): `+ - * / % **` on numeric expressions. |

---

## How to run

### Local

From the **repository root** (the folder that contains `src/`):

```bash
pip install -r requirements.txt
```

Set **`GEMINI_API_KEY`** (PowerShell: `$env:GEMINI_API_KEY = "your-key"`, bash: `export GEMINI_API_KEY=your-key`).

Optional: **`GEMINI_MODEL`** (default in code is `gemini-2.5-flash`).

**Option A — run the file**

```bash
python src/minimal_react_agent.py
```

**Option B — import**

```bash
python -c "from src.minimal_react_agent import react; react('What is 17 * 23? Use the calculator.')"
```

### Google Colab

1. Enable internet on the runtime.
2. Install: `!pip install -q -U google-generativeai ddgs` *(or `!pip install -r requirements.txt` if you uploaded the whole repo)*.
3. Add Colab **Secret** **`GEMINI_API_KEY`** and allow this notebook to use it (or set `os.environ["GEMINI_API_KEY"]`).
4. Upload `src/minimal_react_agent.py` to Colab **or** paste its full contents into a code cell and run it.
5. In a new cell, call **`react("your question")`**.  
   The `if __name__ == "__main__":` block does **not** run when code lives in a notebook cell, so you must call **`react(...)`** yourself.

---

## Observations (what to expect)

- **Steps**: Each loop prints `--- Step N ---` and the model’s text; after a tool runs you see **`[System] Observation:`** (long text may be clipped when printed).
- **RESULT / SUMMARY**: When the model emits **Final Answer:**, the script prints a **RESULT** block and a short **SUMMARY** of earlier steps and observations.
- **Model id**: Default **`gemini-2.5-flash`**. Older names can **404**; override with **`GEMINI_MODEL`** if your project uses another id.
- **Network blips** (e.g. Colab): **`ask_model`** retries transient failures and uses a longer **timeout**.
- **Keys**: Keep **`GEMINI_API_KEY_INLINE`** empty in shared repos; use Secrets or env vars instead.

---

## API key (quick reference)

Use one of: Colab **Secret** `GEMINI_API_KEY`, **`os.environ["GEMINI_API_KEY"]`**, **`GEMINI_API_KEY_INLINE`** in the script (local only, do not commit), or the interactive paste path when **`setup()`** runs on Colab.
