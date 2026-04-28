# GNS3 Docker Template Notes

Build the images on the GNS3 host:

```bash
docker compose build
```

Then create three GNS3 Docker templates.

## PLC Template

- Template type: Docker container
- Name: `OT PLC Ladder - Modbus TCP`
- Image: `cithit/plc:latest`
- Adapters: `1`
- Start command: leave default
- Console: optional shell console
- Exposed service: TCP `5020`
- Addressing: DHCP on `eth0`

Environment variables:

```text
PLC_PROFILE=compactlogix_like
MODBUS_PORT=5020
PLC_CONFIG=/config/plc.yaml
IO_PANEL_URL=http://<remote-io-dhcp-address>:8080/api/io
DHCP_ENABLED=true
DHCP_INTERFACE=eth0
DHCP_FORCE=true
DHCP_TIMEOUT=15
STATIC_IP_FALLBACK_PROMPT=true
```

Mount the local `config` directory into the container as `/config:ro`.

## Remote I/O Panel Template

- Template type: Docker container
- Name: `OT Remote I/O Panel`
- Image: `cithit/rio:latest`
- Adapters: `1`
- Start command: leave default
- Console: optional shell console
- Exposed service: TCP `8080`
- Addressing: DHCP on `eth0`

Environment variables:

```text
IO_CONFIG=/config/io-panel.yaml
DHCP_ENABLED=true
DHCP_INTERFACE=eth0
DHCP_FORCE=true
DHCP_TIMEOUT=15
STATIC_IP_FALLBACK_PROMPT=true
```

Mount the local `config` directory into the container as `/config`.

## HMI Template

- Template type: Docker container
- Name: `OT HMI - Modbus TCP`
- Image: `cithit/hmi:latest`
- Adapters: `1`
- Start command: leave default
- Console: optional shell console
- Exposed service: TCP `8090`
- Addressing: DHCP on `eth0`

Environment variables:

```text
HMI_CONFIG=/config/hmi.yaml
HMI_IP=dhcp
PLC_HOST=<plc-dhcp-address>
PLC_PORT=5020
PLC_UNIT_ID=1
DHCP_ENABLED=true
DHCP_INTERFACE=eth0
DHCP_FORCE=true
DHCP_TIMEOUT=15
STATIC_IP_FALLBACK_PROMPT=true
```

Mount the local `config` directory into the container as `/config`.

## Ignition Connection

Create a Modbus TCP device in Ignition that points to the PLC node:

```text
hostname: <plc-dhcp-address>
port: 5020
unit id: 1
```

Use the PLC DHCP lease address. Use the register map in the project `README.md`.

## Instructor Panel

Open the remote I/O panel in a browser:

```text
http://<remote-io-dhcp-address>:8080
```

The top section provides instructor scenarios that modify simulated field inputs. Use it to trigger conditions such as high ambient temperature, high water pressure, an open door interlock, or an e-stop trip while students watch PLC and SCADA behavior.

## HMI Panel

Open the HMI in a browser:

```text
http://<hmi-dhcp-address>:8090
```

Use the HMI type drop-down to switch between manufacturing, water, wastewater, and electrical grid process screens. The settings area also lets students or instructors change the HMI station IP shown on screen and the PLC IP/port used for Modbus TCP.

## DHCP Notes

Each image includes `dhclient` and can request an address on startup. Your GNS3 topology must include a DHCP server or router service on the same L2 segment. If your GNS3 Docker template supports Linux capabilities, allow `NET_ADMIN` and `NET_RAW` so the DHCP client can configure the interface.

For GNS3 templates, set `DHCP_FORCE=true` to request a lease even if the runtime pre-populates an address. For local Docker Compose, leave `DHCP_FORCE` unset so the containers keep their Docker-managed addresses and start immediately.

If DHCP fails and the console is interactive, `STATIC_IP_FALLBACK_PROMPT=true` offers the static IP prompt automatically.

## Static IP Console Prompt

If you want students to assign a static address from the container console instead of using DHCP, set these environment variables in the GNS3 Docker template:

```text
STATIC_IP_PROMPT=true
DHCP_ENABLED=false
DHCP_INTERFACE=eth0
```

When the container starts, it prompts for:

- IP address with CIDR, such as `192.168.10.20/24`
- default gateway, optional
- DNS server, optional

The prompt only appears when the container has an interactive stdin/TTY. In GNS3, use an interactive Docker console for the appliance. If the container is started non-interactively, it logs a message and skips the prompt so automated builds and Compose runs do not hang.

You can also set a static address without prompting:

```text
STATIC_IP_CIDR=192.168.10.20/24
STATIC_GATEWAY=192.168.10.1
STATIC_DNS=192.168.10.1
DHCP_ENABLED=false
```

## Realistic Traffic Guidance

For training, the simulator gives repeatable Modbus TCP traffic with a ladder scan loop and realistic register behavior. For traffic that closely resembles a specific PLC model, capture a baseline PCAP from that model and tune:

- scan cycle and jitter
- Modbus function codes that are accepted or rejected
- invalid address exception behavior
- idle socket timeout
- register holes
- initial values and warm-start behavior
