import sys
import time
import json
import socket
from pathlib import Path
from datetime import datetime

import requests
from flask import Flask
from flask_socketio import SocketIO

BRIDGE_PORT = 5002
FNG_URL = "https://api.alternate.me/fng/"
FNG_HOST = "api.alternate.me"
CACHE_FILE = Path("fng_cache.json")
ERROR_LOG_INTERVAL_SECONDS = 300

app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    ping_interval=20,
    ping_timeout=60
)

_last_fng_error_log_ts = 0.0

intelligence_data = {
    "market_status": "ANALYZING",
    "data_health": "PARTIAL_DATA",
    "global_metrics": {
        "btc_price": 0,
        "eth_price": 0,
        "gold_price": 0,
        "btc_change_24h": 0,
        "fear_greed": 50,
        "sentiment": "Neutral"
    },
    "wallets": [
        {"id": "W1", "name": "ANCHOR", "role": "Safe/Quality", "status": "HOLDING"},
        {"id": "W2", "name": "HYBRID", "role": "Spot/Futures", "status": "MONITORING"},
        {"id": "W3", "name": "HUNTER", "role": "Quick Gains", "status": "IDLE"}
    ],
    "last_update": ""
}

def log_rate_limited(message: str):
    global _last_fng_error_log_ts
    now = time.time()
    if now - _last_fng_error_log_ts >= ERROR_LOG_INTERVAL_SECONDS:
        print(message)
        _last_fng_error_log_ts = now

def can_resolve(hostname: str) -> bool:
    try:
        socket.gethostbyname(hostname)
        return True
    except Exception:
        return False

def load_fng_cache():
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_rate_limited(f"[FNG][WARN] Failed to load cache: {e}")
        return None

def save_fng_cache(value: int, classification: str):
    payload = {
        "fear_greed": value,
        "sentiment": classification,
        "cached_at": datetime.now().isoformat()
    }
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_rate_limited(f"[FNG][WARN] Failed to save cache: {e}")

def apply_fng_from_cache():
    cached = load_fng_cache()
    if not cached:
        intelligence_data["global_metrics"]["fear_greed"] = 50
        intelligence_data["global_metrics"]["sentiment"] = "Unavailable"
        return False

    intelligence_data["global_metrics"]["fear_greed"] = int(cached.get("fear_greed", 50))
    intelligence_data["global_metrics"]["sentiment"] = cached.get("sentiment", "Unavailable (cached)")
    return True

def fetch_fng_optional():
    if not can_resolve(FNG_HOST):
        used_cache = apply_fng_from_cache()
        intelligence_data["data_health"] = "DEGRADED"
        if used_cache:
            log_rate_limited("[FNG][DEGRADED] DNS resolution failed for api.alternate.me. Using cached Fear & Greed data.")
        else:
            log_rate_limited("[FNG][DEGRADED] DNS resolution failed for api.alternate.me. No cache available; using neutral defaults.")
        return False

    try:
        fg_r = requests.get(FNG_URL, timeout=10)
        fg_r.raise_for_status()
        fg_json = fg_r.json()
        fg_data = fg_json["data"][0]

        value = int(fg_data["value"])
        classification = fg_data["value_classification"]

        intelligence_data["global_metrics"]["fear_greed"] = value
        intelligence_data["global_metrics"]["sentiment"] = classification
        save_fng_cache(value, classification)
        return True
    except Exception as e:
        used_cache = apply_fng_from_cache()
        intelligence_data["data_health"] = "DEGRADED"
        if used_cache:
            log_rate_limited(f"[FNG][DEGRADED] Fetch failed; using cache. Error: {e}")
        else:
            log_rate_limited(f"[FNG][DEGRADED] Fetch failed; no cache available, using defaults. Error: {e}")
        return False

def get_global_data():
    coingecko_ok = False
    fng_ok = False

    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,pax-gold&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        intelligence_data["global_metrics"]["btc_price"] = data["bitcoin"]["usd"]
        intelligence_data["global_metrics"]["eth_price"] = data["ethereum"]["usd"]
        intelligence_data["global_metrics"]["gold_price"] = data["pax-gold"]["usd"]
        intelligence_data["global_metrics"]["btc_change_24h"] = data["bitcoin"]["usd_24h_change"]
        coingecko_ok = True
    except Exception as e:
        print(f"[MARKET][WARN] CoinGecko fetch failed: {e}")

    fng_ok = fetch_fng_optional()

    if coingecko_ok and fng_ok:
        intelligence_data["data_health"] = "HEALTHY"
    elif coingecko_ok and not fng_ok:
        intelligence_data["data_health"] = "DEGRADED"
    elif not coingecko_ok and fng_ok:
        intelligence_data["data_health"] = "DEGRADED"
    else:
        intelligence_data["data_health"] = "PARTIAL_DATA"

    change = intelligence_data["global_metrics"]["btc_change_24h"]
    if change < -5:
        intelligence_data["market_status"] = "BLOOD_BATH (BUY)"
    elif change > 3:
        intelligence_data["market_status"] = "BULLISH"
    else:
        intelligence_data["market_status"] = "STABLE"

def update_loop():
    while True:
        get_global_data()
        intelligence_data["last_update"] = datetime.now().strftime("%H:%M:%S")
        socketio.emit("arzplus_status_update", intelligence_data)
        m = intelligence_data["global_metrics"]
        print(
            f"[{intelligence_data['last_update']}] "
            f"BTC: {m['btc_price']} | Gold: {m['gold_price']} | "
            f"FNG: {m['fear_greed']} ({m['sentiment']}) | "
            f"Status: {intelligence_data['market_status']} | "
            f"Health: {intelligence_data['data_health']}"
        )
        time.sleep(30)

if __name__ == "__main__":
    import threading
    threading.Thread(target=update_loop, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=BRIDGE_PORT, debug=False, allow_unsafe_werkzeug=True)
