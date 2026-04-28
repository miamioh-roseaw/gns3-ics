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

EXPOSE 5020/tcp 8081/tcp
ENV SERVICE_NAME="PLC Settings Panel" SERVICE_PORT="8081"
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "plc.py"]
