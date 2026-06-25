# Dockerization Strategy
- Base Image: python:3.11-slim
- Working Dir: /app
- Entrypoint: python tools/heartbeat.py
- Monitoring: asoctl.py monitor
- Ports: 8080 (API), 9090 (Metrics)
