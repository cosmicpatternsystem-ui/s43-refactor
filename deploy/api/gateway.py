import json
import os
from flask import Flask, jsonify

app = Flask(__name__)
LOG_PATH = "runtime/audit/audit_log.json"

@app.route('/v1/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ACTIVE",
        "version": "1.1.0-COMMERCIAL",
        "engine": "PRIME-X1",
        "security": "LOCKED"
    })

@app.route('/v1/audit/latest', methods=['GET'])
def get_latest_audit():
    if not os.path.exists(LOG_PATH):
        return jsonify({"error": "No audit logs found"}), 404
    
    with open(LOG_PATH, 'r') as f:
        logs = json.load(f)
        return jsonify(logs[-1] if logs else {})

if __name__ == '__main__':
    print("ASO-X Commercial API Gateway starting on port 8080...")
    app.run(port=8080)
