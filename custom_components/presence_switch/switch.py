"""Switch platform for Presence Switch integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Literal

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import (
    Event,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DELAY_REMAINING,
    ATTR_EXEMPTIONS_ACTIVE,
    ATTR_NEXT_AUTO_OFF,
    ATTR_PRESENCE_STATE,
    CONF_AUTO_OFF_ON_DEPARTURE,
    CONF_DELAY_MINUTES,
    CONF_EXEMPTION_ENTITIES,
    CONF_PRESENCE_ENTITY,
    CONF_RESTORE_STATE,
    DEFAULT_AUTO_OFF_ON_DEPARTURE,
    DEFAULT_DELAY_MINUTES,
    DEFAULT_RESTORE_STATE,
    DOMAIN,
    SERVICE_FORCE_DISABLE,
    SERVICE_FORCE_ENABLE,
    SERVICE_RESET_AUTO,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Presence Switch platform."""
    data = config_entry.data
    
    switch = PresenceSwitch(
        hass,
        config_entry.entry_id,
        data[CONF_NAME],
        data[CONF_PRESENCE_ENTITY],
        data.get(CONF_DELAY_MINUTES, DEFAULT_DELAY_MINUTES),
        data.get(CONF_EXEMPTION_ENTITIES, []),
        data.get(CONF_RESTORE_STATE, DEFAULT_RESTORE_STATE),
        data.get(CONF_AUTO_OFF_ON_DEPARTURE, DEFAULT_AUTO_OFF_ON_DEPARTURE),
    )
    
    async_add_entities([switch], update_before_add=True)


