# Desk Five — AI Equity Notes

A local web app that runs your AI stock advisor for 5 NSE-listed stocks

Pick a stock → it pulls the last 3 years of price data live from Yahoo
Finance → computes risk/return metrics (Sharpe, Sortino, Max Drawdown,
VaR, Beta, moving averages) → sends them to an LLM (via Groq) → shows
you a BUY / HOLD / SELL note.

---

## 1. Get a Groq API key (do this first)

⚠️ **Important:** the key you pasted into our chat earlier is no longer
private — please go generate a brand-new one.

1. Go to https://console.groq.com/keys
2. Revoke/delete the old key if it's still listed
3. Create a new key and copy it

You will paste this key into a file on **your own computer only** —
never share it in a chat again.

## 2. Install Python requirements

Open a terminal in the `backend` folder and run:

```bash
pip install -r requirements.txt
```

Requires Python 3.10+.

## 3. Add your API key

In the `backend` folder, copy `.env.example` to a new file named `.env`:

```bash
cp .env.example .env
```

Open `.env` in a text editor and paste your key:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

Save the file. (`.env` is your local secret file — don't upload it
anywhere or share it.)

## 4. Run the app

From the `backend` folder:

```bash
python app.py
```

You'll see:

```
Stock Advisor running at: http://127.0.0.1:5000
```

Open that link in your browser.

## 5. Use it

1. Click one of the 5 stock tiles
2. Click **Run analysis**
3. Wait a few seconds — it's downloading 3 years of daily prices and
   calling the AI model
4. You'll get a BUY/HOLD/SELL badge, the key metrics, and the full
   written note

---

## What changed from your original scripts

| Original | This version | Why |
|---|---|---|
| PySpark + Delta Lake (`Financial_db.py`) | Plain pandas (`analysis.py`) | Spark/Delta need Java + cluster setup; pandas does identical math and runs anywhere |
| Hardcoded API key in code | Read from local `.env` file | The hardcoded key was exposed once shared — never put real keys in code |
| Saved to Delta tables, ran once as a batch script | Runs on-demand per ticker, via a button in browser | You wanted visitors to trigger it themselves, not re-run a whole batch pipeline |
| Comments said "GPT-4o" | Labeled as Llama 4 Scout (via Groq) | That's the model actually being called — the original comment was inaccurate |

The 5-part analysis structure (Performance / Risk / Technical Signal /
Portfolio Role / Recommendation) and all the underlying formulas
(Sharpe, Sortino, Max Drawdown, VaR 95%, Beta vs NIFTY 50, MA-50,
MA-200) are unchanged from your original logic.

## Folder structure

```
stock-advisor/
├── backend/
│   ├── app.py            ← Flask server, run this
│   ├── analysis.py        ← price fetch + metrics (pandas)
│   ├── ai_report.py        ← LLM call (Groq)
│   ├── requirements.txt
│   └── .env.example       ← copy to .env and add your key
└── frontend/
    └── index.html          ← the web page
```

## Notes & limits

- This is **not investment advice** — it's an AI-generated note based
  on historical statistics. Says so on the page too.
- Each click makes a fresh network call to Yahoo Finance and one LLM
  call to Groq — there's no caching yet. If you click the same stock
  repeatedly you'll regenerate (and re-pay token cost for) the report
  each time.
- Right now this only runs on your computer (`127.0.0.1` = your
  machine only, nobody else can reach it). When you're ready to put it
  on the internet, the usual next step is a small hosting service
  (e.g. Render, Railway, or PythonAnywhere) — happy to help with that
  when you get there.
