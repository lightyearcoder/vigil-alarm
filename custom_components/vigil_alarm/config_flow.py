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
    CONF_HEARTBEAT_INTERVAL,
    CONF_HEARTBEAT_URL,
    BACKUP_VERSIONS_RANGE,
    CONF_BACKUP_VERSIONS,
    DEFAULT_BACKUP_VERSIONS,
    CONF_LOG_RETENTION_DAYS,
    DEFAULT_HEARTBEAT_INTERVAL,
    HEARTBEAT_INTERVAL_RANGE,
    CONF_SELFTEST_AUTO,
    CONF_SELFTEST_FROM,
    CONF_SELFTEST_INTERVAL,
    CONF_SELFTEST_SECONDS,
    CONF_SELFTEST_TO,
    DEFAULT_SELFTEST,
    SELFTEST_RANGES,
    DEFAULT_LOG_RETENTION_DAYS,
    LOG_RETENTION_CEILING,
    LOG_RETENTION_FLOOR,
    CONF_MIN_CODE_LENGTH,
    CONF_SCREEN_OFF_ON_ALARM,
    CONF_SCREEN_OFF_SECONDS,
    DEFAULT_SCREEN_OFF_ON_ALARM,
    DEFAULT_SCREEN_OFF_SECONDS,
    SCREEN_OFF_RANGE,
    CONF_STARTUP_WAIT,
    DEFAULT_STARTUP_WAIT,
    STARTUP_WAIT_RANGE,
    LOCK_DEFAULTS,
    LOCK_TRIES_RANGE,
    LOCK_WAIT_RANGE,
    MIN_CODE_LENGTH_CEILING,
    MIN_CODE_LENGTH_FLOOR,
    CONF_EXIT_DELAY,
    CONF_MODES,
    CONF_TRIGGER_TIME,
    CONF_ABORT_SECONDS,
    DEFAULT_ABORT_SECONDS,
    ABORT_SECONDS_RANGE,
    CONF_CHIME_ENTITY,
    CONF_CHIME_SECONDS,
    DEFAULT_CHIME_SECONDS,
    CHIME_SECONDS_RANGE,
    CHIME_DOMAINS,
    DEFAULT_BATTERY_THRESHOLD,
    DEFAULT_EXIT_DELAY,
    DOMAIN,
    MODES,
    DEFAULT_MODES,
)
from .editing import CONF_NAME, _TrialEntry
from .manager import build_config
from .heartbeat import valid_url
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


def _heartbeat_ok(user_input: dict[str, Any]) -> bool:
    url = str(user_input.get(CONF_HEARTBEAT_URL) or "").strip()
    if url:
        user_input[CONF_HEARTBEAT_URL] = url
    else:
        user_input.pop(CONF_HEARTBEAT_URL, None)
    return not url or valid_url(url)


