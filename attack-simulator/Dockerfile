FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run the demo sequence targeting the gateway
ENTRYPOINT ["python", "attack_simulator.py"]
CMD ["--mode", "demo", "--url", "http://api-gateway:8080"]
