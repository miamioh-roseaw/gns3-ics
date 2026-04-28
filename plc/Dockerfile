FROM python:3.12-slim

WORKDIR /app
RUN apt-get update \
  && apt-get install -y --no-install-recommends isc-dhcp-client iproute2 \
  && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY plc.py .
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

EXPOSE 5020/tcp
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "plc.py"]
