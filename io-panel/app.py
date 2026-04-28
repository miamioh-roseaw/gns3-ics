import os
from pathlib import Path
from typing import Any

import yaml
from flask import Flask, abort, jsonify, redirect, render_template, request, url_for


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

BASELINE_POINTS = {
    "pressure": {"device_type": "pressure_sensor", "value": 72.5},
    "temperature": {"device_type": "temperature_sensor", "value": 89.0},
    "start_pb": {"device_type": "push_button", "value": False},
    "estop_ok": {"device_type": "e_stop_contact", "value": True},
    "door_closed": {"device_type": "door_interlock", "value": True},
    "tank_high": {"device_type": "float_switch", "value": False},
}

SCENARIOS = {
    "ambient_heat_rise": {
        "label": "Ambient Heat Rise",
        "severity": "Process upset",
        "description": "Raise the temperature transmitter to simulate a hot enclosure or nearby heat source.",
        "setpoints": {"temperature": 145.0},
    },
    "water_pressure_surge": {
        "label": "Water Pressure Surge",
        "severity": "High alarm",
        "description": "Drive the pressure transmitter upward as if a downstream valve closed suddenly.",
        "setpoints": {"pressure": 265.0},
    },
    "blocked_outlet": {
        "label": "Blocked Outlet",
        "severity": "Process fault",
        "description": "Combine high pressure with a high tank float to mimic a restricted discharge path.",
        "setpoints": {"pressure": 220.0, "tank_high": True},
    },
    "door_interlock_open": {
        "label": "Door Interlock Open",
        "severity": "Safety permissive",
        "description": "Open the panel door interlock so the PLC should drop permissive logic.",
        "setpoints": {"door_closed": False},
    },
    "estop_pressed": {
        "label": "E-Stop Pressed",
        "severity": "Safety trip",
        "description": "Open the e-stop contact and verify the SCADA alarm and PLC output response.",
        "setpoints": {"estop_ok": False},
    },
    "pressure_sensor_failed_low": {
        "label": "Pressure Sensor Failed Low",
        "severity": "Instrumentation fault",
        "description": "Force the pressure signal near zero while the rest of the process remains normal.",
        "setpoints": {"pressure": 0.0},
    },
}


def default_config() -> dict[str, Any]:
    return {
        "active_scenario": "normal",
        "points": {name: point.copy() for name, point in BASELINE_POINTS.items()},
    }


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        save_config(default_config())
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or default_config()
    config.setdefault("active_scenario", "normal")
    config.setdefault("points", {})
    return config


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)


@app.get("/")
def index():
    config = load_config()
    return render_template(
        "index.html",
        config=config,
        device_types=DEVICE_TYPES,
        scenarios=SCENARIOS,
    )


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
    return jsonify({"active_scenario": config.get("active_scenario", "normal"), "points": points})


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
    config["active_scenario"] = "manual_override"
    save_config(config)
    return redirect(url_for("index"))


@app.post("/scenario/<scenario_id>")
def apply_scenario(scenario_id: str):
    config = load_config()
    if scenario_id not in SCENARIOS:
        abort(404)
    scenario = SCENARIOS[scenario_id]
    for name, value in scenario["setpoints"].items():
        if name in config.get("points", {}):
            config["points"][name]["value"] = value
    config["active_scenario"] = scenario_id
    save_config(config)
    return redirect(url_for("index"))


@app.post("/scenario/reset")
def reset_scenario():
    config = load_config()
    config["points"] = {name: point.copy() for name, point in BASELINE_POINTS.items()}
    config["active_scenario"] = "normal"
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
    config["active_scenario"] = "manual_override"
    save_config(config)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
