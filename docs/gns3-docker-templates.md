# GNS3 Docker Template Notes

Build the images on the GNS3 host:

```bash
docker compose build
```

Then create three GNS3 Docker templates.

## PLC Template

- Template type: Docker container
- Name: `OT PLC Ladder - Modbus TCP`
- Image: `cithit/gns3-ics:plc-latest`
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
- Image: `cithit/gns3-ics:remote-io-latest`
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

## HMI Template

- Template type: Docker container
- Name: `OT HMI - Modbus TCP`
- Image: `cithit/gns3-ics:hmi-latest`
- Adapters: `1`
- Start command: leave default
- Console: optional shell console
- Exposed service: TCP `8090`
- Suggested IP in topology: `10.10.10.40/24`

Environment variables:

```text
HMI_CONFIG=/config/hmi.yaml
HMI_IP=10.10.10.40
PLC_HOST=10.10.10.20
PLC_PORT=5020
PLC_UNIT_ID=1
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

## Instructor Panel

Open the remote I/O panel in a browser:

```text
http://10.10.10.30:8080
```

The top section provides instructor scenarios that modify simulated field inputs. Use it to trigger conditions such as high ambient temperature, high water pressure, an open door interlock, or an e-stop trip while students watch PLC and SCADA behavior.

## HMI Panel

Open the HMI in a browser:

```text
http://10.10.10.40:8090
```

Use the HMI type drop-down to switch between manufacturing, water, wastewater, and electrical grid process screens. The settings area also lets students or instructors change the HMI station IP shown on screen and the PLC IP/port used for Modbus TCP.

## Realistic Traffic Guidance

For training, the simulator gives repeatable Modbus TCP traffic with a ladder scan loop and realistic register behavior. For traffic that closely resembles a specific PLC model, capture a baseline PCAP from that model and tune:

- scan cycle and jitter
- Modbus function codes that are accepted or rejected
- invalid address exception behavior
- idle socket timeout
- register holes
- initial values and warm-start behavior
