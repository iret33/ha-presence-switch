"""Constants for the Presence Switch integration."""

DOMAIN = "presence_switch"

# Configuration keys
CONF_PRESENCE_ENTITY = "presence_entity"
CONF_DELAY_MINUTES = "delay_minutes"
CONF_EXEMPTION_ENTITIES = "exemption_entities"
CONF_RESTORE_STATE = "restore_state"
CONF_AUTO_OFF_ON_DEPARTURE = "auto_off_on_departure"

# Defaults
DEFAULT_DELAY_MINUTES = 5
DEFAULT_RESTORE_STATE = True
DEFAULT_AUTO_OFF_ON_DEPARTURE = True

# States
STATE_HOME = "home"
STATE_NOT_HOME = "not_home"

# Services
SERVICE_FORCE_ENABLE = "force_enable"
SERVICE_FORCE_DISABLE = "force_disable"
SERVICE_RESET_AUTO = "reset_auto"

# Attributes
ATTR_PRESENCE_STATE = "presence_state"
ATTR_DELAY_REMAINING = "delay_remaining"
ATTR_EXEMPTIONS_ACTIVE = "exemptions_active"
ATTR_NEXT_AUTO_OFF = "next_auto_off"
