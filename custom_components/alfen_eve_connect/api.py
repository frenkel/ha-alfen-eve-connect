"""Local HTTPS client for Alfen Eve chargers."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp

from .const import (
    API_INFO,
    API_LOGIN,
    API_LOGOUT,
    API_PROFILES_ADD,
    API_PROFILES_CLEAR,
    API_PROFILES_ID_LIST,
    API_PROP,
    LOGIN_VALID_SECONDS,
    PAUSE_PROFILE_REQUEST,
    PROP_SOLAR_COMFORT_LEVEL,
    PROP_SOLAR_GREEN_SHARE,
    PROP_SOLAR_MODE,
    PROP_SOLAR_OVERRIDE_SOCKET1,
    SOLAR_MODE_COMFORT,
    SOLAR_MODE_DISABLED,
    SOLAR_MODE_GREEN,
    USER_BOOST_PROFILE_ID,
    USER_PAUSE_PROFILE_ID,
    comfort_level_min,
    to_unsigned,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)


class AlfenError(Exception):
    """Generic error talking to the charger."""


class AlfenAuthError(AlfenError):
    """Login was rejected."""


def normalize_id(prop_id: str) -> str:
    """Normalise '2129_00' / '2129_0' to '2129_0' (subindex is hex)."""
    try:
        index, sub = prop_id.split("_", 1)
        return f"{index.upper()}_{int(sub, 16):X}"
    except ValueError:
        return prop_id


class AlfenClient:
    """Minimal client for the charger's local API (the one the Alfen apps use)."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._base = f"https://{host}"
        self._username = username
        self._password = password
        self._last_login = 0.0
        self._lock = asyncio.Lock()

    # -- low level ---------------------------------------------------------
    async def _raw(
        self, method: str, path: str, json: Any = None
    ) -> tuple[int, Any]:
        try:
            async with self._session.request(
                method,
                self._base + path,
                json=json,
                ssl=False,
                timeout=REQUEST_TIMEOUT,
                headers={"Content-Type": "application/json"},
            ) as resp:
                text = await resp.text()
                data: Any = None
                if text:
                    try:
                        data = await resp.json(content_type=None)
                    except ValueError:
                        data = text
                return resp.status, data
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise AlfenError(f"Cannot reach charger: {err}") from err

    async def _login(self) -> None:
        status, data = await self._raw(
            "POST",
            API_LOGIN,
            {"username": self._username, "password": self._password},
        )
        if status in (401, 403):
            raise AlfenAuthError("Invalid username or password")
        if status >= 400:
            raise AlfenError(f"Login failed ({status}): {data}")
        self._last_login = time.monotonic()

    async def _request(self, method: str, path: str, json: Any = None) -> Any:
        """Do a request, logging in first or again when needed."""
        async with self._lock:
            if time.monotonic() - self._last_login > LOGIN_VALID_SECONDS:
                await self._login()
            status, data = await self._raw(method, path, json)
            if status == 401:
                await self._login()
                status, data = await self._raw(method, path, json)
            if status >= 400:
                raise AlfenError(f"{method} {path} failed ({status}): {data}")
            return data

    # -- public API ----------------------------------------------------------
    async def login(self) -> None:
        async with self._lock:
            await self._login()

    async def logout(self) -> None:
        async with self._lock:
            try:
                await self._raw(
                    "POST",
                    API_LOGOUT,
                    {"username": self._username, "password": self._password},
                )
            except AlfenError:
                pass
            self._last_login = 0.0

    async def get_info(self) -> dict[str, Any]:
        status, data = await self._raw("GET", API_INFO)
        if status >= 400 or not isinstance(data, dict):
            raise AlfenError(f"Unexpected /api/info response ({status})")
        return data

    async def get_properties(self, ids: list[str]) -> dict[str, Any]:
        """Read properties; returns {normalised_id: value}."""
        result: dict[str, Any] = {}
        # The charger limits how many ids fit in one request.
        for start in range(0, len(ids), 32):
            chunk = ids[start : start + 32]
            data = await self._request("GET", f"{API_PROP}?ids={','.join(chunk)}")
            props = data.get("properties", []) if isinstance(data, dict) else []
            for prop in props:
                if "id" in prop:
                    result[normalize_id(str(prop["id"]))] = prop.get("value")
        return result

    async def set_properties(self, values: dict[str, Any]) -> None:
        body = {pid: {"id": pid, "value": value} for pid, value in values.items()}
        await self._request("POST", API_PROP, body)

    async def get_active_profile_ids(self) -> set[int]:
        """Return active charging profile ids (as uint32)."""
        data = await self._request("GET", API_PROFILES_ID_LIST)
        ids = _find_key(data, "ChargingProfileIDs") or []
        return {to_unsigned(int(i)) for i in ids}

    async def clear_profile(self, profile_id: int) -> None:
        """Remove a charging profile; a 400 means it was not present."""
        async with self._lock:
            if time.monotonic() - self._last_login > LOGIN_VALID_SECONDS:
                await self._login()
            status, data = await self._raw(
                "POST", f"{API_PROFILES_CLEAR}{profile_id}"
            )
            if status == 401:
                await self._login()
                status, data = await self._raw(
                    "POST", f"{API_PROFILES_CLEAR}{profile_id}"
                )
        if status > 400:
            raise AlfenError(f"Clearing profile {profile_id} failed ({status}): {data}")

    async def add_profile(self, profile: dict[str, Any]) -> None:
        await self._request("POST", API_PROFILES_ADD, profile)

    # -- high level actions (same sequence as the Eve Connect app) -----------
    async def pause_charging(self) -> None:
        await self.set_properties({PROP_SOLAR_OVERRIDE_SOCKET1: 0})
        await self.clear_profile(USER_BOOST_PROFILE_ID)
        await self.add_profile(PAUSE_PROFILE_REQUEST)

    async def resume_charging(self) -> None:
        await self.set_properties({PROP_SOLAR_OVERRIDE_SOCKET1: 0})
        await self.clear_profile(USER_BOOST_PROFILE_ID)
        await self.clear_profile(USER_PAUSE_PROFILE_ID)

    async def set_solar_only(self) -> None:
        """Green mode with 100% green share: charge only on solar surplus."""
        await self.set_properties(
            {
                PROP_SOLAR_MODE: SOLAR_MODE_GREEN,
                PROP_SOLAR_GREEN_SHARE: 100,
                PROP_SOLAR_OVERRIDE_SOCKET1: 0,
            }
        )

    async def set_comfort(self, phases: int) -> None:
        """Comfort mode at the lowest level (6 A per phase), faster on solar surplus."""
        await self.set_properties(
            {
                PROP_SOLAR_MODE: SOLAR_MODE_COMFORT,
                PROP_SOLAR_COMFORT_LEVEL: comfort_level_min(phases),
                PROP_SOLAR_OVERRIDE_SOCKET1: 0,
            }
        )

    async def set_normal(self) -> None:
        """Solar charging off: charge at the configured maximum current."""
        await self.set_properties(
            {PROP_SOLAR_MODE: SOLAR_MODE_DISABLED, PROP_SOLAR_OVERRIDE_SOCKET1: 0}
        )


def _find_key(data: Any, key: str) -> Any:
    """Find a key anywhere in a nested JSON response."""
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for value in data.values():
            found = _find_key(value, key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for value in data:
            found = _find_key(value, key)
            if found is not None:
                return found
    return None
