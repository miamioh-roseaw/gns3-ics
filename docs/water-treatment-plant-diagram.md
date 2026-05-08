# Water Treatment Plant OT Diagram

This diagram gives the GNS3 lab a water treatment plant scenario using the existing PLC, Remote I/O, and HMI containers. It shows where the simulated field sensors belong in the process and how those signals move through the OT network.

## Process And Sensor Layout

```mermaid
flowchart LR
    raw["Raw Water Source"]
    intake["Raw Water Intake<br/>Intake pump and screen"]
    chem["Chemical Feed<br/>Coagulant and pH adjustment"]
    mix["Rapid Mix / Flocculation Basin"]
    clarifier["Clarifier<br/>Settling and sludge collection"]
    filters["Media Filters<br/>Turbidity and head-loss control"]
    clearwell["Clearwell / Storage Tank"]
    pumps["High-Service Pumps"]
    distribution["Distribution Header"]

    raw --> intake --> chem --> mix --> clarifier --> filters --> clearwell --> pumps --> distribution

    intakeSensors["Intake Sensors<br/>LS-101 screen limit switch<br/>PB-101 local start push button<br/>ES-101 pump e-stop contact"]
    chemSensors["Chemical Feed Sensors<br/>PT-201 feed pressure sensor<br/>TT-201 room temperature sensor<br/>DI-201 cabinet door interlock"]
    clarifierSensors["Clarifier Sensors<br/>FS-301 high float switch<br/>PX-301 scraper proximity sensor<br/>LS-301 sludge valve limit switch"]
    filterSensors["Filter Sensors<br/>PT-401 filter pressure sensor<br/>LS-401 backwash valve limit switch<br/>PB-401 manual backwash push button"]
    clearwellSensors["Clearwell Sensors<br/>FS-501 low/high float switches<br/>TT-501 water temperature sensor<br/>DI-501 hatch door interlock"]
    pumpSensors["Pump Station Sensors<br/>PT-601 discharge pressure sensor<br/>ES-601 pump e-stop contact<br/>PX-601 motor coupling proximity sensor"]

    intakeSensors -. field wiring .-> rio
    chemSensors -. field wiring .-> rio
    clarifierSensors -. field wiring .-> rio
    filterSensors -. field wiring .-> rio
    clearwellSensors -. field wiring .-> rio
    pumpSensors -. field wiring .-> rio

    rio["Remote I/O Panel<br/>cithit/ot-rio-7<br/>Instructor panel :8080"]
    plc["PLC<br/>cithit/ot-plc-7<br/>Modbus TCP :5020<br/>Settings panel :8081"]
    hmi["Water HMI<br/>cithit/ot-hmi-7<br/>Operator panel :8090"]
    ignition["Ignition / SCADA<br/>Modbus TCP client"]

    rio -- "sensor state API" --> plc
    plc -- "Modbus TCP" --> hmi
    plc -- "Modbus TCP" --> ignition
```

## OT Network View

```mermaid
flowchart TB
    subgraph field["Field Instrument Layer"]
        pressure["Pressure sensors"]
        temperature["Temperature sensors"]
        limits["Limit switches"]
        pushbuttons["Push buttons"]
        estops["E-stop contacts"]
        doors["Door interlocks"]
        floats["Float switches"]
        proximity["Proximity sensors"]
    end

    subgraph control["Control Layer"]
        rio["Remote I/O<br/>IP set at console<br/>Web :8080"]
        plc["PLC<br/>IP set at console<br/>Modbus :5020<br/>Web :8081"]
    end

    subgraph operations["Operations Layer"]
        hmi["HMI<br/>Water scenario selected<br/>Web :8090"]
        scada["Ignition SCADA<br/>Modbus driver"]
        instructor["Instructor workstation<br/>Fault and process injection"]
    end

    pressure --> rio
    temperature --> rio
    limits --> rio
    pushbuttons --> rio
    estops --> rio
    doors --> rio
    floats --> rio
    proximity --> rio

    instructor -- "changes sensor values and fault presets" --> rio
    instructor -- "changes PLC scan and Remote I/O URL" --> plc
    rio -- "simulated field values" --> plc
    hmi -- "read coils, discrete inputs, input registers" --> plc
    scada -- "read coils, discrete inputs, input registers" --> plc
```

## Suggested I/O Map

The existing containers already expose a starter Modbus map. These tags can be reused for the water treatment scenario or expanded as more points are added.

| Water plant signal | Sensor type | Container point | Modbus area | Reference |
| --- | --- | --- | --- | --- |
| High-service pump run command | Output coil | `pump_run_cmd` | Coil | `000001` |
| Plant alarm active | Output coil | `alarm_active` | Coil | `000002` |
| Local pump start | Push button | `start_pb` | Discrete Input | `100001` |
| Pump e-stop healthy | E-stop contact | `estop_ok` | Discrete Input | `100002` |
| Pump room door closed | Door interlock | `door_closed` | Discrete Input | `100003` |
| Clearwell high level | Float switch | `tank_high` | Discrete Input | `100004` |
| Discharge pressure | Pressure sensor | `pressure` | Input Register | `300001`, scaled x10 |
| Water or room temperature | Temperature sensor | `temperature` | Input Register | `300002`, scaled x10 |

## Instructor Scenario Ideas

The Remote I/O instructor panel can drive common water treatment faults:

- Increase ambient temperature in the pump room to test cooling and alarm response.
- Dramatically increase discharge or filter pressure to simulate a blocked outlet or fouled filter.
- Open a door interlock during operation to test safety permissives.
- Trip an e-stop contact to verify pump shutdown logic.
- Force a float switch high or low to simulate a clearwell level problem.
- Toggle a proximity sensor to simulate rotating equipment feedback loss.
- Toggle limit switches to simulate a stuck valve or failed position indication.

## GNS3 Placement

Use one Docker appliance per OT role:

| Device | Docker image | Primary lab purpose | Student-facing URL |
| --- | --- | --- | --- |
| PLC | `cithit/ot-plc-7:latest` | Ladder-style scan and Modbus TCP server | `http://<plc-ip>:8081` |
| Remote I/O | `cithit/ot-rio-7:latest` | Field sensor selection and instructor faults | `http://<rio-ip>:8080` |
| HMI | `cithit/ot-hmi-7:latest` | Water treatment operator screen | `http://<hmi-ip>:8090` |

For a simple /24 lab network, assign the containers from the console prompt, for example:

```text
PLC:        192.168.1.2/24
Remote I/O: 192.168.1.3/24
HMI:        192.168.1.4/24
Ignition:   192.168.1.10/24
```

In the HMI, select the Water scenario and enter the PLC as either the full IP address, such as `192.168.1.2`, or the last octet, such as `2`, when the HMI is on the same /24 network.
