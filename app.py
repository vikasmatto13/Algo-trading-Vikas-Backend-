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
        r = requests.get(f"{UPSTOX_BASE}/user/profile", headers=headers(), timeout=5)
        if r.status_code == 200:
            d = r.json().get("data", {})
            return jsonify({"ok": True, "name": d.get("user_name",""), "email": d.get("email","")})
        return jsonify({"ok": False, "error": r.text}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/signals")
def signals():
    instruments = "NSE_INDEX|Nifty 50,NSE_INDEX|Nifty Bank,MCX_FO|GOLD25JUNFUT"
    try:
        r = requests.get(f"{UPSTOX_BASE}/market-quote/ltp",
            headers=headers(), params={"instrument_key": instruments}, timeout=5)
        data = r.json().get("data", {})
        result = [{"instrument": k.split("|")[-1], "ltp": v.get("last_price",0), "signal": "BUY"}
                  for k, v in data.items()]
        return jsonify({"ok": True, "signals": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/place-order", methods=["POST"])
def place_order():
    body = request.json
    paper = os.environ.get("PAPER_TRADE", "true").lower() == "true"
    if paper:
        return jsonify({"ok": True, "paper": True, "message": f"Paper trade: {body}"})
    try:
        r = requests.post(f"{UPSTOX_BASE}/order/place",
            headers={**headers(), "Content-Type": "application/json"},
            json={"quantity": body.get("qty",50), "product": "D", "validity": "DAY",
                  "price": 0, "instrument_token": body.get("token",""),
                  "order_type": "MARKET", "transaction_type": body.get("action","BUY"),
                  "disclosed_quantity": 0, "trigger_price": 0, "is_amo": False}, timeout=5)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/positions")
def positions():
    try:
        r = requests.get(f"{UPSTOX_BASE}/portfolio/short-term-positions",
            headers=headers(), timeout=5)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
