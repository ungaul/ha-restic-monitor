from __future__ import annotations

import os
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from . import repo
from .const import CONF_PATH, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS, DOMAIN


def _interval_selector() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=1,
            max=168,
            step=1,
            unit_of_measurement="h",
            mode=NumberSelectorMode.BOX,
        )
    )


SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PATH): str,
        vol.Required(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_HOURS
        ): _interval_selector(),
    }
)


class ResticConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> ResticOptionsFlow:
        return ResticOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            path = os.path.realpath(user_input[CONF_PATH])
            found = await self.hass.async_add_executor_job(repo.discover, path)
            if not found:
                errors[CONF_PATH] = "no_repository_found"
            else:
                await self.async_set_unique_id(path)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Restic ({path})",
                    data={CONF_PATH: path},
                    options={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])},
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(SCHEMA, user_input),
            errors=errors,
        )


class ResticOptionsFlow(OptionsFlowWithReload):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])}
            )
        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_SCAN_INTERVAL, default=current): _interval_selector()}
            ),
        )
