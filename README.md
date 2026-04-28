# GNS3 OT/ICS Docker Lab Starter

This starter kit creates two Docker-backed OT devices for GNS3:

- `ot-plc-ladder`: a ladder-scan PLC simulator that exposes Modbus TCP for SCADA tools such as Ignition.
- `ot-remote-io-panel`: a browser-managed remote I/O panel with selectable field devices.

The PLC behavior is intentionally realistic at the Modbus/register/scan level, but it cannot be an exact network fingerprint of a vendor PLC. Exact fingerprinting would require the real firmware/protocol stack, vendor TCP quirks, and timing behavior.

## Run locally

```bash
docker compose up --build
```

Open the remote I/O panel:

```text
http://localhost:8080
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

## GNS3 Use

Build each folder as a Docker appliance, or import this compose model into a host that GNS3 can reach. For GNS3 Docker templates, expose:

- PLC: TCP `5020`
- Remote I/O panel: TCP `8080`

In a GNS3 topology, place Ignition on the same emulated segment or route to the PLC container address. Use `10.10.10.20:5020` if running with the included compose network.

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
