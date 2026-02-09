"""Config flow for Presence Switch integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_AUTO_OFF_ON_DEPARTURE,
    CONF_DELAY_MINUTES,
    CONF_EXEMPTION_ENTITIES,
    CONF_PRESENCE_ENTITY,
    CONF_RESTORE_STATE,
    DEFAULT_AUTO_OFF_ON_DEPARTURE,
    DEFAULT_DELAY_MINUTES,
    DEFAULT_RESTORE_STATE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class PresenceSwitchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Presence Switch."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]
            
            await self.async_set_unique_id(name)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=name,
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Required(CONF_PRESENCE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["device_tracker", "person", "binary_sensor"],
                    )
                ),
                vol.Optional(
                    CONF_DELAY_MINUTES, default=DEFAULT_DELAY_MINUTES
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=60,
                        step=1,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_EXEMPTION_ENTITIES, default=[]
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                    )
                ),
                vol.Optional(
                    CONF_RESTORE_STATE, default=DEFAULT_RESTORE_STATE
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_AUTO_OFF_ON_DEPARTURE, default=DEFAULT_AUTO_OFF_ON_DEPARTURE
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> PresenceSwitchOptionsFlow:
        """Get the options flow for this handler."""
        return PresenceSwitchOptionsFlow(config_entry)


class PresenceSwitchOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Presence Switch."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_DELAY_MINUTES,
                    default=self.config_entry.data.get(
                        CONF_DELAY_MINUTES, DEFAULT_DELAY_MINUTES
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=60,
                        step=1,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_EXEMPTION_ENTITIES,
                    default=self.config_entry.data.get(CONF_EXEMPTION_ENTITIES, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                    )
                ),
                vol.Optional(
                    CONF_RESTORE_STATE,
                    default=self.config_entry.data.get(
                        CONF_RESTORE_STATE, DEFAULT_RESTORE_STATE
                    ),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_AUTO_OFF_ON_DEPARTURE,
                    default=self.config_entry.data.get(
                        CONF_AUTO_OFF_ON_DEPARTURE, DEFAULT_AUTO_OFF_ON_DEPARTURE
                    ),
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
