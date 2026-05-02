from __future__ import annotations

from abc import ABC, abstractmethod

from mduino_pcsm.models import CommandResult, ControllerSnapshot


class ControllerService(ABC):
    """Shared backend interface for mock and real controller transports."""

    label: str = "Controller"

    @abstractmethod
    def list_available_ports(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def connect(self, port: str | None) -> CommandResult:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> CommandResult:
        raise NotImplementedError

    @abstractmethod
    def refresh(self) -> ControllerSnapshot:
        raise NotImplementedError

    @abstractmethod
    def set_parameter(self, protocol_name: str, raw_value: object) -> CommandResult:
        raise NotImplementedError

    @property
    @abstractmethod
    def connected(self) -> bool:
        raise NotImplementedError

