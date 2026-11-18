"""Charging on/off switch for Alfen Eve Connect."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AlfenConfigEntry
from .api import AlfenError
from .entity import AlfenEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlfenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([AlfenChargingSwitch(entry.runtime_data)])


class AlfenChargingSwitch(AlfenEntity, SwitchEntity):
    """On = charging allowed, off = paused (0 A charging profile)."""

    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charging")

    @property
    def is_on(self) -> bool | None:
        paused = self.coordinator.data.paused
        return None if paused is None else not paused

    async def async_turn_on(self, **kwargs: Any) -> None:
        try:
            await self.coordinator.client.resume_charging()
        except AlfenError as err:
            raise HomeAssistantError(f"Starten van laden mislukt: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            await self.coordinator.client.pause_charging()
        except AlfenError as err:
            raise HomeAssistantError(f"Stoppen van laden mislukt: {err}") from err
        await self.coordinator.async_request_refresh()
