from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import repo
from .const import DOMAIN
from .coordinator import ResticCoordinator


class ResticEntity(CoordinatorEntity[ResticCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: ResticCoordinator, repo_name: str, key: str) -> None:
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id
        self.repo_name = repo_name
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry_id}_{repo_name}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{repo_name}")},
            name=repo_name,
            manufacturer="restic",
            model="Repository",
        )

    @property
    def repo_status(self) -> repo.RepoStatus | None:
        return self.coordinator.data.get(self.repo_name)
