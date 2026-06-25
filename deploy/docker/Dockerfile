FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install flask
COPY . .
EXPOSE 8080
CMD ["python", "deploy/api/gateway.py"]
