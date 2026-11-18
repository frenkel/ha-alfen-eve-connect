"""Constants for the Alfen Eve Connect integration.

Property IDs, profile IDs and payloads were taken from the official Alfen
apps (MyEve 2.3.1 and Eve Connect 1.5.4), which talk to the charger over the
local network through its HTTPS API.
"""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "alfen_eve_connect"

DEFAULT_USERNAME = "admin"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

# The charger drops a login session after 5 minutes (Eve Connect uses 300000 ms).
LOGIN_VALID_SECONDS = 240

# --- API endpoints -----------------------------------------------------------
API_LOGIN = "/api/login"
API_LOGOUT = "/api/logout"
API_INFO = "/api/info"
API_PROP = "/api/prop"
API_PROFILES_ADD = "/api/chargingprofiles?add"
API_PROFILES_CLEAR = "/api/chargingprofiles?clear="
API_PROFILES_ID_LIST = "/api/chargingprofiles?id_list"

# --- Property IDs (format used on the wire: "XXXX_Y", subindex in hex) --------
PROP_MAX_CURRENT = "2129_0"  # Socket 1 - Max current (A)
PROP_STATION_MAX_CURRENT = "2062_0"  # Station maximum current (A)
PROP_MAIN_STATE = "2501_1"  # Socket 1 - Mainstate
PROP_POWER = "2221_16"  # Socket 1 - Power Real Sum
PROP_ENERGY = "2221_22"  # Socket 1 - Energy Delivered Sum
PROP_SOLAR_MODE = "3280_1"  # Solar - Operation Mode (0 disabled, 1 comfort, 2 green)
PROP_SOLAR_GREEN_SHARE = "3280_2"  # Solar - Green Share (%)
PROP_SOLAR_COMFORT_LEVEL = "3280_3"  # Solar - Comfort Level (W)
PROP_SOLAR_OVERRIDE_SOCKET1 = "3280_4"  # Solar - Override Socket 1 (boost)

POLLED_PROPERTIES = [
    PROP_MAX_CURRENT,
    PROP_STATION_MAX_CURRENT,
    PROP_MAIN_STATE,
    PROP_POWER,
    PROP_ENERGY,
    PROP_SOLAR_MODE,
    PROP_SOLAR_GREEN_SHARE,
    PROP_SOLAR_COMFORT_LEVEL,
    PROP_SOLAR_OVERRIDE_SOCKET1,
]

SOLAR_MODE_DISABLED = 0
SOLAR_MODE_COMFORT = 1
SOLAR_MODE_GREEN = 2

# --- Charging profiles (identical to Eve Connect) -----------------------------
# Profile IDs are uint32 on the charger; the apps use the signed form in the
# clear URL, so both forms are accepted when reading the active list.
USER_PAUSE_PROFILE_ID = -12122008  # == 4282845288 unsigned
USER_BOOST_PROFILE_ID = -19571004  # == 4275396292 unsigned


def to_unsigned(profile_id: int) -> int:
    """Return the uint32 form of a (possibly signed) profile id."""
    return profile_id & 0xFFFFFFFF


# A relative profile with limit 0 A on all connectors: the charger suspends
# charging until the profile is cleared again.
PAUSE_PROFILE_REQUEST = {
    "connectorId": 0,
    "csChargingProfiles": {
        "chargingProfileId": to_unsigned(USER_PAUSE_PROFILE_ID),
        "chargingProfileKind": "Relative",
        "chargingProfilePurpose": "ChargingStationExternalConstraints",
        "stackLevel": 1000,
        "useLocalTime": True,
        "useRandomisedDelay": False,
        "chargingSchedule": {
            "chargingRateUnit": "A",
            "chargingSchedulePeriod": [{"startPeriod": 0, "limit": 0}],
        },
    },
}

# --- Charging mode select ------------------------------------------------------
MODE_NORMAL = "normal"
MODE_SOLAR = "solar"
CHARGING_MODES = [MODE_NORMAL, MODE_SOLAR]
