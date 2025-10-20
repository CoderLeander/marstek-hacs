# Marstek Battery Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]
[![hacs][hacsbadge]][hacs]
[![Community Forum][forum-shield]][forum]

This is a custom integration for Home Assistant that allows you to monitor Marstek battery systems via UDP communication. The integration provides comprehensive monitoring of your Marstek battery system with **25+ sensors** covering battery status, power management, network connectivity, and system information.

## ⚠️ Prerequisites - API Access Required

**IMPORTANT**: The API on Marstek batteries is **disabled by default**. You must request API access before this integration will work.

### How to Enable API Access:

1. **Request API access** by contacting Marstek through their contact form: https://eu.marstekenergy.com/nl-be/pages/contact
2. **Mention in your message** that you want to enable the API for Home Assistant integration
3. **Wait for confirmation** from Marstek support
4. **Check your mobile app** - You'll know the API is enabled when you see an "**Advanced**" section appear in your Marstek mobile app
5. **Configure the API** in the Advanced section:
   - Enable/disable the API
   - Set the port (default: 30000)

## Features

- **25+ sensors** monitoring all aspects of your Marstek system
- **Comprehensive coverage**:
  - Battery status (voltage, current, power, temperature, SOC)
  - System mode and power management
  - Energy monitoring (grid, solar, load power)
  - Network connectivity (WiFi and Bluetooth status)
  - Device information and diagnostics
- **Real-time updates** every minute with intelligent rate limiting
- **Easy setup** through Home Assistant UI with automatic device discovery
- **Local communication** (no cloud required, direct UDP to your battery)
- **Retry logic** for reliable connection during setup
- **HACS compatible** for easy installation and updates

## Installation

### Step 1: Install via HACS (Recommended)

1. **Install HACS** if you haven't already: [HACS Installation Guide](https://hacs.xyz/docs/setup/download)
2. **Add this repository to HACS**:
   - Go to HACS → Integrations
   - Click the three dots (⋮) in the top right corner
   - Select "Custom repositories"
   - Add this repository URL and select "Integration" as the category
   - Click "Add"
3. **Install the integration**:
   - Find "Marstek Battery" in HACS
   - Click "Download"
   - Restart Home Assistant

### Step 2: Add the Integration

1. **Navigate to integrations**: Settings → Devices & Services → Add Integration
2. **Search for "Marstek"** and select the Marstek Battery integration
3. **Enter your device information**:
   - **Device IP Address**: Find your battery's IP address in your router or Marstek app (e.g., `192.168.1.142`)
   - **Remote Port**: The API port configured in your Marstek app (default: `30000`)
   - **Local Port**: Port for Home Assistant to use (default: `30000`)
4. **Click Submit**: The integration will test the connection with up to 3 automatic retries
5. **Success**: Your Marstek device and 25+ sensors will appear in Home Assistant

### Alternative: Manual Installation

1. Download the latest release from GitHub
2. Copy the `custom_components/marstek` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Follow Step 2 above to add the integration

## How It Works

- **Discovery**: The integration automatically discovers your Marstek device and extracts all available information
- **Polling**: Updates all sensors every **1 minute** with intelligent rate limiting to avoid overwhelming your battery
- **Reliability**: Built-in retry logic ensures stable connection during setup and operation
- **Local Communication**: Direct UDP communication with your battery (no internet required)

## Supported Devices

This integration has been tested with:

- Marstek battery systems with UDP/JSON-RPC API capability
- Requires API access enabled by Marstek support

## Available Sensors (25+ Total)

The integration automatically creates comprehensive monitoring sensors organized by category:

### 📊 Device Information (8 sensors)
| Sensor | Description |
|--------|-------------|
| Device Name | Battery system name |
| Device Version | Firmware version |
| BLE MAC Address | Bluetooth MAC address |
| WiFi MAC Address | WiFi MAC address |
| WiFi Name (SSID) | Connected WiFi network |
| Device IP Address | Network IP address |
| Device ID | Internal device identifier |
| Remote Port | API communication port |

### 🔋 Battery Status (7 sensors)
| Sensor | Unit | Description |
|--------|------|-------------|
| Battery Voltage | V | Current battery voltage |
| Battery Current | A | Battery current (+ charging, - discharging) |
| Battery Power | W | Current battery power |
| Battery Temperature | °C | Battery temperature |
| Battery SOC | % | State of charge (battery level) |
| Battery Cycles | cycles | Number of charge/discharge cycles |
| Battery Cell Count | cells | Number of battery cells |

### ⚡ Power Management (3 sensors)
| Sensor | Unit | Description |
|--------|------|-------------|
| Grid Power | W | Power from/to electricity grid |
| Solar Power | W | Solar panel power generation |
| Load Power | W | Power consumption by connected loads |

