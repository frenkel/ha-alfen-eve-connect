"""Base entity for Alfen Eve Connect."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AlfenCoordinator


class AlfenEntity(CoordinatorEntity[AlfenCoordinator]):
    """Common device info."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AlfenCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        base = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{base}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, base)},
            manufacturer="Alfen",
            model="Eve",
            name="Alfen Eve",
        )

    def prop(self, prop_id: str):
        return self.coordinator.data.properties.get(prop_id)
