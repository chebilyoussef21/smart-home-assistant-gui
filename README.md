# Home Assistant GUI

# 1) Installation:

## Quick install (Linux)
bash curl -fsSL https://raw.githubusercontent.com/OWNER/REPO/main/install.sh | sudo bash

## Manual Run (Linux Desktop)
xhost +local:docker
docker run --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  ghcr.io/OWNER/REPO:latest

## --> install.sh + docker-compose is how you deploy/run the app on target machines, while .github/workflows/build.yaml (GitHub Actions) is how you build, test, version, and publish the app image automatically whenever you push code. They solve different stages of the lifecycle.

## System FLOW:
You push code → GitHub Actions builds & pushes a new container image.
Target machines are already running your compose stack + Watchtower.
Watchtower detects the new image tag and restarts the app with the update.
User data persists in the volume; only the container code changes.

#IDK
# build locally
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/OWNER/REPO:latest --push .
# run locally
xhost +local:docker
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro ghcr.io/OWNER/REPO:latest


# 2) App Overview:

A modern, intuitive Qt-based Python GUI for controlling your Home Assistant setup. Designed specifically for Raspberry Pi clients and non-technical users who want to interact with their smart home without dealing with the complexity of Home Assistant's web interface.

## Features

### 🏠 **Device Control**
- **Grid View**: Scrollable grid of device cards showing entity name, state, and control buttons
- **Real-time Updates**: Live state updates via WebSocket connection
- **Smart Controls**: Automatic detection of device types (lights, switches, sensors, etc.)
- **Dimmable Support**: Brightness control for dimmable lights with sliders and progress bars
- **Filtering**: Filter devices by domain (light, switch, sensor, etc.) and search by name

### 🤖 **Automation Management**
- **Visual Editor**: Form-based interface for creating and editing automations
- **Trigger Management**: Support for state, time, and event triggers
- **Condition Support**: Add conditions to your automations
- **Action Configuration**: Configure actions with entity selection and parameters
- **Automation List**: View all automations with status indicators

### ⚙️ **Settings & Configuration**
- **Connection Management**: Configure Home Assistant host, API token, and connection settings
- **Real-time Status**: Live connection status monitoring
- **UI Customization**: Dark theme with modern design
- **Refresh Controls**: Configurable auto-refresh intervals
- **Error Handling**: Comprehensive error handling with user-friendly messages

### 🎨 **Modern UI Design**
- **Dark Theme**: Professional dark theme with modern styling
- **Responsive Layout**: Adaptive layout that works on different screen sizes
- **SVG Icons**: Clean, scalable icons throughout the interface
- **Smooth Animations**: Hover effects and smooth transitions
- **Status Indicators**: Color-coded status indicators for connection and device states

## Architecture

### **Modular Design**
```
├── main.py                 # Application entry point
├── test_modular_ui.py     # Test script for modular UI
├── config/
│   └── settings.py         # Configuration management
├── services/
│   ├── ha_api.py          # Home Assistant API wrapper
│   └── automation_manager.py # Automation management
├── models/
│   ├── entity.py          # Entity data model
│   └── automation.py      # Automation data model
├── ui/
│   ├── main_window.py     # Main application window
│   └── widgets/
│       ├── navigation_sidebar.py # Navigation sidebar
│       ├── page_stack_manager.py # Page stack management
│       ├── overview_page.py     # Overview dashboard
│       ├── device_grid.py       # Device grid view
│       ├── device_card.py       # Individual device cards
│       ├── automation_editor.py # Automation editor
│       ├── scenes_page.py       # Scenes management
│       ├── scripts_page.py      # Scripts management
│       └── settings_panel.py    # Settings panel
├── utils/
│   └── helpers.py         # Utility functions
└── assets/
    ├── stylesheet/
    │   └── styles.qss     # Dark theme stylesheet
    └── icons/             # SVG icons
```

### **Key Components**

1. **HomeAssistantAPI**: Enhanced API wrapper with REST and WebSocket support
2. **Entity Model**: Type-safe entity representation with validation
3. **Automation Model**: Comprehensive automation data structures
4. **Page Stack Manager**: Manages page navigation with state preservation
5. **Navigation Sidebar**: Modern sidebar with Home Assistant sections
6. **Modular Pages**: Separate widgets for each major functionality
7. **Device Grid**: Scrollable grid with filtering and real-time updates
8. **Settings Panel**: Configuration management with connection testing

### **Page Structure**

The application is organized into the following main pages:

- **Overview**: System dashboard with quick controls and status
- **Devices**: Grid view of all Home Assistant entities with controls
- **Automations**: Visual editor for creating and managing automations
- **Scenes**: Scene management and activation
- **Scripts**: Script execution and management
- **Settings**: Configuration and connection management

