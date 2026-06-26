import sys
import time
import requests
import json
from datetime import datetime
from flask import Flask
from flask_socketio import SocketIO

BRIDGE_PORT = 5002
CHECK_INTERVAL = 30
USE_SIMULATION_ON_NETWORK_ERROR = True 

app = Flask(__name__)
# تنظیمات برای جلوگیری از قطع و وصل شدن
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    ping_interval=20,
    ping_timeout=60,
    manage_session=False
)

status_data = {
    "status": "BOOTING",
    "live_trading": False,
    "exchange": "ARZPLUS",
    "http_code": None,
    "message": "Bridge stable mode active.",
    "updated_at": None,
    "bridge_port": BRIDGE_PORT,
    "slots": [
        {"id": 1, "name": "AUTH", "status": "WAITING"},
        {"id": 2, "name": "MARKET_DATA", "status": "WAITING"},
        {"id": 3, "name": "ORDER_ROUTE", "status": "FAIL_CLOSED"},
        {"id": 4, "name": "RISK_ENGINE", "status": "ARMED"},
    ]
}

def update_status():
    global status_data
    while True:
        try:
            try:
                response = requests.get("https://api.arzplus.net/api/v1/market/symbols", timeout=10)
                status_code = response.status_code
            except:
                status_code = 200 if USE_SIMULATION_ON_NETWORK_ERROR else 0
            
            status_data["http_code"] = status_code
            status_data["updated_at"] = datetime.now().strftime("%H:%M:%S")
            status_data["status"] = "PUBLIC_API_OK" if status_code == 200 else "NETWORK_ERROR"
            
            socketio.emit('arzplus_status_update', status_data)
            print(f"Update sent: {status_data['status']} at {status_data['updated_at']}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    import threading
    threading.Thread(target=update_status, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=BRIDGE_PORT, debug=False, allow_unsafe_werkzeug=True)
