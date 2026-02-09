# Presence Switch for Home Assistant

[![GitHub Release](https://img.shields.io/github/release/iret33/ha-presence-switch.svg)](https://github.com/iret33/ha-presence-switch/releases)
[![License](https://img.shields.io/github/license/iret33/ha-presence-switch.svg)](LICENSE)

A smart switch integration for Home Assistant that automatically turns off when no one is home, with configurable delays and exemptions.

## Features

- **Presence-aware**: Automatically responds to home/away state changes
- **Configurable delay**: Set a custom delay before auto-off triggers
- **Exemptions**: Specify entities that prevent auto-off (guest mode, parties, etc.)
- **State restoration**: Optionally restore previous state on Home Assistant restart
- **Manual override**: Force enable/disable regardless of presence
- **Visual indicators**: Icon changes based on presence state

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the menu (⋮) and select "Custom repositories"
4. Add `https://github.com/iret33/ha-presence-switch` with category "Integration"
5. Click "Download"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/presence_switch/` directory to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

### UI Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Presence Switch"
4. Configure the following options:

| Option | Description | Default |
|--------|-------------|---------|
| Name | Friendly name for the switch | Required |
| Presence Entity | Device tracker or person entity to monitor | Required |
| Delay Minutes | Minutes to wait before auto-off when leaving | 5 |
| Exemption Entities | Entities that prevent auto-off when active | None |
| Restore State | Restore previous state after restart | true |
| Auto-off on Departure | Enable auto-off when leaving home | true |

### Example Use Cases

#### Air Conditioner Control
- Turn off AC 10 minutes after everyone leaves
- Exemption: "Guest Mode" input boolean for when you have visitors

#### Security Lighting
- Turn on lights when home, auto-off when away
- Exemption: "Vacation Mode" for simulated presence

#### Entertainment System
- Auto-off TV/sound system when no one is home
- Exemption: "Party Mode" switch

## Services

The following services are available:

### `switch.turn_on` / `switch.turn_on`
Standard switch services. Turning on manually will cancel any pending auto-off.

### Custom Attributes

The switch exposes these additional attributes:

| Attribute | Description |
|-----------|-------------|
| `presence_state` | Current state of the monitored presence entity |
| `exemptions_active` | Whether any exemption entity is currently active |
| `delay_remaining` | Minutes remaining until auto-off (if scheduled) |
| `next_auto_off` | ISO timestamp of scheduled auto-off |

## Automation Examples

```yaml
# Notify when auto-off is triggered
automation:
  - alias: "Notify when AC auto-off triggered"
    trigger:
      - platform: state
        entity_id: switch.ac_presence_switch
        from: "on"
        to: "off"
    condition:
      - condition: state
        entity_id: device_tracker.sayed_phone
        state: "not_home"
    action:
      - service: notify.mobile_app_phone
        data:
          message: "AC turned off - everyone left home"
```

```yaml
# Enable guest mode when visitors arrive
automation:
  - alias: "Guest mode on with doorbell"
    trigger:
      - platform: state
        entity_id: binary_sensor.doorbell
        to: "on"
    action:
      - service: input_boolean.turn_on
        target:
          entity_id: input_boolean.guest_mode
```

## Troubleshooting

### Switch not turning off
- Check that the presence entity is correctly reporting `not_home`
- Verify no exemption entities are active
- Check Home Assistant logs for errors

### Delay not working
- Ensure delay is set to a value > 0
- Check if the switch was manually turned on (this cancels auto-off)

## Support

- [Open an issue](https://github.com/iret33/ha-presence-switch/issues) for bug reports
- [Start a discussion](https://github.com/iret33/ha-presence-switch/discussions) for questions

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
