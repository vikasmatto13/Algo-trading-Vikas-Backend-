from flask import Flask, jsonify, request
from flask_cors import CORS
import os, requests

app = Flask(__name__)
CORS(app)

UPSTOX_BASE = "https://api.upstox.com/v2"

def headers():
    token = os.environ.get("UPSTOX_TOKEN", "")
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

@app.route("/")
def home():
    return jsonify({"status": "AlgoEdge backend running"})

@app.route("/api/test")
def test():
    try:
        r = requests.get(f"{UPSTOX_BASE}/user/profile", headers=headers(), timeout=10)
        return jsonify({"ok": r.status_code == 200, "status": r.status_code, "body": r.text[:500]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/signals")
def signals():
    key = request.args.get("key", "NSE_INDEX|Nifty 50")
    try:
        r = requests.get(
            f"{UPSTOX_BASE}/market-quote/ltp",
            headers=headers(),
            params={"instrument_key": key},
            timeout=10
        )
        return jsonify({"ok": r.status_code == 200, "status": r.status_code, "body": r.text[:1000], "key": key})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "key": key}), 500

@app.route("/api/place-order", methods=["POST"])
def place_order():
    body = request.json or {}
    paper = os.environ.get("PAPER_TRADE", "true").lower() == "true"
    if paper:
        return jsonify({"ok": True, "paper": True, "message": f"Paper trade: {body}"})
    try:
        payload = {
            "quantity": body.get("qty", 50),
            "product": "D",
            "validity": "DAY",
            "price": 0,
            "instrument_token": body.get("token", ""),
            "order_type": "MARKET",
            "transaction_type": body.get("action", "BUY"),
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False
        }
        r = requests.post(
            f"{UPSTOX_BASE}/order/place",
            headers={**headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=10
        )
        return jsonify({"ok": r.status_code in (200, 201), "status": r.status_code, "body": r.text[:1000]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/positions")
def positions():
    try:
        r = requests.get(f"{UPSTOX_BASE}/portfolio/short-term-positions", headers=headers(), timeout=10)
        return jsonify({"ok": r.status_code == 200, "status": r.status_code, "body": r.text[:1000]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
