"""
ai_report.py
------------
Rewrite of GEN_AI.py's reporting logic.
Takes the metrics dict from analysis.py and asks an LLM (via Groq)
to produce a BUY / HOLD / SELL report, same structure as your
original 5-part analysis prompt.

The API key is read from the environment (.env file) -- it is
NEVER hardcoded here.
"""

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # reads GROQ_API_KEY from a local .env file

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"  # actual model used (via Groq, not GPT-4o)

# Explicit decision rules so the model has real thresholds to weigh the
# stock against, instead of judging each stock in isolation (which biases
# towards BUY, since isolated positive-sounding stats read as good news).
SYSTEM_PROMPT = """
You are an expert quantitative financial analyst. You are skeptical by
default — most stocks at any given time deserve a HOLD, not a BUY.
Only recommend BUY or SELL when the metrics clearly justify it.

Use these concrete thresholds as your starting point (adjust slightly
with judgement, but stay close to them):

SELL if any of:
- Sharpe ratio is below 0.3, OR
- Max drawdown is worse than -30%, OR
- Price (MA-50) is below MA-200 (death cross) AND annual return is negative

BUY if any of:
- Sharpe ratio is above 1.0 AND max drawdown is better (less negative) than -25%, OR
- MA-50 is meaningfully above MA-200 (golden cross) AND Sharpe ratio is above 0.6

HOLD for everything in between, including mixed signals (e.g. good
return but high drawdown, or good Sharpe but a death cross).

Respond with ONLY valid JSON, no markdown fences, no extra text:
{
  "signal": "BUY" | "HOLD" | "SELL",
  "performance_summary": "...",
  "risk_assessment": "...",
  "technical_signal": "...",
  "portfolio_role": "...",
  "recommendation_rationale": "..."
}

Each field 2-3 sentences, data-driven, referencing the actual numbers given.
"""


def _build_user_prompt(m: dict) -> str:
    return f"""
Analyse this stock:
Ticker        : {m['ticker']} ({m['name']})
Latest Price  : ₹{m['latest_price']}
Annual Return : {m['annual_return_pct']}%
Annual Vol    : {m['annual_vol_pct']}%
Sharpe Ratio  : {m['sharpe_ratio']}
Sortino Ratio : {m['sortino_ratio']}
Max Drawdown  : {m['max_drawdown'] * 100:.2f}%
VaR 95%       : {m['var_95'] * 100:.2f}%
Beta          : {m['beta']}
MA-50         : {m['ma_50']}
MA-200        : {m['ma_200']}
30d Vol       : {m['vol_30d']}
Data points   : {m['data_points']} (last 3 years)
"""


def _strip_code_fences(text: str) -> str:
    """Some models wrap JSON in ```json ... ``` even when told not to."""
    text = text.strip()
    text = re.sub(r"^```(json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def generate_report(metrics: dict) -> dict:
    """
    Calls the LLM and returns:
    {"signal": "BUY"/"HOLD"/"SELL", "report": "<formatted text>", "model": "..."}
    """
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY not found. Create a .env file in the backend folder "
            "with a line: GROQ_API_KEY=your_key_here"
        )

    client = Groq(api_key=GROQ_API_KEY)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.2,  # lower temperature: more consistent, less prone to drifting positive
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(metrics)},
        ],
    )

    raw = response.choices[0].message.content
    cleaned = _strip_code_fences(raw)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # Model didn't return clean JSON -- surface the real text rather
        # than silently guessing a signal from a substring match.
        return {
            "signal": "HOLD",
            "report": (
                "Could not parse a structured response from the model. "
                "Raw output below:\n\n" + raw
            ),
            "model": MODEL_NAME,
        }

    signal = str(parsed.get("signal", "HOLD")).strip().upper()
    if signal not in ("BUY", "HOLD", "SELL"):
        signal = "HOLD"

    body = (
        f"1. Performance Summary\n{parsed.get('performance_summary', '')}\n\n"
        f"2. Risk Assessment\n{parsed.get('risk_assessment', '')}\n\n"
        f"3. Technical Signal\n{parsed.get('technical_signal', '')}\n\n"
        f"4. Portfolio Role\n{parsed.get('portfolio_role', '')}\n\n"
        f"5. Recommendation: {signal}\n{parsed.get('recommendation_rationale', '')}"
    )

    return {"signal": signal, "report": body, "model": MODEL_NAME}
