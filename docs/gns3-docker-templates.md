# GNS3 Docker Template Notes

Build the images on the GNS3 host:

```bash
docker compose build
```

Then create three GNS3 Docker templates.

## PLC Template

- Template type: Docker container
- Name: `OT PLC Ladder - Modbus TCP`
- Image: `cithit/ot-plc:latest`
- Adapters: `1`
- Start command: leave default
- Console: optional shell console
- Exposed service: TCP `5020`
- Addressing: static IP prompt on `eth0`

Environment variables:

```text
PLC_PROFILE=compactlogix_like
MODBUS_PORT=5020
PLC_CONFIG=/config/plc.yaml
IO_PANEL_URL=http://<remote-io-static-address>:8080/api/io
STATIC_INTERFACE=eth0
```

Mount the local `config` directory into the container as `/config:ro`.

## Remote I/O Panel Template

- Template type: Docker container
- Name: `OT Remote I/O Panel`
- Image: `cithit/ot-rio:latest`
- Adapters: `1`
- Start command: leave default
- Console: optional shell console
- Exposed service: TCP `8080`
- Addressing: static IP prompt on `eth0`

Environment variables:

```text
IO_CONFIG=/config/io-panel.yaml
STATIC_INTERFACE=eth0
```

Mount the local `config` directory into the container as `/config`.

## HMI Template

- Template type: Docker container
- Name: `OT HMI - Modbus TCP`
- Image: `cithit/ot-hmi:latest`
- Adapters: `1`
- Start command: leave default
- Console: optional shell console
- Exposed service: TCP `8090`
- Addressing: static IP prompt on `eth0`

Environment variables:

```text
HMI_CONFIG=/config/hmi.yaml
HMI_IP=static
PLC_HOST=<plc-static-address>
PLC_PORT=5020
PLC_UNIT_ID=1
STATIC_INTERFACE=eth0
```

Mount the local `config` directory into the container as `/config`.

## Ignition Connection

Create a Modbus TCP device in Ignition that points to the PLC node:

```text
hostname: <plc-static-address>
port: 5020
unit id: 1
```

Use the PLC static address. Use the register map in the project `README.md`.

## Instructor Panel

Open the remote I/O panel in a browser:

```text
http://<remote-io-static-address>:8080
```

The top section provides instructor scenarios that modify simulated field inputs. Use it to trigger conditions such as high ambient temperature, high water pressure, an open door interlock, or an e-stop trip while students watch PLC and SCADA behavior.

## HMI Panel

Open the HMI in a browser:

```text
http://<hmi-static-address>:8090
```

Use the HMI type drop-down to switch between manufacturing, water, wastewater, and electrical grid process screens. The settings area also lets students or instructors change the HMI station IP shown on screen and the PLC IP/port used for Modbus TCP.

## Static IP Console Prompt

Each appliance asks for a static address from the container console before the application starts. Use an interactive Docker console in GNS3.

The prompt asks for:

- IP address with CIDR, such as `192.168.10.20/24`
- default gateway, optional
- DNS server, optional

If the container is started non-interactively, it logs a message, keeps the current address, and starts the application so automated builds and Compose runs do not hang. If static assignment fails, the container logs a warning and still starts the application.

For GNS3 templates, allow `NET_ADMIN` or run the appliance as privileged so Linux can apply the entered IP address.

You can also set a static address without prompting:

```text
STATIC_IP_CIDR=192.168.10.20/24
STATIC_GATEWAY=192.168.10.1
STATIC_DNS=192.168.10.1
STATIC_INTERFACE=eth0
```

## Realistic Traffic Guidance

For training, the simulator gives repeatable Modbus TCP traffic with a ladder scan loop and realistic register behavior. For traffic that closely resembles a specific PLC model, capture a baseline PCAP from that model and tune:

- scan cycle and jitter
- Modbus function codes that are accepted or rejected
- invalid address exception behavior
- idle socket timeout
- register holes
- initial values and warm-start behavior
