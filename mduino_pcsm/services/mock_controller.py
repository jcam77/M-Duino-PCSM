from __future__ import annotations

from collections import deque
from datetime import datetime

from mduino_pcsm.models import (
    CommandResult,
    ControllerSnapshot,
    ControllerStatus,
    EventEntry,
    PARAMETER_DEFINITIONS,
)
from mduino_pcsm.services.base import ControllerService


class MockControllerService(ControllerService):
    label = "Mock controller"

    def __init__(self) -> None:
        self._connected = False
        self._selected_port = "MOCK-MDUINO-001"
        self._parameters = {
            definition.protocol_name: definition.default
            for definition in PARAMETER_DEFINITIONS
        }
        self._status = ControllerStatus(
            controller_state="IDLE",
            mode="HYDROGEN_TEST",
            arm_input=False,
            trigger_input=False,
            connection_status="Disconnected",
            last_reason="Waiting for connection.",
            hotwire_enabled=True,
        )
        self._events: deque[EventEntry] = deque(maxlen=200)
        self._demo_step = 0
        self._add_event("Mock backend ready.")

    @property
    def connected(self) -> bool:
        return self._connected

    def list_available_ports(self) -> list[str]:
        return [self._selected_port]

    def connect(self, port: str | None) -> CommandResult:
        self._selected_port = port or self._selected_port
        self._connected = True
        self._status.connection_status = f"Connected to {self._selected_port}"
        self._status.last_reason = "Mock controller connected."
        self._status.last_state_change = datetime.now()
        self._add_event(f"Connected to {self._selected_port}.")
        return CommandResult(True, self._status.connection_status)

    def disconnect(self) -> CommandResult:
        self._connected = False
        self._status.connection_status = "Disconnected"
        self._status.last_reason = "Operator disconnected session."
        self._status.arm_input = False
        self._status.trigger_input = False
        self._status.spark_active = False
        self._status.daq_active = False
        self._status.controller_state = "IDLE"
        self._status.last_state_change = datetime.now()
        self._add_event("Disconnected from mock controller.")
        return CommandResult(True, "Disconnected.")

    def refresh(self) -> ControllerSnapshot:
        if self._connected:
            self._status.connection_status = f"Connected to {self._selected_port}"
        return self._snapshot()

    def set_parameter(self, protocol_name: str, raw_value: object) -> CommandResult:
        if not self._connected:
            return CommandResult(False, "ERROR DISCONNECTED")
        if self._status.controller_state != "IDLE":
            return CommandResult(False, "ERROR NOT_IDLE")
        if protocol_name not in self._parameters:
            return CommandResult(False, "ERROR UNKNOWN_PARAMETER")

        if protocol_name == "DAQ_US":
            spark_us = int(self._parameters["SPARK_US"])
            if int(raw_value) > spark_us:
                return CommandResult(False, "ERROR DAQ_GT_SPARK")
        if protocol_name == "SPARK_US":
            daq_us = int(self._parameters["DAQ_US"])
            if daq_us > int(raw_value):
                return CommandResult(False, "ERROR SPARK_LT_DAQ")

        for definition in PARAMETER_DEFINITIONS:
            if definition.protocol_name != protocol_name or definition.kind == "bool":
                continue
            if definition.min_raw is not None and int(raw_value) < definition.min_raw:
                return CommandResult(False, "ERROR OUT_OF_RANGE")
            if definition.max_raw is not None and int(raw_value) > definition.max_raw:
                return CommandResult(False, "ERROR OUT_OF_RANGE")

        self._parameters[protocol_name] = raw_value
        if protocol_name == "USE_HOTWIRE":
            self._status.hotwire_enabled = bool(raw_value)

        self._status.last_reason = f"Accepted {protocol_name} update."
        self._add_event(f"SET {protocol_name} -> {raw_value} accepted.")
        return CommandResult(True, "OK")

    def run_demo_transition(self) -> CommandResult:
        if not self._connected:
            return CommandResult(False, "Connect the mock controller first.")

        sequence = (
            ("ARMED", True, False, False, False, "arm engaged"),
            ("MELTING", True, True, False, False, "trigger received; hot-wire started"),
            ("SPARK_WAIT_DAQ", True, True, True, False, "spark stage active"),
            ("FIRED", False, False, False, True, "sequence completed successfully"),
            ("IDLE", False, False, False, False, "operator reset after fired state"),
        )
        state, arm, trigger, spark, daq, reason = sequence[self._demo_step]
        self._demo_step = (self._demo_step + 1) % len(sequence)
        self._status.controller_state = state
        self._status.arm_input = arm
        self._status.trigger_input = trigger
        self._status.spark_active = spark
        self._status.daq_active = daq
        self._status.last_reason = reason
        self._status.last_state_change = datetime.now()
        self._add_event(f"STATE {state}: {reason}.")
        return CommandResult(True, f"Mock transition -> {state}")

    def _snapshot(self) -> ControllerSnapshot:
        return ControllerSnapshot(
            status=self._status,
            parameters=dict(self._parameters),
            events=list(self._events),
        )

    def _add_event(self, message: str) -> None:
        self._events.appendleft(EventEntry(timestamp=datetime.now(), message=message))

