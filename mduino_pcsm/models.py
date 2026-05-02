from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ParameterDefinition:
    firmware_name: str
    protocol_name: str
    label: str
    ui_unit: str
    kind: str
    default: Any
    raw_per_display_unit: float = 1.0
    min_raw: int | None = None
    max_raw: int | None = None
    step: float | int = 1
    help_text: str = ""

    def raw_to_display(self, raw_value: Any) -> Any:
        if self.kind == "bool":
            return bool(raw_value)
        display_value = raw_value / self.raw_per_display_unit
        if self.kind == "int":
            return int(round(display_value))
        return float(display_value)

    def display_to_raw(self, display_value: Any) -> Any:
        if self.kind == "bool":
            return bool(display_value)
        return int(round(float(display_value) * self.raw_per_display_unit))


@dataclass
class ControllerStatus:
    controller_state: str
    mode: str
    arm_input: bool
    trigger_input: bool
    connection_status: str
    last_reason: str
    spark_active: bool = False
    daq_active: bool = False
    hotwire_enabled: bool = True
    firmware_version: str = "M_Duino_v002"
    last_state_change: datetime = field(default_factory=datetime.now)


@dataclass
class EventEntry:
    timestamp: datetime
    message: str


@dataclass
class CommandResult:
    success: bool
    message: str


@dataclass
class ControllerSnapshot:
    status: ControllerStatus
    parameters: dict[str, Any]
    events: list[EventEntry]


PARAMETER_DEFINITIONS: tuple[ParameterDefinition, ...] = (
    ParameterDefinition(
        firmware_name="hotWireBurn_us",
        protocol_name="HOTWIRE_US",
        label="Hot-wire burn time",
        ui_unit="s",
        kind="float",
        default=15_000_000,
        raw_per_display_unit=1_000_000,
        min_raw=100_000,
        max_raw=60_000_000,
        step=0.1,
        help_text="Main tuning parameter for the melting stage.",
    ),
    ParameterDefinition(
        firmware_name="sparkDwell_us",
        protocol_name="SPARK_US",
        label="Spark dwell",
        ui_unit="us",
        kind="int",
        default=5_000,
        min_raw=100,
        max_raw=100_000,
        step=100,
        help_text="Spark pulse duration.",
    ),
    ParameterDefinition(
        firmware_name="daqPulse_us",
        protocol_name="DAQ_US",
        label="DAQ pulse width",
        ui_unit="us",
        kind="int",
        default=600,
        min_raw=50,
        max_raw=100_000,
        step=50,
        help_text="DAQ pulse width. Must not exceed spark dwell.",
    ),
    ParameterDefinition(
        firmware_name="sparkTestInterval_us",
        protocol_name="SPARKTEST_US",
        label="Spark-test interval",
        ui_unit="ms",
        kind="int",
        default=500_000,
        raw_per_display_unit=1_000,
        min_raw=50_000,
        max_raw=5_000_000,
        step=50,
        help_text="Used in spark-test mode.",
    ),
    ParameterDefinition(
        firmware_name="useHotWireStep",
        protocol_name="USE_HOTWIRE",
        label="Use hot-wire step",
        ui_unit="bool",
        kind="bool",
        default=True,
        help_text="Enables or skips the melting stage.",
    ),
)