Each page maintains its own state and can be refreshed independently while preserving user interactions and data.

## Installation

### Prerequisites
- Python 3.8 or higher
- Home Assistant instance running (local or remote)
- Long-lived access token from Home Assistant

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd smart_home_assistant_gui_qt
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Home Assistant**:
   - Generate a long-lived access token in Home Assistant
   - Update `config/settings.py` with your Home Assistant details:
   ```python
   HOME_ASSISTANT = {
       "host": "http://your-ha-instance:8123",
       "api_token": "YOUR_LONG_LIVED_ACCESS_TOKEN",
       "use_websocket": True,
       "timeout": 10
   }
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## Configuration

### Home Assistant Settings
Edit `config/settings.py` to configure your Home Assistant connection:

```python
HOME_ASSISTANT = {
    "host": "http://localhost:8123",  # Your HA instance URL
    "api_token": "YOUR_TOKEN",        # Long-lived access token
    "use_websocket": True,            # Enable real-time updates
    "timeout": 10                     # Request timeout in seconds
}

UI = {
    "theme": "dark",                  # UI theme
    "refresh_interval": 5,            # Auto-refresh interval in seconds
}
```

### User Settings
User-specific settings are automatically saved to `config/user_settings.json` and include:
- Theme preferences
- Refresh intervals
- Display options
- Notification settings

## Usage

### Device Control
1. **View Devices**: The main "Devices" tab shows all your Home Assistant entities
2. **Filter Devices**: Use the domain filter and search box to find specific devices
3. **Control Devices**: Click toggle buttons to control lights, switches, and other devices
4. **Brightness Control**: For dimmable lights, use the brightness slider
5. **Real-time Updates**: Device states update automatically via WebSocket

### Automation Management
1. **View Automations**: The "Automations" tab lists all your automations
2. **Create Automation**: Click "New Automation" to create a new automation
3. **Edit Automation**: Select an automation and click "Edit" to modify it
4. **Automation Details**: View triggers, conditions, and actions for each automation

### Settings
1. **Connection Settings**: Configure Home Assistant host and API token
2. **Test Connection**: Use the "Test Connection" button to verify settings
3. **UI Preferences**: Customize theme, refresh intervals, and display options
4. **Save Settings**: Click "Save Settings" to persist your preferences

## Development

### Project Structure
The project follows a modular architecture with clear separation of concerns:

- **Models**: Data structures and validation
- **Services**: Business logic and API communication
- **UI**: User interface components and layouts
- **Utils**: Helper functions and utilities

### Adding New Features
1. **New Device Types**: Extend the `DeviceCard` class to support new entity types
2. **New Automation Triggers**: Add trigger types to the `Trigger` model
3. **New UI Views**: Create new widgets in the `ui/widgets/` directory
4. **API Extensions**: Add new methods to the `HomeAssistantAPI` class

### Testing
```bash
# Run tests (when implemented)
python -m pytest tests/

# Check code style
flake8 .

# Type checking
mypy .
```

## Troubleshooting

### Common Issues

1. **Connection Failed**:
   - Verify Home Assistant is running and accessible
   - Check the host URL and port
   - Ensure the API token is valid and has proper permissions

2. **WebSocket Connection Issues**:
   - Check if WebSocket is enabled in Home Assistant
   - Verify firewall settings allow WebSocket connections
   - Try disabling WebSocket in settings if issues persist

3. **Device Not Responding**:
   - Check if the entity is available in Home Assistant
   - Verify the entity supports the requested service
   - Check Home Assistant logs for errors

4. **UI Not Loading**:
   - Ensure all dependencies are installed
   - Check the logs directory for error messages
   - Verify the stylesheet file exists

### Logs
Application logs are saved to `logs/ha_gui.log` and include:
- Connection status changes
- API request/response details
- Error messages and stack traces
- User actions and system events

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [PyQt5](https://doc.qt.io/qtforpython/) (Qt for Python)
- Designed for [Home Assistant](https://www.home-assistant.io/)
- Icons from [Material Design Icons](https://materialdesignicons.com/)

## Future Enhancements

- **Voice Control**: Integration with speech recognition
- **MQTT Support**: Direct MQTT communication
- **AI Integration**: Smart automation suggestions
- **Mobile Support**: Responsive design for tablets
- **Plugin System**: Extensible architecture for custom integrations
- **Dashboard Customization**: User-configurable dashboards
- **Scene Management**: Visual scene editor
- **Energy Monitoring**: Energy usage visualization
