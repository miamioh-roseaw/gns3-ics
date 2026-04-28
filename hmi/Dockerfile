FROM python:3.12-slim

WORKDIR /app
RUN apt-get update \
  && apt-get install -y --no-install-recommends isc-dhcp-client iproute2 \
  && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates ./templates
COPY static ./static
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8090/tcp
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "app.py"]
