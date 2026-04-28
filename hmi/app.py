import os
import socket
import logging
from pathlib import Path
from typing import Any

import yaml
from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymodbus.client import ModbusTcpClient


app = Flask(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
LOG = logging.getLogger("ot-hmi")
CONFIG_PATH = Path(os.getenv("HMI_CONFIG", "/config/hmi.yaml"))
DEFAULT_CONFIG_PATH = Path("/app/config/hmi.yaml")

HMI_TYPES = {
    "manufacturing": {
        "label": "Manufacturing",
        "title": "Packaging Line HMI",
        "process": "Line 2 Pump Station",
        "primary": "Pump Run Command",
        "pressure_label": "Pneumatic / Water Pressure",
        "temperature_label": "Cabinet Temperature",
    },
    "water": {
        "label": "Water",
        "title": "Water Treatment HMI",
        "process": "Clearwell Transfer Pump",
        "primary": "Transfer Pump",
        "pressure_label": "Discharge Pressure",
        "temperature_label": "Pump Room Temperature",
    },
    "wastewater": {
        "label": "Wastewater",
        "title": "Wastewater Lift Station HMI",
        "process": "Wet Well Pump Control",
        "primary": "Lift Pump",
        "pressure_label": "Force Main Pressure",
        "temperature_label": "MCC Temperature",
    },
    "electrical_grid": {
        "label": "Electrical Grid",
        "title": "Substation Aux Systems HMI",
        "process": "Transformer Cooling Loop",
        "primary": "Cooling Pump",
        "pressure_label": "Cooling Loop Pressure",
        "temperature_label": "Transformer Ambient Temperature",
    },
}


def default_config() -> dict[str, Any]:
    return {
        "hmi_type": "water",
        "hmi_ip": os.getenv("HMI_IP", local_ip()),
        "plc_host": os.getenv("PLC_HOST", "plc"),
        "plc_port": int(os.getenv("PLC_PORT", "5020")),
        "unit_id": int(os.getenv("PLC_UNIT_ID", "1")),
    }


def local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("10.255.255.255", 1))
            return sock.getsockname()[0]
    except OSError:
        return "0.0.0.0"


def is_ipv4_address(value: str) -> bool:
    octets = value.split(".")
    return len(octets) == 4 and all(octet.isdigit() and 0 <= int(octet) <= 255 for octet in octets)


def normalize_base_ip(value: str) -> str:
    value = value.strip()
    return value if is_ipv4_address(value) else local_ip()


def expand_last_octet(value: str, base_ip: str) -> str:
    value = value.strip()
    if not value.isdigit():
        return value
    last_octet = int(value)
    if last_octet < 1 or last_octet > 254:
        return value
    base_ip = normalize_base_ip(base_ip)
    if not is_ipv4_address(base_ip):
        return value
    octets = base_ip.split(".")
    return ".".join([*octets[:3], str(last_octet)])


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        if DEFAULT_CONFIG_PATH.exists():
            with DEFAULT_CONFIG_PATH.open("r", encoding="utf-8") as handle:
                config = yaml.safe_load(handle) or default_config()
        else:
            config = default_config()
    else:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or default_config()
    config.setdefault("hmi_type", "water")
    config.setdefault("hmi_ip", os.getenv("HMI_IP", local_ip()))
    if str(config["hmi_ip"]).lower() in {"", "auto", "static"} or not is_ipv4_address(str(config["hmi_ip"])):
        config["hmi_ip"] = local_ip()
    config.setdefault("plc_host", os.getenv("PLC_HOST", "plc"))
    config.setdefault("plc_port", 5020)
    config.setdefault("unit_id", 1)
    return config


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)


def read_plc(config: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {
        "connected": False,
        "error": "",
        "pump_run_cmd": False,
        "alarm_active": False,
        "start_pb": False,
        "estop_ok": False,
        "door_closed": False,
        "tank_high": False,
        "pressure": None,
        "temperature": None,
    }
    client = ModbusTcpClient(host=config["plc_host"], port=int(config["plc_port"]), timeout=1)
    try:
        if not client.connect():
            values["error"] = "PLC connection failed"
            return values

        coils = client.read_coils(0, count=2, slave=int(config["unit_id"]))
        discrete = client.read_discrete_inputs(0, count=4, slave=int(config["unit_id"]))
        registers = client.read_input_registers(0, count=2, slave=int(config["unit_id"]))

        if coils.isError() or discrete.isError() or registers.isError():
            values["error"] = "PLC read returned a Modbus exception"
            return values

        values.update(
            {
                "connected": True,
                "pump_run_cmd": bool(coils.bits[0]),
                "alarm_active": bool(coils.bits[1]),
                "start_pb": bool(discrete.bits[0]),
                "estop_ok": bool(discrete.bits[1]),
                "door_closed": bool(discrete.bits[2]),
                "tank_high": bool(discrete.bits[3]),
                "pressure": registers.registers[0] / 10,
                "temperature": registers.registers[1] / 10,
            }
        )
    except Exception as exc:
        values["error"] = str(exc)
        LOG.warning("PLC read failed: %s", exc)
    finally:
        client.close()
    return values


@app.get("/")
def index():
    config = load_config()
    plc = read_plc(config)
    screen = HMI_TYPES.get(config["hmi_type"], HMI_TYPES["water"])
    return render_template("index.html", config=config, hmi_types=HMI_TYPES, plc=plc, screen=screen)


@app.get("/api/status")
def api_status():
    config = load_config()
    return jsonify({"config": config, "plc": read_plc(config)})


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "service": "hmi"})


@app.post("/settings")
def settings():
    config = load_config()
    hmi_type = request.form.get("hmi_type", config["hmi_type"])
    config["hmi_type"] = hmi_type if hmi_type in HMI_TYPES else "water"
    config["hmi_ip"] = normalize_base_ip(request.form.get("hmi_ip", config["hmi_ip"]))
    config["plc_host"] = expand_last_octet(
        request.form.get("plc_host", config["plc_host"]),
        config["hmi_ip"],
    )
    config["plc_port"] = int(request.form.get("plc_port", config["plc_port"]))
    config["unit_id"] = int(request.form.get("unit_id", config["unit_id"]))
    save_config(config)
    return redirect(url_for("index"))


if __name__ == "__main__":
    LOG.info("Starting HMI web server on 0.0.0.0:8090")
    app.run(host="0.0.0.0", port=8090)
