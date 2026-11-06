from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import repo
from .const import DOMAIN
from .coordinator import ResticConfigEntry, ResticCoordinator
from .entity import ResticEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ResticConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    known: set[str] = set()

    def _add_new() -> None:
        new = [n for n in coordinator.data if n not in known]
        known.update(new)
        async_add_entities(RepositorySize(coordinator, n) for n in new)

    def _prune() -> None:
        if not coordinator.data:
            return
        registry = dr.async_get(hass)
        prefix = f"{entry.entry_id}_"
        for device in dr.async_entries_for_config_entry(registry, entry.entry_id):
            for domain, identifier in device.identifiers:
                if domain == DOMAIN and identifier.removeprefix(prefix) not in coordinator.data:
                    registry.async_update_device(
                        device.id, remove_config_entry_id=entry.entry_id
                    )
                    known.discard(identifier.removeprefix(prefix))

    def _refresh() -> None:
        _prune()
        _add_new()

    _prune()
    _add_new()

    entry.async_on_unload(coordinator.async_add_listener(_refresh))


class RepositorySize(ResticEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = UnitOfInformation.BYTES
    _attr_suggested_unit_of_measurement = UnitOfInformation.GIGABYTES
    _attr_suggested_display_precision = 1

    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator: ResticCoordinator, repo_name: str) -> None:
        super().__init__(coordinator, repo_name, "size")

    @property
    def native_value(self) -> int | None:
        d = self.repo_status
        if (
            d
            and d.available
            and repo.has_snapshot_on(
                d.last_snapshot, dt_util.now().date(), dt_util.DEFAULT_TIME_ZONE
            )
        ):
            return d.size
        return None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        d = self.repo_status
        if d is None:
            return {}
        return {
            "last_snapshot": d.last_snapshot.isoformat() if d.last_snapshot else None,
            "snapshot_count": d.snapshot_count if d.available else None,
            "error": d.error,
        }
