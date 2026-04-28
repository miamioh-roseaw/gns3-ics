import logging
import os
import signal
import threading
import time
from dataclasses import dataclass
from typing import Any

import requests
import yaml
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext
from pymodbus.server import StartTcpServer


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
LOG = logging.getLogger("ot-plc")


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


def main() -> None:
    config = load_config()
    context = build_context()
    runtime = PlcRuntime(config, context)
    signal.signal(signal.SIGTERM, runtime.stop)
    signal.signal(signal.SIGINT, runtime.stop)

    scan_thread = threading.Thread(target=runtime.run, daemon=True)
    scan_thread.start()

    port = int(os.getenv("MODBUS_PORT", config.get("modbus_port", 5020)))
    LOG.info("Starting Modbus TCP server on 0.0.0.0:%s", port)
    StartTcpServer(context=context, address=("0.0.0.0", port))


if __name__ == "__main__":
    main()
