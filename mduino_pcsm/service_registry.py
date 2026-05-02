from __future__ import annotations

from mduino_pcsm.services.base import ControllerService
from mduino_pcsm.services.mock_controller import MockControllerService
from mduino_pcsm.services.serial_controller import SerialControllerService


def create_services() -> dict[str, ControllerService]:
    return {
        "Mock controller": MockControllerService(),
        "USB serial": SerialControllerService(),
    }
