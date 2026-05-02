from __future__ import annotations

from collections import deque
from datetime import datetime
import re
import time
from typing import Any

from mduino_pcsm.models import (
    CommandResult,
    ControllerSnapshot,
    ControllerStatus,
    EventEntry,
    PARAMETER_DEFINITIONS,
)
from mduino_pcsm.services.base import ControllerService

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - dependency may not be installed yet
    serial = None
    list_ports = None


class SerialControllerService(ControllerService):
    label = "USB serial"

    def __init__(self) -> None:
        self._connected = False
        self._port: str | None = None
        self._serial = None
        self._parameters = {
            definition.protocol_name: definition.default
            for definition in PARAMETER_DEFINITIONS
        }
        self._events: deque[EventEntry] = deque(maxlen=300)
        self._status = ControllerStatus(
            controller_state="OFFLINE",
            mode="UNKNOWN",
            arm_input=False,
            trigger_input=False,
            connection_status="Serial backend not connected",
            last_reason="Waiting for serial connection.",
            hotwire_enabled=bool(self._parameters["USE_HOTWIRE"]),
            firmware_version="unknown",
            last_state_change=datetime.now(),
        )

    @property
    def connected(self) -> bool:
        return self._connected

    def list_available_ports(self) -> list[str]:
        if list_ports is None:
            return []
        return [port.device for port in list_ports.comports()]

    def connect(self, port: str | None) -> CommandResult:
        if serial is None:
            return CommandResult(False, "pyserial is not installed in this environment.")
        if not port or port == "No ports found":
            return CommandResult(False, "Select a valid serial port first.")

        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=0.15,
                write_timeout=0.5,
            )
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
        except Exception as exc:
            return CommandResult(False, f"Unable to open {port}: {exc}")

        self._connected = True
        self._port = port
        self._status.connection_status = f"Connected to {port}"
        self._status.last_reason = "Listening for firmware status output."
        self._status.last_state_change = datetime.now()
        self._add_event(f"Connected to {port}.")
        self._read_serial_lines(duration=0.8)
        return CommandResult(True, self._status.connection_status)

    def disconnect(self) -> CommandResult:
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial = None
        self._connected = False
        self._port = None
        self._status.connection_status = "Serial backend not connected"
        self._status.last_reason = "Serial session closed."
        self._status.controller_state = "OFFLINE"
        self._status.mode = "UNKNOWN"
        self._status.arm_input = False
        self._status.trigger_input = False
        self._status.spark_active = False
        self._status.daq_active = False
        self._status.last_state_change = datetime.now()
        self._add_event("Disconnected from serial controller.")
        return CommandResult(True, "Disconnected.")

    def refresh(self) -> ControllerSnapshot:
        if self._connected:
            self._read_serial_lines(duration=0.2)
        return ControllerSnapshot(
            status=self._status,
            parameters=dict(self._parameters),
            events=list(self._events),
        )

    def set_parameter(self, protocol_name: str, raw_value: object) -> CommandResult:
        if not self._connected or self._serial is None:
            return CommandResult(False, "ERROR DISCONNECTED")

        command_value = "1" if protocol_name == "USE_HOTWIRE" and bool(raw_value) else str(int(raw_value))
        response = self._send_command(f"SET {protocol_name} {command_value}")
        if response is None:
            message = (
                "No explicit firmware acknowledgement received. "
                "Live monitoring still works, but runtime SET may not be implemented yet."
            )
            self._add_event(f"SET {protocol_name} {command_value} sent without acknowledgement.")
            return CommandResult(False, message)
        if response.startswith("ERROR"):
            self._add_event(f"{response}")
            self._status.last_reason = response
            return CommandResult(False, response)

        self._parameters[protocol_name] = raw_value
        if protocol_name == "USE_HOTWIRE":
            self._status.hotwire_enabled = bool(raw_value)
        self._status.last_reason = f"Accepted {protocol_name} update."
        self._add_event(f"{response}")
        self._read_serial_lines(duration=0.2)
        return CommandResult(True, response)

    def _send_command(self, command: str, expect_response: bool = True) -> str | None:
        if self._serial is None:
            return None
        try:
            self._serial.write(f"{command}\n".encode("utf-8"))
            self._serial.flush()
        except Exception as exc:
            self._status.last_reason = f"Serial write failed: {exc}"
            self._add_event(self._status.last_reason)
            return None

        self._add_event(f"> {command}")
        if not expect_response:
            return None

        deadline = time.monotonic() + 0.8
        while time.monotonic() < deadline:
            line = self._read_one_line()
            if not line:
                continue
            self._handle_line(line)
            if line.startswith(("OK", "ERROR", "VALUE ")):
                return line
        return None

    def _read_serial_lines(self, duration: float) -> None:
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            line = self._read_one_line()
            if not line:
                break
            self._handle_line(line)

    def _read_one_line(self) -> str | None:
        if self._serial is None:
            return None
        try:
            raw = self._serial.readline()
        except Exception as exc:
            self._status.last_reason = f"Serial read failed: {exc}"
            self._add_event(self._status.last_reason)
            return None
        if not raw:
            return None
        line = raw.decode("utf-8", errors="ignore").strip()
        return line or None

    def _handle_line(self, line: str) -> None:
        if line.startswith("STATUS | "):
            self._parse_status_line(line)
            return
        if line.startswith("STATE: "):
            self._parse_transition_line(line)
            return
        if line.startswith("VALUE "):
            self._parse_value_line(line)
            return
        if line.startswith("OK") or line.startswith("ERROR"):
            self._status.last_reason = line
            self._add_event(line)
            return
        if line.startswith("SPARK_TEST_EVENT: "):
            active = "started" in line.lower()
            self._status.spark_active = active
            self._status.last_reason = line
            self._status.last_state_change = datetime.now()
            self._add_event(line)
            return
        if "Trigger Box Controller" in line and "startup" in line:
            match = re.search(r"v(\d+)", line)
            if match:
                self._status.firmware_version = f"M_Duino_v{match.group(1)}"
            self._add_event(line)
            return
        self._parse_keyed_startup_line(line)

    def _parse_status_line(self, line: str) -> None:
        fields = self._parse_key_value_segments(line.split("|")[1:])
        mode = fields.get("Mode")
        arm = fields.get("Arm")
        trigger = fields.get("Trigger")
        state = fields.get("State")
        hotwire_step = fields.get("HotWireStep")

        if mode:
            self._status.mode = mode
        if state:
            self._status.controller_state = state
        if arm is not None:
            self._status.arm_input = self._coerce_bool(arm)
        if trigger is not None:
            self._status.trigger_input = self._coerce_bool(trigger)
        if hotwire_step is not None:
            hotwire_enabled = self._coerce_bool(hotwire_step)
            self._status.hotwire_enabled = hotwire_enabled
            self._parameters["USE_HOTWIRE"] = hotwire_enabled

        parameter_map = {
            "hotWireBurn_us": "HOTWIRE_US",
            "sparkDwell_us": "SPARK_US",
            "daqPulse_us": "DAQ_US",
            "sparkTestInterval_us": "SPARKTEST_US",
        }
        for source_key, target_key in parameter_map.items():
            if source_key in fields:
                self._parameters[target_key] = self._coerce_int(fields[source_key], self._parameters[target_key])

        self._status.connection_status = f"Connected to {self._port}"
        self._status.last_state_change = datetime.now()

    def _parse_transition_line(self, line: str) -> None:
        match = re.match(r"STATE:\s+(\w+)\s+->\s+(\w+)(?:\s+\|\s+reason=(.*))?$", line)
        if not match:
            self._add_event(line)
            return
        _, new_state, reason = match.groups()
        self._status.controller_state = new_state
        self._status.last_reason = reason or "State transition observed."
        self._status.last_state_change = datetime.now()
        self._add_event(line)

    def _parse_value_line(self, line: str) -> None:
        parts = line.split()
        if len(parts) < 3:
            self._add_event(line)
            return
        name = parts[1]
        raw_value = parts[2]
        if name in self._parameters:
            if name == "USE_HOTWIRE":
                self._parameters[name] = self._coerce_bool(raw_value)
                self._status.hotwire_enabled = bool(self._parameters[name])
            else:
                self._parameters[name] = self._coerce_int(raw_value, self._parameters[name])
        self._add_event(line)

    def _parse_keyed_startup_line(self, line: str) -> None:
        mapping: dict[str, tuple[str, str]] = {
            "Hot-wire step enabled": ("USE_HOTWIRE", "bool"),
            "hotWireBurn_us": ("HOTWIRE_US", "int"),
            "sparkDwell_us": ("SPARK_US", "int"),
            "daqPulse_us": ("DAQ_US", "int"),
            "sparkTestInterval_us": ("SPARKTEST_US", "int"),
        }
        if ": " not in line:
            self._add_event(line)
            return
        key, value = line.split(": ", 1)
        if key in mapping:
            protocol_name, kind = mapping[key]
            if kind == "bool":
                parsed = self._coerce_bool(value)
                self._parameters[protocol_name] = parsed
                self._status.hotwire_enabled = parsed
            else:
                self._parameters[protocol_name] = self._coerce_int(value, self._parameters[protocol_name])
        self._add_event(line)

    def _parse_key_value_segments(self, segments: list[str]) -> dict[str, str]:
        parsed: dict[str, str] = {}
        for segment in segments:
            part = segment.strip()
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            parsed[key.strip()] = value.strip()
        return parsed

    def _coerce_bool(self, value: Any) -> bool:
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _coerce_int(self, value: Any, fallback: Any) -> int:
        try:
            return int(str(value).strip())
        except Exception:
            return int(fallback)

    def _add_event(self, message: str) -> None:
        self._events.appendleft(EventEntry(timestamp=datetime.now(), message=message))
