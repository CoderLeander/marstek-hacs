# Marstek Battery Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]
[![hacs][hacsbadge]][hacs]
[![Community Forum][forum-shield]][forum]

This is a custom integration for Home Assistant that allows you to monitor Marstek battery systems via UDP communication.

## Features

- Real-time monitoring of battery parameters
- Support for multiple sensor types:
  - Battery Voltage
  - Battery Current
  - Battery Power
  - Battery Temperature
  - Battery State of Charge (SOC)
- Easy configuration through the Home Assistant UI
- Local communication (no cloud required)
- Compatible with HACS (Home Assistant Community Store)

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS → Integrations
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Install" on the Marstek Battery integration
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/marstek` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Marstek Battery" and follow the setup process

## Configuration

1. Go to Settings → Devices & Services → Add Integration
2. Search for "Marstek Battery"
3. Enter your device configuration:
   - **Device IP Address**: The IP address of your Marstek device (e.g., `192.168.1.142`)
   - **BLE MAC Address**: The BLE MAC address of your device (e.g., `009b0805d5ac`)
   - **Remote Port**: Port the device listens on (default: `30000`)
   - **Local Port**: Port to bind locally (default: `30000`)
4. Click Submit and the integration will test the connection
5. Your battery sensors will appear in Home Assistant

## Supported Devices

This integration has been tested with:
- Marstek battery systems with UDP/JSON-RPC communication

## Sensors

The integration creates the following sensors:

| Sensor | Unit | Description |
|--------|------|-------------|
| Battery Voltage | V | Current battery voltage |
| Battery Current | A | Current battery current (positive = charging, negative = discharging) |
| Battery Power | W | Current battery power |
| Battery Temperature | °C | Battery temperature |
| Battery State of Charge | % | Battery charge level |

## Troubleshooting

### Connection Issues

1. **Timeout errors**: Check that your device IP is correct and reachable
2. **Port conflicts**: Ensure port 30000 isn't used by other applications
3. **Network issues**: Verify your Home Assistant can reach the device network

### Sensor Data Issues

1. **Missing sensor values**: The integration will try to find sensor data in the API response automatically
2. **Incorrect values**: Check your device's API documentation for the correct field names

### Debug Logging

Add this to your `configuration.yaml` to enable debug logging:

```yaml
logger:
  logs:
    custom_components.marstek: debug
```

## Development

### API Response Structure

The integration expects JSON-RPC responses from your Marstek device. The sensor extraction logic will automatically search for common field names like:

- Voltage: `voltage`, `volt`, `v`
- Current: `current`, `amp`, `a`  
- Power: `power`, `watt`, `w`
- Temperature: `temperature`, `temp`, `t`
- SOC: `soc`, `state_of_charge`, `battery_level`, `charge`

### Extending the Integration

You can easily add more sensors by:

1. Adding new sensor types to `const.py`
2. Adding the extraction logic in `sensor.py`
3. Adding more API methods to `marstek_client.py`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you have questions or need help:

1. Check the [Issues](https://github.com/yourusername/marstek-hacs/issues) page
2. Create a new issue with:
   - Your Home Assistant version
   - Integration version
   - Device model and firmware
   - Detailed description of the problem
   - Any relevant logs

---

[releases-shield]: https://img.shields.io/github/release/yourusername/marstek-hacs.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/yourusername/marstek-hacs.svg?style=for-the-badge
[commits]: https://github.com/yourusername/marstek-hacs/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license]: https://github.com/yourusername/marstek-hacs/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/yourusername/marstek-hacs.svg?style=for-the-badge
[releases]: https://github.com/yourusername/marstek-hacs/releases