# GNS3 Docker Template Notes

Build the images on the GNS3 host:

```bash
docker compose build
```

Then create two GNS3 Docker templates.

## PLC Template

- Template type: Docker container
- Name: `OT PLC Ladder - Modbus TCP`
- Image: `gns3-ot-plc-ladder:latest`
- Adapters: `1`
- Start command: leave default
- Console: optional shell console
- Exposed service: TCP `5020`
- Suggested IP in topology: `10.10.10.20/24`

Environment variables:

```text
PLC_PROFILE=compactlogix_like
MODBUS_PORT=5020
PLC_CONFIG=/config/plc.yaml
IO_PANEL_URL=http://10.10.10.30:8080/api/io
```

Mount the local `config` directory into the container as `/config:ro`.

## Remote I/O Panel Template

- Template type: Docker container
- Name: `OT Remote I/O Panel`
- Image: `gns3-ot-remote-io-panel:latest`
- Adapters: `1`
- Start command: leave default
- Console: optional shell console
- Exposed service: TCP `8080`
- Suggested IP in topology: `10.10.10.30/24`

Environment variables:

```text
IO_CONFIG=/config/io-panel.yaml
```

Mount the local `config` directory into the container as `/config`.

## Ignition Connection

Create a Modbus TCP device in Ignition that points to the PLC node:

```text
hostname: 10.10.10.20
port: 5020
unit id: 1
```

Use the register map in the project `README.md`.

## Realistic Traffic Guidance

For training, the simulator gives repeatable Modbus TCP traffic with a ladder scan loop and realistic register behavior. For traffic that closely resembles a specific PLC model, capture a baseline PCAP from that model and tune:

- scan cycle and jitter
- Modbus function codes that are accepted or rejected
- invalid address exception behavior
- idle socket timeout
- register holes
- initial values and warm-start behavior
