"""Data update coordinator for Alfen Eve Connect."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AlfenAuthError, AlfenClient, AlfenError
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    POLLED_PROPERTIES,
    USER_PAUSE_PROFILE_ID,
    to_unsigned,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class AlfenData:
    """Snapshot of the charger state."""

    properties: dict[str, Any] = field(default_factory=dict)
    paused: bool | None = None


class AlfenCoordinator(DataUpdateCoordinator[AlfenData]):
    """Polls the charger."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: AlfenClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> AlfenData:
        try:
            props = await self.client.get_properties(POLLED_PROPERTIES)
        except AlfenAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except AlfenError as err:
            raise UpdateFailed(str(err)) from err

        paused: bool | None
        try:
            active = await self.client.get_active_profile_ids()
            paused = to_unsigned(USER_PAUSE_PROFILE_ID) in active
        except AlfenError as err:
            _LOGGER.debug("Could not read charging profiles: %s", err)
            paused = self.data.paused if self.data else None

        return AlfenData(properties=props, paused=paused)
