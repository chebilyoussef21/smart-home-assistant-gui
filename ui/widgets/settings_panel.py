# ui/widgets/settings_panel.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFormLayout, QLineEdit, QSpinBox, QCheckBox,
    QComboBox, QSlider, QMessageBox, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from typing import Dict, Any, Optional
import logging
import json
import os

logger = logging.getLogger(__name__)

class SettingsPanel(QWidget):
    """Settings panel for configuring the Home Assistant GUI."""
    
    # Signal emitted when settings change
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, ha_api, api_config):
        super().__init__()
        self.ha_api = ha_api
        self.api_config = api_config
        self.settings = self._load_settings()
        
        # Connect API signals
        self.ha_api.connection_status_changed.connect(self._on_connection_status_changed)
        self.ha_api.error_occurred.connect(self._on_error_occurred)
        
        self._init_ui()
        self._update_connection_status()

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from config file."""
        try:
            # Try to load from a settings file
            settings_file = os.path.join(os.path.dirname(__file__), "..", "..", "config", "user_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load user settings: {e}")
        
        # Return default settings
        return {
            "theme": "dark",
            "refresh_interval": 5,
            "auto_refresh": True,
            "show_offline_entities": False,
            "compact_view": False,
            "notifications": True,
            "sound_effects": False
        }

    def _save_settings(self):
        """Save settings to config file."""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), "..", "..", "config", "user_settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
                
            self.settings_changed.emit(self.settings)
            logger.info("Settings saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save settings:\n{str(e)}")

    def _init_ui(self):
        """Initialize the settings panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        self._create_header(layout)
        
        # Scrollable content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        
        # Settings sections
        self._create_connection_section(content_layout)
        self._create_ui_section(content_layout)
        self._create_behavior_section(content_layout)
        self._create_about_section(content_layout)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def _create_header(self, parent_layout):
        """Create the header with title and save button."""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Settings")
        title_label.setObjectName("pageTitle")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Save button
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self._save_settings)
        header_layout.addWidget(self.save_button)
        
        parent_layout.addWidget(header_frame)

    def _create_connection_section(self, parent_layout):
        """Create the connection settings section."""
        group = QGroupBox("Connection Settings")
        layout = QFormLayout(group)
        
        # Connection status
        self.connection_status_label = QLabel("Unknown")
        self.connection_status_label.setProperty("class", "statusUnknown")
        layout.addRow("Status:", self.connection_status_label)
        
        # Host
        self.host_edit = QLineEdit()
        self.host_edit.setText(self.api_config.get("host", ""))
        self.host_edit.setPlaceholderText("http://localhost:8123")
        layout.addRow("Host:", self.host_edit)
        
        # API Token
        self.token_edit = QLineEdit()
        self.token_edit.setText(self.api_config.get("api_token", ""))
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.token_edit.setPlaceholderText("Your long-lived access token")
        layout.addRow("API Token:", self.token_edit)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(self.api_config.get("timeout", 10))
        self.timeout_spin.setSuffix(" seconds")
        layout.addRow("Timeout:", self.timeout_spin)
        
        # WebSocket
        self.websocket_checkbox = QCheckBox("Use WebSocket for real-time updates")
        self.websocket_checkbox.setChecked(self.api_config.get("use_websocket", True))
        layout.addRow("", self.websocket_checkbox)
        
        # Test connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        layout.addRow("", self.test_button)
        
        parent_layout.addWidget(group)

    def _create_ui_section(self, parent_layout):
        """Create the UI settings section."""
        group = QGroupBox("User Interface")
        layout = QFormLayout(group)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "dark"))
        layout.addRow("Theme:", self.theme_combo)
        
        # Refresh interval
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(1, 60)
        self.refresh_spin.setValue(self.settings.get("refresh_interval", 5))
        self.refresh_spin.setSuffix(" seconds")
        layout.addRow("Refresh Interval:", self.refresh_spin)
        
        # Auto refresh
        self.auto_refresh_checkbox = QCheckBox("Enable automatic refresh")
        self.auto_refresh_checkbox.setChecked(self.settings.get("auto_refresh", True))
        layout.addRow("", self.auto_refresh_checkbox)
        
        # Show offline entities
        self.show_offline_checkbox = QCheckBox("Show offline entities")
        self.show_offline_checkbox.setChecked(self.settings.get("show_offline_entities", False))
        layout.addRow("", self.show_offline_checkbox)
        
        # Compact view
        self.compact_view_checkbox = QCheckBox("Use compact view")
        self.compact_view_checkbox.setChecked(self.settings.get("compact_view", False))
        layout.addRow("", self.compact_view_checkbox)
        
        parent_layout.addWidget(group)

    def _create_behavior_section(self, parent_layout):
        """Create the behavior settings section."""
        group = QGroupBox("Behavior")
        layout = QFormLayout(group)
        
        # Notifications
        self.notifications_checkbox = QCheckBox("Enable notifications")
        self.notifications_checkbox.setChecked(self.settings.get("notifications", True))
        layout.addRow("", self.notifications_checkbox)
        
        # Sound effects
        self.sound_effects_checkbox = QCheckBox("Enable sound effects")
        self.sound_effects_checkbox.setChecked(self.settings.get("sound_effects", False))
        layout.addRow("", self.sound_effects_checkbox)
        
        parent_layout.addWidget(group)

    def _create_about_section(self, parent_layout):
        """Create the about section."""
        group = QGroupBox("About")
        layout = QVBoxLayout(group)
        
        # App info
        app_info = QLabel("Home Assistant GUI v1.0.0")
        app_info.setAlignment(Qt.AlignCenter)
        app_info.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(app_info)
        
        # Description
        description = QLabel(
            "A modern, intuitive GUI for controlling your Home Assistant setup.\n"
            "Built with PyQt5 and designed for Raspberry Pi clients."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #888888; margin-bottom: 10px;")
        layout.addWidget(description)
        
        # System info
        system_info = QLabel(
            f"Connected to: {self.api_config.get('host', 'Unknown')}\n"
            f"API Version: {self._get_api_version()}"
        )
        system_info.setAlignment(Qt.AlignCenter)
        system_info.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(system_info)
        
        parent_layout.addWidget(group)

    def _get_api_version(self) -> str:
        """Get the Home Assistant API version."""
        try:
            config = self.ha_api.get_config()
            if config:
                return config.get("version", "Unknown")
        except Exception:
            pass
        return "Unknown"

    def _test_connection(self):
        """Test the connection with current settings."""
        self.test_button.setText("Testing...")
        self.test_button.setEnabled(False)
        
        # Update API config with current values
        test_config = {
            "host": self.host_edit.text(),
            "api_token": self.token_edit.text(),
            "timeout": self.timeout_spin.value(),
            "use_websocket": self.websocket_checkbox.isChecked()
        }
        
        # Test connection in a separate thread
        QTimer.singleShot(100, lambda: self._perform_connection_test(test_config))

    def _perform_connection_test(self, test_config):
        """Perform the actual connection test."""
        try:
            # Create temporary API instance for testing
            from services.ha_api import HomeAssistantAPI
            test_api = HomeAssistantAPI(
                host=test_config["host"],
                token=test_config["api_token"],
                timeout=test_config["timeout"],
                use_websocket=False  # Don't use WebSocket for testing
            )
            
            config = test_api.get_config()
            if config:
                self.connection_status_label.setText("✅ Connected")
                self.connection_status_label.setProperty("class", "statusOnline")
                QMessageBox.information(self, "Success", "Connection test successful!")
            else:
                self.connection_status_label.setText("❌ Connection Failed")
                self.connection_status_label.setProperty("class", "statusOffline")
                QMessageBox.warning(self, "Error", "Connection test failed!")
                
        except Exception as e:
            self.connection_status_label.setText("❌ Connection Error")
            self.connection_status_label.setProperty("class", "statusOffline")
            QMessageBox.warning(self, "Error", f"Connection test failed:\n{str(e)}")
        
        finally:
            self.test_button.setText("Test Connection")
            self.test_button.setEnabled(True)

    def _on_connection_status_changed(self, is_connected):
        """Handle connection status changes."""
        self._update_connection_status()

    def _on_error_occurred(self, error_message):
        """Handle errors from the API."""
        # Update connection status if it's a connection error
        if "Connection" in error_message or "WebSocket" in error_message:
            self._update_connection_status()

    def _update_connection_status(self):
        """Update the connection status display."""
        if hasattr(self.ha_api, 'is_connected'):
            if self.ha_api.is_connected:
                self.connection_status_label.setText("✅ Connected")
                self.connection_status_label.setProperty("class", "statusOnline")
            else:
                self.connection_status_label.setText("❌ Disconnected")
                self.connection_status_label.setProperty("class", "statusOffline")
        else:
            self.connection_status_label.setText("Unknown")
            self.connection_status_label.setProperty("class", "statusUnknown")

    def refresh(self):
        """Refresh the settings panel."""
        self._update_connection_status()
        
        # Update system info
        system_info = self._get_api_version()
        
        # Update settings from current values
        self.settings.update({
            "theme": self.theme_combo.currentText(),
            "refresh_interval": self.refresh_spin.value(),
            "auto_refresh": self.auto_refresh_checkbox.isChecked(),
            "show_offline_entities": self.show_offline_checkbox.isChecked(),
            "compact_view": self.compact_view_checkbox.isChecked(),
            "notifications": self.notifications_checkbox.isChecked(),
            "sound_effects": self.sound_effects_checkbox.isChecked()
        })

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings."""
        return self.settings.copy()

    def get_api_config(self) -> Dict[str, Any]:
        """Get current API configuration."""
        return {
            "host": self.host_edit.text(),
            "api_token": self.token_edit.text(),
            "timeout": self.timeout_spin.value(),
            "use_websocket": self.websocket_checkbox.isChecked()
        }
