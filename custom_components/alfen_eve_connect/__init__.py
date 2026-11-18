"""Alfen Eve Connect: control an Alfen Eve charger over the local network."""

from __future__ import annotations

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import AlfenClient
from .coordinator import AlfenCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]

type AlfenConfigEntry = ConfigEntry[AlfenCoordinator]


def create_client(hass: HomeAssistant, host: str, username: str, password: str) -> AlfenClient:
    """Create a client with its own cookie jar (the charger is addressed by IP)."""
    session = async_create_clientsession(
        hass, verify_ssl=False, cookie_jar=aiohttp.CookieJar(unsafe=True)
    )
    return AlfenClient(session, host, username, password)


async def async_setup_entry(hass: HomeAssistant, entry: AlfenConfigEntry) -> bool:
    client = create_client(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = AlfenCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AlfenConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        # Free the single login slot so the Alfen apps can connect again.
        await entry.runtime_data.client.logout()
    return unloaded
