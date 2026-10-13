"""Config flow: only the alarm itself. Everything else is edited in the Vigil panel."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_THRESHOLD,
    CONF_CODE_ARM_REQUIRED,
    CONF_DEFAULT_ENTRY_DELAY,
    CONF_EXIT_DELAY,
    CONF_MODES,
    CONF_TRIGGER_TIME,
    DEFAULT_BATTERY_THRESHOLD,
    DEFAULT_EXIT_DELAY,
    DOMAIN,
    MODES,
)
from .editing import CONF_NAME, _TrialEntry
from .manager import build_config
from .items import OPTION_KEY
from .migration import ENTRY_VERSION, default_groups
from .vigil_core import ConfigError


def _select(options: list[str], key: str, *, multiple: bool = False) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=multiple,
            translation_key=key,
            mode=selector.SelectSelectorMode.DROPDOWN if not multiple else selector.SelectSelectorMode.LIST,
        )
    )


def _seconds(maximum: int = 3600) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0, max=maximum, step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX
        )
    )


def _entry_schema(d: dict[str, Any]) -> vol.Schema:
    fields: dict[Any, Any] = {
        vol.Required(CONF_MODES, default=d.get(CONF_MODES, list(MODES))): _select(
            list(MODES), "mode", multiple=True
        ),
    }
    for mode in MODES:
        key = CONF_EXIT_DELAY.format(mode=mode)
        fields[vol.Required(key, default=d.get(key, DEFAULT_EXIT_DELAY[mode]))] = _seconds()
    fields[vol.Required(CONF_DEFAULT_ENTRY_DELAY, default=d.get(CONF_DEFAULT_ENTRY_DELAY, 30))] = _seconds()
    fields[vol.Required(CONF_TRIGGER_TIME, default=d.get(CONF_TRIGGER_TIME, 0))] = _seconds(86400)
    fields[vol.Required(CONF_BATTERY_THRESHOLD, default=d.get(CONF_BATTERY_THRESHOLD, DEFAULT_BATTERY_THRESHOLD))] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.BOX)
    )
    fields[vol.Required(CONF_CODE_ARM_REQUIRED, default=d.get(CONF_CODE_ARM_REQUIRED, True))] = bool
    return vol.Schema(fields)


class VigilConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = ENTRY_VERSION

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input[CONF_MODES]:
                errors["base"] = "no_modes"
            else:
                name = user_input.pop(CONF_NAME)
                return self.async_create_entry(
                    title=name,
                    data=user_input,
                    options={OPTION_KEY: default_groups(self.hass.config.language, list(user_input[CONF_MODES]))},
                )
        schema = _entry_schema(user_input or {}).extend({vol.Required(CONF_NAME, default="Vigil Alarm"): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input[CONF_MODES]:
                errors["base"] = "no_modes"
            else:
                trial = _TrialEntry(entry, user_input)
                try:
                    build_config(trial)  # type: ignore[arg-type]
                except ConfigError as err:
                    errors["base"] = "invalid_config"
                    placeholders = {"error": str(err)}
                else:
                    self.hass.config_entries.async_update_entry(entry, data=user_input)
                    return self.async_abort(reason="reconfigure_successful")
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_entry_schema(user_input or dict(entry.data)),
            errors=errors,
            description_placeholders={"error": placeholders["error"]} if errors.get("base") == "invalid_config" else None,
        )
