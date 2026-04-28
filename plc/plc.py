import logging
import os
import signal
import threading
import time
from dataclasses import dataclass
from typing import Any

import requests
import yaml
from flask import Flask, jsonify, redirect, render_template_string, request, url_for
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext
from pymodbus.server import StartTcpServer


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
LOG = logging.getLogger("ot-plc")

PLC_SETTINGS_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PLC Settings</title>
    <style>
      :root { color-scheme: dark; font-family: Inter, system-ui, sans-serif; background: #101416; color: #eef3ef; }
      * { box-sizing: border-box; }
      body { margin: 0; background: #101416; }
      main { width: min(980px, calc(100vw - 32px)); margin: 0 auto; padding: 24px 0; }
      header, section { border: 1px solid #30403a; border-radius: 8px; background: #17201c; padding: 16px; margin-bottom: 14px; }
      h1, h2, p { margin: 0; }
      h1 { font-size: 28px; }
      h2 { font-size: 18px; margin-bottom: 12px; }
      p { margin-top: 6px; color: #aebdb5; }
      form { display: grid; grid-template-columns: 1fr 1fr 140px; gap: 12px; align-items: end; }
      label { display: grid; gap: 7px; color: #b9c8c0; font-size: 13px; font-weight: 750; }
      input, button { min-height: 42px; border: 1px solid #3d5048; border-radius: 6px; padding: 8px 10px; }
      input { background: #0f1513; color: #eef3ef; }
      button { background: #d7f5aa; color: #102016; font-weight: 850; cursor: pointer; }
      table { width: 100%; border-collapse: collapse; }
      th, td { padding: 9px 8px; border-bottom: 1px solid #2d3c36; text-align: left; }
      th { color: #d7f5aa; }
      code { color: #d7f5aa; }
      @media (max-width: 720px) { form { grid-template-columns: 1fr; } }
    </style>
  </head>
  <body>
    <main>
      <header>
        <h1>PLC Settings</h1>
        <p>Modbus TCP on <code>{{ modbus_port }}</code>. Web settings on <code>{{ web_port }}</code>.</p>
      </header>
      <section>
        <h2>Runtime</h2>
        <form action="/settings" method="post">
          <label>
            Scan Time ms
            <input name="scan_ms" type="number" min="10" max="5000" value="{{ runtime.scan_ms }}">
          </label>
          <label>
            Remote I/O URL
            <input name="io_panel_url" value="{{ runtime.io_panel_url }}" placeholder="http://192.168.1.3:8080/api/io">
          </label>
          <button type="submit">Apply</button>
        </form>
      </section>
      <section>
        <h2>Points</h2>
        <table>
          <thead><tr><th>Name</th><th>Type</th><th>Address</th><th>Value</th></tr></thead>
          <tbody>
            {% for point in runtime.points %}
            <tr><td>{{ point.name }}</td><td>{{ point.type }}</td><td>{{ point.address }}</td><td>{{ point.value }}</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </section>
    </main>
  </body>
</html>
"""


@dataclass
class Point:
    name: str
    type: str
    address: int
    source: str
    scale: float = 1.0
    value: float | bool = 0


class PlcRuntime:
    def __init__(self, config: dict[str, Any], context: ModbusServerContext):
        self.config = config
        self.context = context
        self.points = [Point(**point) for point in config.get("points", [])]
        self.scan_ms = int(config.get("scan_ms", 100))
        self.io_panel_url = os.getenv("IO_PANEL_URL", config.get("io_panel_url", ""))
        self.running = True
        self.last_toggle = time.monotonic()

    def run(self) -> None:
        LOG.info("PLC scan started: %sms", self.scan_ms)
        while self.running:
            started = time.monotonic()
            io_values = self._read_remote_io()
            self._update_inputs(io_values)
            self._execute_ladder()
            self._sleep_until_next_scan(started)

    def stop(self, *_args: object) -> None:
        self.running = False

    def update_settings(self, scan_ms: int, io_panel_url: str) -> None:
        self.scan_ms = scan_ms
        self.io_panel_url = io_panel_url

    def _read_remote_io(self) -> dict[str, Any]:
        if not self.io_panel_url:
            return {}
        try:
            response = requests.get(self.io_panel_url, timeout=0.25)
            response.raise_for_status()
            return response.json().get("points", {})
        except requests.RequestException as exc:
            LOG.debug("Remote I/O read failed: %s", exc)
            return {}

    def _update_inputs(self, io_values: dict[str, Any]) -> None:
        for point in self.points:
            if point.name in io_values:
                point.value = io_values[point.name]["value"]
            if point.type in {"coil", "discrete_input"}:
                value = 1 if bool(point.value) else 0
                function = 1 if point.type == "coil" else 2
            else:
                value = int(float(point.value) * point.scale)
                function = 3 if point.type == "holding_register" else 4
            self.context[0].setValues(function, point.address, [value])

    def _execute_ladder(self) -> None:
        """Tiny ladder-like scan: contacts drive coils in declaration order."""
        for rung in self.config.get("ladder", []):
            contacts = rung.get("contacts", [])
            energized = all(self._contact_state(contact) for contact in contacts)
            coil = rung.get("coil")
            if coil:
                self._write_bool(coil, energized)

    def _contact_state(self, contact: dict[str, Any]) -> bool:
        name = contact["name"]
        normally_closed = bool(contact.get("normally_closed", False))
        state = bool(self._read_named_value(name))
        return not state if normally_closed else state

    def _read_named_value(self, name: str) -> Any:
        for point in self.points:
            if point.name == name:
                return point.value
        return False

    def _write_bool(self, name: str, value: bool) -> None:
        for point in self.points:
            if point.name == name:
                point.value = value
                function = 1 if point.type == "coil" else 2
                self.context[0].setValues(function, point.address, [1 if value else 0])
                return

    def _sleep_until_next_scan(self, started: float) -> None:
        elapsed = (time.monotonic() - started) * 1000
        time.sleep(max((self.scan_ms - elapsed) / 1000, 0.001))


def build_context() -> ModbusServerContext:
    slave = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * 10000),
        co=ModbusSequentialDataBlock(0, [0] * 10000),
        hr=ModbusSequentialDataBlock(0, [0] * 10000),
        ir=ModbusSequentialDataBlock(0, [0] * 10000),
        zero_mode=True,
    )
    return ModbusServerContext(slaves=slave, single=True)


def load_config() -> dict[str, Any]:
    config_path = os.getenv("PLC_CONFIG", "/config/plc.yaml")
    if not os.path.exists(config_path):
        fallback_path = "/app/config/plc.yaml"
        LOG.warning("Config %s not found; using built-in default %s", config_path, fallback_path)
        config_path = fallback_path
    with open(config_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def create_web_app(runtime: PlcRuntime, modbus_port: int, web_port: int) -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template_string(
            PLC_SETTINGS_TEMPLATE,
            runtime=runtime,
            modbus_port=modbus_port,
            web_port=web_port,
        )

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok", "service": "plc"})

    @app.get("/api/status")
    def api_status():
        return jsonify(
            {
                "scan_ms": runtime.scan_ms,
                "io_panel_url": runtime.io_panel_url,
                "points": [
                    {"name": point.name, "type": point.type, "address": point.address, "value": point.value}
                    for point in runtime.points
                ],
            }
        )

    @app.post("/settings")
    def settings():
        scan_ms = int(request.form.get("scan_ms", runtime.scan_ms))
        io_panel_url = request.form.get("io_panel_url", runtime.io_panel_url).strip()
        runtime.update_settings(scan_ms, io_panel_url)
        return redirect(url_for("index"))

    return app


def main() -> None:
    config = load_config()
    context = build_context()
    runtime = PlcRuntime(config, context)
    signal.signal(signal.SIGTERM, runtime.stop)
    signal.signal(signal.SIGINT, runtime.stop)

    scan_thread = threading.Thread(target=runtime.run, daemon=True)
    scan_thread.start()

    port = int(os.getenv("MODBUS_PORT", config.get("modbus_port", 5020)))
    web_port = int(os.getenv("PLC_WEB_PORT", "8081"))
    web_app = create_web_app(runtime, port, web_port)
    web_thread = threading.Thread(
        target=lambda: web_app.run(host="0.0.0.0", port=web_port, use_reloader=False),
        daemon=True,
    )
    web_thread.start()
    LOG.info("Starting PLC settings web server on 0.0.0.0:%s", web_port)

    LOG.info("Starting Modbus TCP server on 0.0.0.0:%s", port)
    StartTcpServer(context=context, address=("0.0.0.0", port))


if __name__ == "__main__":
    main()