### 🏠 Energy Monitoring (5 sensors)
| Sensor | Unit | Description |
|--------|------|-------------|
| A Phase Power | W | Phase A electrical power |
| B Phase Power | W | Phase B electrical power |
| C Phase Power | W | Phase C electrical power |
| Total Power | W | Total system power |
| CT State | - | Current transformer status |

### 📡 Network Status (8 sensors)
| Sensor | Unit | Description |
|--------|------|-------------|
| WiFi SSID | - | Connected WiFi network name |
| WiFi Signal Strength | dBm | WiFi signal strength |
| WiFi IP Address | - | Device WiFi IP address |
| WiFi Gateway | - | Network gateway IP |
| WiFi Subnet Mask | - | Network subnet mask |
| WiFi DNS Server | - | DNS server IP |
| BLE Status | - | Bluetooth connection state |
| BLE MAC | - | Bluetooth device address |

### 🔧 System Status
| Sensor | Description |
|--------|-------------|
| Battery SOC (Mode) | Battery level from mode system |
| Off-Grid Power | Power when disconnected from grid |

All sensors update automatically every **60 seconds** and are properly categorized in Home Assistant for easy organization in your dashboard.

## Troubleshooting

### ❌ API Not Enabled (Most Common Issue)

**Problem**: Integration shows "cannot_connect" error during setup

**Solution**:
1. **Verify API is enabled**: Check your Marstek mobile app for "Advanced" section
2. **If no Advanced section**: Contact Marstek support at <https://eu.marstekenergy.com/nl-be/pages/contact> to request API access
3. **Wait for activation**: API activation may take some time after Marstek enables it
4. **Check port settings**: Ensure the port in the Advanced section matches your configuration (default: 30000)

### 🔌 Connection Issues

**Problem**: Timeout errors or connection failures

**Solutions**:
1. **Verify IP address**: Check your router or Marstek app for the correct device IP
2. **Check network connectivity**: Ensure Home Assistant can reach your battery's network
3. **Port conflicts**: Make sure port 30000 isn't used by other applications
4. **Firewall**: Verify no firewall is blocking UDP traffic on port 30000
5. **WiFi network**: Ensure both Home Assistant and the battery are on the same network or have proper routing

### 📊 Sensor Issues

**Problem**: Some sensors show "Unknown" or missing values

**Explanations**:
- **Normal behavior**: Not all sensors may have data at all times (e.g., solar power at night)
- **Battery state dependent**: Some values only appear during specific operations
- **API response variations**: Different battery models may provide different data sets

### 🔧 Advanced Debugging

Enable detailed logging by adding this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.marstek: debug
```

**Restart Home Assistant** after adding the logging configuration. Check the logs for detailed API communication information.

## FAQ

### Q: Why do I need to contact Marstek to enable the API?
**A**: The API is disabled by default for security reasons. Marstek enables it manually upon request to ensure only authorized users can access the battery's data interface.

### Q: How often does the integration update sensor data?
**A**: All sensors update every **60 seconds (1 minute)** with built-in rate limiting to prevent overwhelming your battery system.

### Q: Can I change the update frequency?
**A**: The 1-minute interval is optimized for battery health and system stability. Faster updates are not recommended as they may impact battery performance.

### Q: What happens if my battery doesn't respond?
**A**: The integration includes retry logic during setup (3 attempts). During normal operation, failed updates simply wait for the next cycle.

### Q: Do I need internet access?
**A**: No, the integration communicates directly with your battery via your local network. No cloud or internet connection is required.

## Technical Details

### API Communication
- **Protocol**: UDP with JSON-RPC over local network
- **Port**: 30000 (configurable in Marstek app)
- **Commands**: Bat.GetStatus, ES.GetMode, EM.GetStatus, Wifi.GetStatus, BLE.GetStatus
- **Discovery**: Automatic device discovery during setup
- **Rate limiting**: 2-second delays between API calls to protect battery

### Home Assistant Integration
- **Platform**: Sensor platform with multiple coordinators
- **Device registry**: Full device integration with proper identification
- **Entity categories**: Sensors properly categorized (diagnostic, measurement, etc.)
- **Units**: Proper unit assignment (V, A, W, °C, %, dBm)
- **Updates**: DataUpdateCoordinator pattern for efficient data management

## Contributing

Contributions are welcome! Please feel free to:
- Report bugs or request features via GitHub Issues
- Submit pull requests for improvements
- Share feedback on device compatibility

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

### Getting Help

1. **Check the troubleshooting section** above for common issues
2. **Enable debug logging** to get detailed information
3. **Search existing issues** on GitHub
4. **Create a new issue** with:
   - Home Assistant version
   - Integration version  
   - Marstek device model
   - Complete error logs
   - Screenshots if applicable

### API Access Support

For API enablement issues, contact Marstek directly:
- **Contact form**: <https://eu.marstekenergy.com/nl-be/pages/contact>
- **Request**: "Please enable API access for Home Assistant integration"
- **Include**: Your device serial number or purchase information

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