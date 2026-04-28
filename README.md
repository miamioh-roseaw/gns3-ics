# GNS3 OT/ICS Docker Lab Starter

This starter kit creates three Docker-backed OT devices for GNS3:

- `ot-plc-ladder`: a ladder-scan PLC simulator that exposes Modbus TCP for SCADA tools such as Ignition.
- `ot-remote-io-panel`: a browser-managed remote I/O panel with selectable field devices.
- `ot-hmi`: an operator HMI that connects to the PLC over Modbus TCP.

Published Docker Hub images:

```text
cithit/ot-plc-1:latest
cithit/ot-rio-1:latest
cithit/ot-hmi-1:latest
```

The PLC behavior is intentionally realistic at the Modbus/register/scan level, but it cannot be an exact network fingerprint of a vendor PLC. Exact fingerprinting would require the real firmware/protocol stack, vendor TCP quirks, and timing behavior.

## Run locally

```bash
docker compose up --build
```

Open the remote I/O panel:

```text
http://localhost:8080
```

Open the HMI:

```text
http://localhost:8090
```

Connect Ignition or another Modbus TCP client to:

```text
host: localhost
port: 5020
unit id: 1
```

## Default Modbus Map

Zero-based addresses are used internally.

| Signal | Modbus Area | Address | Ignition-style reference |
| --- | --- | ---: | --- |
| `pump_run_cmd` | Coil | 0 | `000001` |
| `alarm_active` | Coil | 1 | `000002` |
| `start_pb` | Discrete Input | 0 | `100001` |
| `estop_ok` | Discrete Input | 1 | `100002` |
| `door_closed` | Discrete Input | 2 | `100003` |
| `tank_high` | Discrete Input | 3 | `100004` |
| `pressure` | Input Register | 0 | `300001`, scaled x10 |
| `temperature` | Input Register | 1 | `300002`, scaled x10 |

## Device Types

The remote I/O panel supports these selectable device types:

- Pressure sensor
- Temperature sensor
- Limit switch
- Push button
- E-stop contact
- Door interlock
- Float switch
- Proximity sensor

## Instructor Scenarios

The remote I/O panel includes an instructor scenario area for injecting common process and safety issues during a lab. Presets currently include:

- Ambient heat rise
- Water pressure surge
- Blocked outlet
- Door interlock open
- E-stop pressed
- Pressure sensor failed low

These presets update the same simulated field points read by the PLC, so Ignition will see the effect through Modbus TCP just like a manual sensor change.

## HMI

The HMI container reads the PLC over Modbus TCP and shows an operator-facing process screen. It includes a selector for:

- Manufacturing
- Water
- Wastewater
- Electrical grid

Each type changes the screen title, process labels, and visual emphasis while using the same PLC data. The HMI settings area also lets you enter:

- this HMI station IP address
- PLC IP or hostname
- PLC TCP port
- Modbus unit ID

## GNS3 Use

Build each folder as a Docker appliance, or import this compose model into a host that GNS3 can reach. For GNS3 Docker templates, expose:

- PLC: TCP `5020`
- Remote I/O panel: TCP `8080`
- HMI: TCP `8090`

In a GNS3 topology, start each appliance with an interactive Docker console. The container asks for a static IP before starting the application:

```text
IP address with CIDR, example 192.168.10.20/24
Default gateway, optional
DNS server, optional
```

If the container is started non-interactively, it keeps the current interface address and starts normally. You can also set `STATIC_IP_CIDR`, `STATIC_GATEWAY`, and `STATIC_DNS` in the template to avoid prompting.

## Tuning the PLC Flavor

Edit `config/plc.yaml` to change:

- scan rate
- point names
- Modbus addresses
- simple ladder contacts/coils
- analog scaling

To mimic a particular PLC family more closely, capture traffic from the real PLC and tune:

- scan interval jitter
- exception responses
- unit ID behavior
- allowed function codes
- register gaps and invalid-address responses
- connection idle timeout behavior
