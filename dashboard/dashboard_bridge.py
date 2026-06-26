import sys
import time
import requests
from datetime import datetime
from flask import Flask
from flask_socketio import SocketIO

BRIDGE_PORT = 5002
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_interval=20, ping_timeout=60)

intelligence_data = {
    "market_status": "ANALYZING",
    "global_metrics": {
        "btc_price": 0, "eth_price": 0, "gold_price": 0,
        "btc_change_24h": 0, "fear_greed": 50, "sentiment": "Neutral"
    },
    "wallets": [
        {"id": "W1", "name": "ANCHOR", "role": "Safe/Quality", "status": "HOLDING"},
        {"id": "W2", "name": "HYBRID", "role": "Spot/Futures", "status": "MONITORING"},
        {"id": "W3", "name": "HUNTER", "role": "Quick Gains", "status": "IDLE"}
    ],
    "last_update": ""
}

def get_global_data():
    try:
        # متد جایگزین برای دور زدن محدودیت بایننس (استفاده از API عمومی بدون تحریم)
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,pax-gold&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        intelligence_data["global_metrics"]["btc_price"] = data['bitcoin']['usd']
        intelligence_data["global_metrics"]["eth_price"] = data['ethereum']['usd']
        intelligence_data["global_metrics"]["gold_price"] = data['pax-gold']['usd']
        intelligence_data["global_metrics"]["btc_change_24h"] = data['bitcoin']['usd_24h_change']
        
        # دریافت شاخص ترس و طمع
        fg_r = requests.get("https://api.alternate.me/fng/", timeout=10)
        fg_data = fg_r.json()['data'][0]
        intelligence_data["global_metrics"]["fear_greed"] = int(fg_data['value'])
        intelligence_data["global_metrics"]["sentiment"] = fg_data['value_classification']
        
        # تحلیل وضعیت بازار
        change = intelligence_data["global_metrics"]["btc_change_24h"]
        if change < -5: intelligence_data["market_status"] = "BLOOD_BATH (BUY)"
        elif change > 3: intelligence_data["market_status"] = "BULLISH"
        else: intelligence_data["market_status"] = "STABLE"

    except Exception as e:
        print(f"Connection Alert: {e}")
        # اگر کوین‌گکو هم بسته بود، از یک منبع دیگر استفاده می‌کنیم (تلاش مجدد در چرخه بعد)

def update_loop():
    while True:
        get_global_data()
        intelligence_data["last_update"] = datetime.now().strftime("%H:%M:%S")
        socketio.emit('arzplus_status_update', intelligence_data)
        # نمایش در کنسول برای اطمینان شما
        m = intelligence_data["global_metrics"]
        print(f"[{intelligence_data['last_update']}] BTC: {m['btc_price']} | Gold: {m['gold_price']} | Status: {intelligence_data['market_status']}")
        time.sleep(30)

if __name__ == '__main__':
    import threading
    threading.Thread(target=update_loop, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=BRIDGE_PORT, debug=False, allow_unsafe_werkzeug=True)
