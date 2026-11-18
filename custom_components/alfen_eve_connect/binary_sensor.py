"""Binary sensors for Alfen Eve Connect."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AlfenConfigEntry
from .const import MAIN_STATE_NO_VEHICLE, PROP_MAIN_STATE
from .entity import AlfenEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlfenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([AlfenVehicleConnectedSensor(entry.runtime_data)])


class AlfenVehicleConnectedSensor(AlfenEntity, BinarySensorEntity):
    """On when a vehicle is plugged in (any main state other than 'no vehicle')."""

    _attr_device_class = BinarySensorDeviceClass.PLUG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "vehicle_connected")

    @property
    def is_on(self) -> bool | None:
        state = self.prop(PROP_MAIN_STATE)
        try:
            return int(state) != MAIN_STATE_NO_VEHICLE
        except (TypeError, ValueError):
            return None