def _entry_schema(d: dict[str, Any]) -> vol.Schema:
    fields: dict[Any, Any] = {
        vol.Required(CONF_MODES, default=d.get(CONF_MODES, list(DEFAULT_MODES))): _select(
            list(MODES), "mode", multiple=True
        ),
    }
    for mode in MODES:
        key = CONF_EXIT_DELAY.format(mode=mode)
        fields[vol.Required(key, default=d.get(key, DEFAULT_EXIT_DELAY[mode]))] = _seconds()
    fields[vol.Required(CONF_DEFAULT_ENTRY_DELAY, default=d.get(CONF_DEFAULT_ENTRY_DELAY, 30))] = _seconds()
    fields[vol.Required(CONF_TRIGGER_TIME, default=d.get(CONF_TRIGGER_TIME, 0))] = _seconds(86400)
    fields[vol.Required(CONF_ABORT_SECONDS, default=d.get(CONF_ABORT_SECONDS, DEFAULT_ABORT_SECONDS))] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=ABORT_SECONDS_RANGE[0], max=ABORT_SECONDS_RANGE[1], step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX)
    )
    fields[vol.Optional(CONF_CHIME_ENTITY, description={"suggested_value": d.get(CONF_CHIME_ENTITY)})] = selector.EntitySelector(
        selector.EntitySelectorConfig(domain=list(CHIME_DOMAINS))
    )
    fields[vol.Required(CONF_CHIME_SECONDS, default=d.get(CONF_CHIME_SECONDS, DEFAULT_CHIME_SECONDS))] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=CHIME_SECONDS_RANGE[0], max=CHIME_SECONDS_RANGE[1], step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX)
    )
    fields[vol.Required(CONF_BATTERY_THRESHOLD, default=d.get(CONF_BATTERY_THRESHOLD, DEFAULT_BATTERY_THRESHOLD))] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.BOX)
    )
    fields[vol.Required(CONF_STARTUP_WAIT, default=d.get(CONF_STARTUP_WAIT, DEFAULT_STARTUP_WAIT))] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=STARTUP_WAIT_RANGE[0], max=STARTUP_WAIT_RANGE[1], step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX
        )
    )
    fields[vol.Required(CONF_CODE_ARM_REQUIRED, default=d.get(CONF_CODE_ARM_REQUIRED, True))] = bool
    fields[vol.Required(CONF_MIN_CODE_LENGTH, default=d.get(CONF_MIN_CODE_LENGTH, MIN_CODE_LENGTH_FLOOR))] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=MIN_CODE_LENGTH_FLOOR, max=MIN_CODE_LENGTH_CEILING, step=1, mode=selector.NumberSelectorMode.BOX
        )
    )
    fields[vol.Required(CONF_SCREEN_OFF_SECONDS, default=d.get(CONF_SCREEN_OFF_SECONDS, DEFAULT_SCREEN_OFF_SECONDS))] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=SCREEN_OFF_RANGE[0], max=SCREEN_OFF_RANGE[1], step=1, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX
        )
    )
    fields[vol.Required(CONF_SCREEN_OFF_ON_ALARM, default=d.get(CONF_SCREEN_OFF_ON_ALARM, DEFAULT_SCREEN_OFF_ON_ALARM))] = bool
    for key, default in LOCK_DEFAULTS.items():
        low, high = LOCK_WAIT_RANGE if "wait" in key else LOCK_TRIES_RANGE
        fields[vol.Required(key, default=d.get(key, default))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=low, max=high, step=1, mode=selector.NumberSelectorMode.BOX)
        )
    fields[vol.Required(CONF_LOG_RETENTION_DAYS, default=d.get(CONF_LOG_RETENTION_DAYS, DEFAULT_LOG_RETENTION_DAYS))] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=LOG_RETENTION_FLOOR, max=LOG_RETENTION_CEILING, step=1, unit_of_measurement="d", mode=selector.NumberSelectorMode.BOX
        )
    )
    fields[vol.Required(CONF_BACKUP_VERSIONS, default=d.get(CONF_BACKUP_VERSIONS, DEFAULT_BACKUP_VERSIONS))] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=BACKUP_VERSIONS_RANGE[0], max=BACKUP_VERSIONS_RANGE[1], step=1, mode=selector.NumberSelectorMode.BOX
        )
    )
    for key in (CONF_SELFTEST_INTERVAL, CONF_SELFTEST_SECONDS):
        low, high = SELFTEST_RANGES[key]
        fields[vol.Required(key, default=d.get(key, DEFAULT_SELFTEST[key]))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=low, max=high, step=1, mode=selector.NumberSelectorMode.BOX)
        )
    fields[vol.Required(CONF_SELFTEST_AUTO, default=d.get(CONF_SELFTEST_AUTO, DEFAULT_SELFTEST[CONF_SELFTEST_AUTO]))] = bool
    for key in (CONF_SELFTEST_FROM, CONF_SELFTEST_TO):
        low, high = SELFTEST_RANGES[key]
        fields[vol.Required(key, default=d.get(key, DEFAULT_SELFTEST[key]))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=low, max=high, step=1, mode=selector.NumberSelectorMode.BOX)
        )
    fields[vol.Optional(CONF_HEARTBEAT_URL, description={"suggested_value": d.get(CONF_HEARTBEAT_URL, "")})] = selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
    )
    fields[vol.Required(CONF_HEARTBEAT_INTERVAL, default=d.get(CONF_HEARTBEAT_INTERVAL, DEFAULT_HEARTBEAT_INTERVAL))] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=HEARTBEAT_INTERVAL_RANGE[0], max=HEARTBEAT_INTERVAL_RANGE[1], step=1, unit_of_measurement="min", mode=selector.NumberSelectorMode.BOX
        )
    )
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
            elif not _heartbeat_ok(user_input):
                errors[CONF_HEARTBEAT_URL] = "heartbeat_url_invalid"
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
            elif not _heartbeat_ok(user_input):
                errors[CONF_HEARTBEAT_URL] = "heartbeat_url_invalid"
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