class PresenceSwitch(SwitchEntity, RestoreEntity):
    """Representation of a Presence Switch."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        name: str,
        presence_entity: str,
        delay_minutes: int,
        exemption_entities: list[str],
        restore_state: bool,
        auto_off_on_departure: bool,
    ) -> None:
        """Initialize the switch."""
        self.hass = hass
        self._entry_id = entry_id
        self._attr_unique_id = entry_id
        self._attr_name = name
        
        self._presence_entity = presence_entity
        self._delay_minutes = delay_minutes
        self._exemption_entities = exemption_entities or []
        self._restore_state = restore_state
        self._auto_off_on_departure = auto_off_on_departure
        
        self._is_on = False
        self._presence_state: str | None = None
        self._auto_off_time: datetime | None = None
        self._cancel_auto_off: asyncio.TimerHandle | None = None
        self._exemptions_active = False
        
        self._attr_extra_state_attributes: dict[str, Any] = {}

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._is_on

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._presence_state is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {
            ATTR_PRESENCE_STATE: self._presence_state,
            ATTR_EXEMPTIONS_ACTIVE: self._exemptions_active,
        }
        
        if self._auto_off_time and self._is_on:
            remaining = (self._auto_off_time - dt_util.utcnow()).total_seconds()
            attrs[ATTR_DELAY_REMAINING] = max(0, int(remaining / 60))
            attrs[ATTR_NEXT_AUTO_OFF] = self._auto_off_time.isoformat()
        else:
            attrs[ATTR_DELAY_REMAINING] = None
            attrs[ATTR_NEXT_AUTO_OFF] = None
            
        return attrs

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self._is_on:
            if self._presence_state == STATE_NOT_HOME:
                return "mdi:account-clock"
            return "mdi:account-check"
        return "mdi:account-off"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state if enabled
        if self._restore_state:
            last_state = await self.async_get_last_state()
            if last_state and last_state.state == STATE_ON:
                self._is_on = True
                _LOGGER.debug("Restored state to ON for %s", self._attr_name)
        
        # Get initial presence state
        presence_state = self.hass.states.get(self._presence_entity)
        if presence_state:
            self._presence_state = presence_state.state
            self._update_exemptions()
        
        # Set up listeners
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._presence_entity] + self._exemption_entities,
                self._async_presence_changed,
            )
        )
        
        # Update attributes
        self._update_attributes()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._is_on = True
        self._cancel_pending_auto_off()
        self._update_attributes()
        self.async_write_ha_state()
        _LOGGER.debug("Switch %s turned ON manually", self._attr_name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._is_on = False
        self._cancel_pending_auto_off()
        self._auto_off_time = None
        self._update_attributes()
        self.async_write_ha_state()
        _LOGGER.debug("Switch %s turned OFF manually", self._attr_name)

    @callback
    def _async_presence_changed(self, event: Event) -> None:
        """Handle presence state changes."""
        entity_id = event.data["entity_id"]
        new_state: State | None = event.data.get("new_state")
        
        if new_state is None:
            return
        
        if entity_id == self._presence_entity:
            old_presence = self._presence_state
            self._presence_state = new_state.state
            
            _LOGGER.debug(
                "Presence changed for %s: %s -> %s",
                self._attr_name,
                old_presence,
                self._presence_state,
            )
            
            self._handle_presence_change()
        
        elif entity_id in self._exemption_entities:
            self._update_exemptions()
            self._handle_presence_change()

    def _handle_presence_change(self) -> None:
        """Handle logic when presence changes."""
        if not self._is_on:
            # Switch is off, nothing to do
            self._update_attributes()
            self.async_write_ha_state()
            return
        
        if self._exemptions_active:
            # An exemption is active, cancel any pending auto-off
            _LOGGER.debug(
                "Exemption active for %s, canceling auto-off",
                self._attr_name,
            )
            self._cancel_pending_auto_off()
            self._auto_off_time = None
            self._update_attributes()
            self.async_write_ha_state()
            return
        
        if self._presence_state == STATE_NOT_HOME and self._auto_off_on_departure:
            # Schedule auto-off if not already scheduled
            if self._cancel_auto_off is None:
                self._schedule_auto_off()
        elif self._presence_state == STATE_HOME:
            # Cancel auto-off when someone returns
            self._cancel_pending_auto_off()
            self._auto_off_time = None
        
        self._update_attributes()
        self.async_write_ha_state()

    def _update_exemptions(self) -> None:
        """Check if any exemption entities are active."""
        if not self._exemption_entities:
            self._exemptions_active = False
            return
        
        for entity_id in self._exemption_entities:
            state = self.hass.states.get(entity_id)
            if state and state.state in (STATE_ON, "true", "yes", "active", STATE_HOME):
                self._exemptions_active = True
                return
        
        self._exemptions_active = False

    def _schedule_auto_off(self) -> None:
        """Schedule the automatic turn-off."""
        if self._delay_minutes <= 0:
            # No delay, turn off immediately
            self._is_on = False
            self._auto_off_time = None
            _LOGGER.info(
                "Auto-off triggered immediately for %s (no delay)",
                self._attr_name,
            )
            return
        
        self._auto_off_time = dt_util.utcnow() + timedelta(minutes=self._delay_minutes)
        
        _LOGGER.info(
            "Scheduling auto-off for %s in %d minutes (at %s)",
            self._attr_name,
            self._delay_minutes,
            self._auto_off_time,
        )
        
        self._cancel_auto_off = self.hass.loop.call_later(
            self._delay_minutes * 60,
            self._auto_off_callback,
        )

    @callback
    def _auto_off_callback(self) -> None:
        """Callback to turn off the switch."""
        self._cancel_auto_off = None
        
        # Double-check conditions before turning off
        self._update_exemptions()
        
        if self._exemptions_active:
            _LOGGER.debug(
                "Auto-off canceled for %s due to active exemption",
                self._attr_name,
            )
            return
        
        if self._presence_state == STATE_HOME:
            _LOGGER.debug(
                "Auto-off canceled for %s - someone returned home",
                self._attr_name,
            )
            self._auto_off_time = None
            self._update_attributes()
            self.async_write_ha_state()
            return
        
        self._is_on = False
        self._auto_off_time = None
        _LOGGER.info("Auto-off triggered for %s", self._attr_name)
        
        self._update_attributes()
        self.async_write_ha_state()

    def _cancel_pending_auto_off(self) -> None:
        """Cancel any pending auto-off timer."""
        if self._cancel_auto_off is not None:
            self._cancel_auto_off.cancel()
            self._cancel_auto_off = None
            _LOGGER.debug("Canceled pending auto-off for %s", self._attr_name)

    def _update_attributes(self) -> None:
        """Update the extra state attributes."""
        self._attr_extra_state_attributes = self.extra_state_attributes

    async def async_force_enable(self) -> None:
        """Force enable the switch (ignore presence)."""
        await self.async_turn_on()
        _LOGGER.info("Force enabled %s", self._attr_name)

    async def async_force_disable(self) -> None:
        """Force disable the switch (ignore presence)."""
        await self.async_turn_off()
        _LOGGER.info("Force disabled %s", self._attr_name)

    async def async_reset_auto(self) -> None:
        """Reset auto-off timer."""
        if self._is_on and self._presence_state == STATE_NOT_HOME:
            self._cancel_pending_auto_off()
            self._schedule_auto_off()
            self._update_attributes()
            self.async_write_ha_state()
            _LOGGER.info("Reset auto-off timer for %s", self._attr_name)
