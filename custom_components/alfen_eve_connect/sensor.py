"""Sensors for Alfen Eve Connect."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AlfenConfigEntry
from .const import (
    MAIN_STATE_STATUS,
    PROP_ENERGY,
    PROP_MAIN_STATE,
    PROP_MAX_CURRENT,
    PROP_POWER,
    PROP_SOLAR_COMFORT_LEVEL,
    PROP_SOLAR_GREEN_SHARE,
)
from .entity import AlfenEntity


def _status(value: Any) -> str | None:
    try:
        return MAIN_STATE_STATUS.get(int(value))
    except (TypeError, ValueError):
        return None


def _round(value: Any, digits: int = 1) -> float | None:
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, kw_only=True)
class AlfenSensorDescription(SensorEntityDescription):
    prop_id: str
    convert: Callable[[Any], Any] = lambda v: v


SENSORS: tuple[AlfenSensorDescription, ...] = (
    AlfenSensorDescription(
        key="power",
        prop_id=PROP_POWER,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        convert=lambda v: _round(v, 0),
    ),
    AlfenSensorDescription(
        key="energy",
        prop_id=PROP_ENERGY,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        convert=lambda v: _round(v, 0),
    ),
    AlfenSensorDescription(
        key="status",
        prop_id=PROP_MAIN_STATE,
        device_class=SensorDeviceClass.ENUM,
        options=list(MAIN_STATE_STATUS.values()),
        convert=_status,
    ),
    AlfenSensorDescription(
        key="max_current",
        prop_id=PROP_MAX_CURRENT,
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AlfenSensorDescription(
        key="green_share",
        prop_id=PROP_SOLAR_GREEN_SHARE,
        native_unit_of_measurement="%",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AlfenSensorDescription(
        key="comfort_level",
        prop_id=PROP_SOLAR_COMFORT_LEVEL,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        convert=lambda v: _round(v, 0),
    ),
    AlfenSensorDescription(
        key="main_state",
        prop_id=PROP_MAIN_STATE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlfenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(AlfenSensor(coordinator, desc) for desc in SENSORS)


class AlfenSensor(AlfenEntity, SensorEntity):
    entity_description: AlfenSensorDescription

    def __init__(self, coordinator, description: AlfenSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        value = self.prop(self.entity_description.prop_id)
        return None if value is None else self.entity_description.convert(value)
