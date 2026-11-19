"""Charging mode select (normal / solar only) for Alfen Eve Connect."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AlfenConfigEntry
from .api import AlfenError
from .const import (
    CHARGING_MODES,
    MODE_COMFORT,
    MODE_NORMAL,
    MODE_SOLAR,
    PROP_MAX_PHASES,
    PROP_SOLAR_GREEN_SHARE,
    PROP_SOLAR_MODE,
    SOLAR_MODE_COMFORT,
    SOLAR_MODE_DISABLED,
    SOLAR_MODE_GREEN,
)
from .entity import AlfenEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlfenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([AlfenChargingModeSelect(entry.runtime_data)])


class AlfenChargingModeSelect(AlfenEntity, SelectEntity):
    """Normal = solar charging disabled (max speed).

    Solar = Green mode with 100% green share: only charges on solar surplus,
    no 1.4 kW minimum from the grid.

    Comfort = Comfort mode with the comfort level at its minimum (6 A per phase):
    always charges at least that (from grid if needed), faster on more solar
    surplus.
    """

    _attr_icon = "mdi:solar-power-variant"
    _attr_options = CHARGING_MODES

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charging_mode")

    @property
    def current_option(self) -> str | None:
        mode = self.prop(PROP_SOLAR_MODE)
        if mode is None:
            return None
        mode = int(mode)
        if mode == SOLAR_MODE_DISABLED:
            return MODE_NORMAL
        if mode == SOLAR_MODE_COMFORT:
            return MODE_COMFORT
        share = self.prop(PROP_SOLAR_GREEN_SHARE)
        if mode == SOLAR_MODE_GREEN and share is not None and int(share) >= 100:
            return MODE_SOLAR
        # A green share below 100% was set elsewhere (e.g. the app).
        return None

    def _phases(self) -> int:
        """Phases of the socket; 1 if unknown (the lowest level, never too much)."""
        try:
            return max(1, int(self.prop(PROP_MAX_PHASES)))
        except (TypeError, ValueError):
            return 1

    async def async_select_option(self, option: str) -> None:
        try:
            if option == MODE_SOLAR:
                await self.coordinator.client.set_solar_only()
            elif option == MODE_COMFORT:
                await self.coordinator.client.set_comfort(self._phases())
            else:
                await self.coordinator.client.set_normal()
        except AlfenError as err:
            raise HomeAssistantError(f"Laadmodus wijzigen mislukt: {err}") from err
        await self.coordinator.async_request_refresh()
