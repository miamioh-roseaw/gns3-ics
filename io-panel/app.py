import os
from pathlib import Path
from typing import Any

import yaml
from flask import Flask, jsonify, redirect, render_template, request, url_for


app = Flask(__name__)
CONFIG_PATH = Path(os.getenv("IO_CONFIG", "/config/io-panel.yaml"))

DEVICE_TYPES = {
    "pressure_sensor": {"label": "Pressure Sensor", "kind": "analog", "unit": "psi", "min": 0, "max": 300},
    "temperature_sensor": {"label": "Temperature Sensor", "kind": "analog", "unit": "degF", "min": -40, "max": 400},
    "limit_switch": {"label": "Limit Switch", "kind": "digital"},
    "push_button": {"label": "Push Button", "kind": "digital"},
    "e_stop_contact": {"label": "E-Stop Contact", "kind": "digital"},
    "door_interlock": {"label": "Door Interlock", "kind": "digital"},
    "float_switch": {"label": "Float Switch", "kind": "digital"},
    "proximity_sensor": {"label": "Proximity Sensor", "kind": "digital"},
}


def default_config() -> dict[str, Any]:
    return {
        "points": {
            "pressure": {"device_type": "pressure_sensor", "value": 72.5},
            "temperature": {"device_type": "temperature_sensor", "value": 89.0},
            "start_pb": {"device_type": "push_button", "value": False},
            "estop_ok": {"device_type": "e_stop_contact", "value": True},
            "door_closed": {"device_type": "door_interlock", "value": True},
            "tank_high": {"device_type": "float_switch", "value": False},
        }
    }


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        save_config(default_config())
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or default_config()


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)


@app.get("/")
def index():
    config = load_config()
    return render_template("index.html", config=config, device_types=DEVICE_TYPES)


@app.get("/api/io")
def api_io():
    config = load_config()
    points = {}
    for name, point in config.get("points", {}).items():
        meta = DEVICE_TYPES.get(point["device_type"], {})
        points[name] = {
            "device_type": point["device_type"],
            "label": meta.get("label", point["device_type"]),
            "kind": meta.get("kind", "digital"),
            "unit": meta.get("unit", ""),
            "value": point.get("value", False),
        }
    return jsonify({"points": points})


@app.post("/point/<name>")
def update_point(name: str):
    config = load_config()
    point = config["points"][name]
    device_type = request.form.get("device_type", point["device_type"])
    point["device_type"] = device_type
    meta = DEVICE_TYPES[device_type]
    if meta["kind"] == "analog":
        point["value"] = float(request.form.get("value", 0))
    else:
        point["value"] = request.form.get("value") == "on"
    save_config(config)
    return redirect(url_for("index"))


@app.post("/point")
def add_point():
    config = load_config()
    name = request.form["name"].strip().lower().replace(" ", "_")
    device_type = request.form["device_type"]
    meta = DEVICE_TYPES[device_type]
    config.setdefault("points", {})[name] = {
        "device_type": device_type,
        "value": 0.0 if meta["kind"] == "analog" else False,
    }
    save_config(config)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
