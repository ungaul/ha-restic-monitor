from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import repo
from .const import (
    CONF_PATH,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

type ResticConfigEntry = ConfigEntry[ResticCoordinator]


class ResticCoordinator(DataUpdateCoordinator[dict[str, repo.RepoStatus]]):
    config_entry: ResticConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ResticConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.title}",
            update_interval=timedelta(
                hours=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS)
            ),
        )

    def _collect(self) -> dict[str, repo.RepoStatus]:
        result: dict[str, repo.RepoStatus] = {}
        for name, path in repo.discover(self.config_entry.data[CONF_PATH]).items():
            result[name] = repo.read_metadata(path, repo.compute_size(path))
        return result

    async def _async_update_data(self) -> dict[str, repo.RepoStatus]:
        return await self.hass.async_add_executor_job(self._collect)
