# ui/widgets/device_card.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QProgressBar, QSlider
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from typing import Dict, Any, Optional
import logging

from models.entity import Entity

logger = logging.getLogger(__name__)

class DeviceCard(QWidget):
    """Enhanced device card widget for displaying and controlling entities."""
    
    # Signal emitted when entity state changes
    entity_toggled = pyqtSignal(str, str)  # entity_id, new_state
    
    def __init__(self, entity: Entity, ha_api):
        super().__init__()
        self.entity = entity
        self.ha_api = ha_api
        self.setObjectName("deviceCard")
        self._slider_active = False  # Track if user is interacting with slider
        self._init_ui()
        self._update_display()

    def _init_ui(self):
        """Initialize the device card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Entity name
        self.name_label = QLabel()
        self.name_label.setObjectName("deviceName")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)

        # Entity state
        self.state_label = QLabel()
        self.state_label.setObjectName("deviceState")
        self.state_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.state_label)

        # Additional info (for sensors, etc.)
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(self.info_label)

        # Progress bar for dimmable entities
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 255)
        layout.addWidget(self.progress_bar)

        # Slider for dimmable entities (like lights)
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setVisible(False)
        self.brightness_slider.setRange(0, 255)
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        self.brightness_slider.sliderPressed.connect(self._on_slider_pressed)
        self.brightness_slider.sliderReleased.connect(self._on_slider_released)
        layout.addWidget(self.brightness_slider)

        # Control buttons
        self._create_control_buttons(layout)

        # Add stretch to push everything to the top
        layout.addStretch()

    def _on_slider_pressed(self):
        """Flag that the user is actively dragging the slider."""
        self._slider_active = True

    def _on_slider_released(self):
        """Flag that the user has finished dragging the slider."""
        self._slider_active = False

    def _create_control_buttons(self, parent_layout):
        """Create control buttons based on entity type."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Determine button type based on entity domain and state
        if self._is_controllable():
            if self._is_dimmable():
                # For dimmable entities, show on/off and brightness control
                self.on_button = QPushButton("ON")
                self.on_button.setObjectName("deviceToggle")
                self.on_button.clicked.connect(self._turn_on)
                button_layout.addWidget(self.on_button)
                
                self.off_button = QPushButton("OFF")
                self.off_button.setObjectName("deviceToggle")
                self.off_button.clicked.connect(self._turn_off)
                button_layout.addWidget(self.off_button)
                
            else:
                # For simple on/off entities
                self.toggle_button = QPushButton()
                self.toggle_button.setObjectName("deviceToggle")
                self.toggle_button.clicked.connect(self._toggle_entity)
                button_layout.addWidget(self.toggle_button)
        else:
            # For read-only entities (sensors, etc.)
            self.info_button = QPushButton("Info")
            self.info_button.setObjectName("secondaryButton")
            self.info_button.setEnabled(False)
            button_layout.addWidget(self.info_button)
        
        parent_layout.addLayout(button_layout)

    def _is_controllable(self) -> bool:
        """Check if the entity can be controlled."""
        controllable_domains = {
            'light', 'switch', 'fan', 'cover', 'lock', 'climate',
            'media_player', 'camera', 'alarm_control_panel'
        }
        return self.entity.domain in controllable_domains

    def _is_dimmable(self) -> bool:
        """Check if the entity supports brightness control."""
        return (self.entity.domain == 'light' and 
                'brightness' in self.entity.attributes)

    def _update_display(self):
        """Update the display with current entity information."""
        # Update name
        self.name_label.setText(self.entity.friendly_name)
        
        # Update state
        state_text = self.entity.state
        if self.entity.unit_of_measurement:
            state_text += f" {self.entity.unit_of_measurement}"
        self.state_label.setText(state_text)
        
        # Set state color
        if self.entity.is_on:
            self.state_label.setProperty("class", "statusOnline")
        elif self.entity.is_off:
            self.state_label.setProperty("class", "statusOffline")
        else:
            self.state_label.setProperty("class", "statusUnknown")
        
        # Update additional info
        self._update_additional_info()
        
        # Update brightness controls
        self._update_brightness_controls()
        
        # Update button states
        self._update_button_states()

    def _update_additional_info(self):
        """Update additional information display."""
        info_parts = []
        
        # Add device class if available
        if self.entity.device_class:
            info_parts.append(f"Type: {self.entity.device_class}")
        
        # Add icon if available
        if self.entity.icon:
            info_parts.append(f"Icon: {self.entity.icon}")
        
        # Add last updated time
        if self.entity.last_updated:
            from datetime import datetime
            try:
                last_update = datetime.fromisoformat(
                    self.entity.last_updated.replace('Z', '+00:00')
                )
                info_parts.append(f"Updated: {last_update.strftime('%H:%M:%S')}")
            except:
                pass
        
        self.info_label.setText(" • ".join(info_parts))

    def _update_brightness_controls(self):
        """Update brightness controls for dimmable entities."""
        if not self._is_dimmable():
            self.progress_bar.setVisible(False)
            self.brightness_slider.setVisible(False)
            return

        brightness = self.entity.attributes.get('brightness', 0)
        brightness = brightness if brightness is not None else 0

        # Update progress bar
        self.progress_bar.setValue(brightness)
        self.progress_bar.setVisible(True)

        # Only update slider if not actively dragging
        if not self._slider_active:
            self.brightness_slider.setValue(brightness)
        self.brightness_slider.setVisible(True)

    def _update_button_states(self):
        """Update button states based on entity state."""
        if hasattr(self, 'toggle_button'):
            if self.entity.is_on:
                self.toggle_button.setText("Turn Off")
                self.toggle_button.setStyleSheet("background-color: #d32f2f;")
            else:
                self.toggle_button.setText("Turn On")
                self.toggle_button.setStyleSheet("background-color: #0078d4;")
        
        if hasattr(self, 'on_button'):
            self.on_button.setEnabled(not self.entity.is_on)
        
        if hasattr(self, 'off_button'):
            self.off_button.setEnabled(self.entity.is_on)

    def _toggle_entity(self):
        """Toggle the entity state."""
        try:
            success = self.ha_api.toggle_entity(self.entity.entity_id)
            if success:
                # Optimistically update state
                new_state = "off" if self.entity.is_on else "on"
                self.entity.state = new_state
                self._update_display()
                self.entity_toggled.emit(self.entity.entity_id, new_state)
            else:
                logger.error(f"Failed to toggle entity {self.entity.entity_id}")
        except Exception as e:
            logger.error(f"Error toggling entity {self.entity.entity_id}: {e}")

    def _turn_on(self):
        """Turn on the entity."""
        try:
            success = self.ha_api.turn_on_entity(self.entity.entity_id)
            if success:
                self.entity.state = "on"
                self._update_display()
                self.entity_toggled.emit(self.entity.entity_id, "on")
        except Exception as e:
            logger.error(f"Error turning on entity {self.entity.entity_id}: {e}")

    def _turn_off(self):
        """Turn off the entity."""
        try:
            success = self.ha_api.turn_off_entity(self.entity.entity_id)
            if success:
                self.entity.state = "off"
                self._update_display()
                self.entity_toggled.emit(self.entity.entity_id, "off")
        except Exception as e:
            logger.error(f"Error turning off entity {self.entity.entity_id}: {e}")

    def _on_brightness_changed(self, value):
        """Handle brightness slider changes."""
        if not self._is_dimmable():
            return
        
        try:
            # If the entity is off, turn it on first
            success = self.ha_api.turn_on_entity(
                self.entity.entity_id, 
                brightness=value
            )
            # If the entity turned on, update brightness
            if success:
                self.entity.attributes['brightness'] = value
                self.progress_bar.setValue(value)
        except Exception as e:
            logger.error(f"Error changing brightness for {self.entity.entity_id}: {e}")

    def update_entity(self, entity_data: Dict[str, Any]):
        """Update the entity with new data from WebSocket."""
        try:
            # Update entity object
            self.entity.update_from_dict(entity_data)
            
            # Update display
            self._update_display()
            
        except Exception as e:
            logger.error(f"Error updating entity display: {e}")

    def get_entity(self) -> Entity:
        """Get the current entity."""
        return self.entity