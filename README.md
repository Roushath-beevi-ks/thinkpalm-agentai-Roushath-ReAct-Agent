# Roushath- Frontend Dev-ReAct Agent - Minimal Python ReAct Agent

A lightweight, purely Python-based AI agent built using the **ReAct (Reasoning and Acting)** framework. This project demonstrates how Large Language Models (LLMs) can be prompted to logically reason step-by-step and dynamically interact with external tools to solve multi-part problems.

Built using the **Google Gemini API** (`google-generativeai`).

## 🌟 Overview

The agent is given a complex query and access to specific restricted tools. Instead of hallucinating an answer, it undergoes a thought cycle:
1. **Thought:** Determines what missing information it needs.
2. **Action:** Selects an appropriate tool.
3. **Action Input:** Passes parameters to the tool.
4. **Observation:** Receives real data back from the tool system.
5. *Repeats until it has enough information to formulate a Final Answer.*

## 🛠️ Tools Included
For this demonstration, the agent has access to two mock tools:
- `get_stock_price(ticker)`: Retrieves the live price of a stock (e.g., AAPL, TSLA).
- `calculator(expression)`: Safely evaluates standard mathematical expressions.

## 🚀 Quick Start (Google Colab / Local run)

1. Clone this repository or copy the script into a Google Colab notebook environment.
2. Install the necessary Gemini SDK:
   ```bash
   pip install -q google-generativeai



