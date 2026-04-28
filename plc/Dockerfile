FROM python:3.12-slim

WORKDIR /app
RUN apt-get update \
  && apt-get install -y --no-install-recommends iproute2 \
  && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY plc.py .
COPY config ./config
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

EXPOSE 5020/tcp
ENV SERVICE_NAME="Modbus TCP PLC" SERVICE_PORT="5020"
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "plc.py"]
