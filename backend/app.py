"""
app.py
------
Local Flask server. Serves the frontend and exposes one API endpoint:

  GET /api/analyze?ticker=TCS.NS

which runs analysis.py (fetch + metrics) then ai_report.py (LLM call)
and returns JSON for the frontend to render.

RUN LOCALLY:
    1. pip install -r requirements.txt
    2. Create backend/.env with: GROQ_API_KEY=your_key_here
    3. python app.py
    4. Open http://127.0.0.1:5000 in your browser
"""

from flask import Flask, jsonify, request, send_from_directory
import os
import traceback

from analysis import analyze_ticker, TICKERS, TICKER_NAMES
from ai_report import generate_report

app = Flask(__name__, static_folder="../frontend", static_url_path="")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/tickers")
def list_tickers():
    """Returns the 5 supported stocks for the dropdown."""
    return jsonify([
        {"ticker": t, "name": TICKER_NAMES[t]} for t in TICKERS
    ])


@app.route("/api/analyze")
def analyze():
    ticker = request.args.get("ticker", "").strip()
    if ticker not in TICKERS:
        return jsonify({"error": f"Invalid ticker. Must be one of {TICKERS}"}), 400

    try:
        metrics = analyze_ticker(ticker)
        ai = generate_report(metrics)
        return jsonify({
            "metrics": metrics,
            "signal": ai["signal"],
            "report": ai["report"],
            "model": ai["model"],
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Stock Advisor running at: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
