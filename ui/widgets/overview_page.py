# ui/widgets/overview_page.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QFrame, QScrollArea, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap
from typing import Dict, Any, List
import logging
from datetime import datetime

from models.entity import Entity

logger = logging.getLogger(__name__)

class OverviewPage(QWidget):
    """Overview page showing system status and quick controls."""
    
    # Signals
    entity_clicked = pyqtSignal(str)  # entity_id
    refresh_requested = pyqtSignal()
    
    def __init__(self, ha_api):
        super().__init__()
        self.ha_api = ha_api
        self.entities: List[Entity] = []
        self.last_refresh = None
        
        # Connect API signals
        self.ha_api.entity_updated.connect(self._on_entity_updated)
        
        self._init_ui()
        QTimer.singleShot(0, self.refresh)

    def _init_ui(self):
        """Initialize the overview page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        self._create_header(layout)
        
        # Main content with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(16)
        
        # Create sections
        self._create_system_status_section()
        self._create_quick_controls_section()
        self._create_recent_activity_section()
        self._create_energy_usage_section()
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def _create_header(self, parent_layout):
        """Create the page header."""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Overview")
        title_label.setObjectName("pageTitle")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Last updated
        self.last_updated_label = QLabel("Never updated")
        self.last_updated_label.setStyleSheet("color: #888888; font-size: 12px;")
        header_layout.addWidget(self.last_updated_label)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_button)
        
        parent_layout.addWidget(header_frame)

    def _create_system_status_section(self):
        """Create the system status section."""
        group = QGroupBox("System Status")
        layout = QGridLayout(group)
        
        # Connection status
        self.connection_status_label = QLabel("Unknown")
        self.connection_status_label.setProperty("class", "statusUnknown")
        layout.addWidget(QLabel("Connection:"), 0, 0)
        layout.addWidget(self.connection_status_label, 0, 1)
        
        # Home Assistant version
        self.ha_version_label = QLabel("Unknown")
        layout.addWidget(QLabel("HA Version:"), 0, 2)
        layout.addWidget(self.ha_version_label, 0, 3)
        
        # Total entities
        self.total_entities_label = QLabel("0")
        layout.addWidget(QLabel("Total Entities:"), 1, 0)
        layout.addWidget(self.total_entities_label, 1, 1)
        
        # Active automations
        self.active_automations_label = QLabel("0")
        layout.addWidget(QLabel("Active Automations:"), 1, 2)
        layout.addWidget(self.active_automations_label, 1, 3)
        
        # Online devices
        self.online_devices_label = QLabel("0")
        layout.addWidget(QLabel("Online Devices:"), 2, 0)
        layout.addWidget(self.online_devices_label, 2, 1)
        
        # Offline devices
        self.offline_devices_label = QLabel("0")
        layout.addWidget(QLabel("Offline Devices:"), 2, 2)
        layout.addWidget(self.offline_devices_label, 2, 3)
        
        self.content_layout.addWidget(group)

    def _create_quick_controls_section(self):
        """Create the quick controls section."""
        group = QGroupBox("Quick Controls")
        layout = QGridLayout(group)
        
        # Get some common entities for quick access
        self.quick_control_buttons = []
        
        # This will be populated with actual entities during refresh
        for i in range(6):  # 2 rows x 3 columns
            button = QPushButton("Loading...")
            button.setObjectName("deviceToggle")
            button.setEnabled(False)
            button.clicked.connect(lambda checked, idx=i: self._on_quick_control_clicked(idx))
            layout.addWidget(button, i // 3, i % 3)
            self.quick_control_buttons.append(button)
        
        self.content_layout.addWidget(group)

    def _create_recent_activity_section(self):
        """Create the recent activity section."""
        group = QGroupBox("Recent Activity")
        layout = QVBoxLayout(group)
        
        self.activity_list = QLabel("No recent activity")
        self.activity_list.setStyleSheet("color: #888888; font-style: italic;")
        self.activity_list.setWordWrap(True)
        layout.addWidget(self.activity_list)
        
        self.content_layout.addWidget(group)

    def _create_energy_usage_section(self):
        """Create the energy usage section."""
        group = QGroupBox("Energy Usage")
        layout = QGridLayout(group)
        
        # Today's usage
        self.today_usage_label = QLabel("0 kWh")
        layout.addWidget(QLabel("Today:"), 0, 0)
        layout.addWidget(self.today_usage_label, 0, 1)
        
        # This month's usage
        self.month_usage_label = QLabel("0 kWh")
        layout.addWidget(QLabel("This Month:"), 0, 2)
        layout.addWidget(self.month_usage_label, 0, 3)
        
        # Cost
        self.cost_label = QLabel("$0.00")
        layout.addWidget(QLabel("Estimated Cost:"), 1, 0)
        layout.addWidget(self.cost_label, 1, 1)
        
        self.content_layout.addWidget(group)

    def refresh(self):
        """Refresh the overview data."""
        try:
            # Update connection status
            if hasattr(self.ha_api, 'is_connected'):
                if self.ha_api.is_connected:
                    self.connection_status_label.setText("✅ Connected")
                    self.connection_status_label.setProperty("class", "statusOnline")
                else:
                    self.connection_status_label.setText("❌ Disconnected")
                    self.connection_status_label.setProperty("class", "statusOffline")
                    # Skip network calls while offline to avoid UI blocking
                    self.entities = []
                    self._update_quick_controls()
                    self._update_energy_usage()
                    return
            
            # Get Home Assistant config
            config = self.ha_api.get_config()
            if config:
                self.ha_version_label.setText(config.get("version", "Unknown"))
            
            # Get entities
            states_data = self.ha_api.get_states()
            self.entities = []
            for state_data in states_data:
                try:
                    entity = Entity.from_dict(state_data)
                    self.entities.append(entity)
                except Exception as e:
                    logger.warning(f"Failed to parse entity: {e}")
            
            # Update entity counts
            self.total_entities_label.setText(str(len(self.entities)))
            
            online_count = sum(1 for e in self.entities if e.is_available)
            offline_count = len(self.entities) - online_count
            
            self.online_devices_label.setText(str(online_count))
            self.offline_devices_label.setText(str(offline_count))
            
            # Update quick controls
            self._update_quick_controls()
            
            # Update energy usage
            self._update_energy_usage()
            
            # Update last refresh time
            self.last_refresh = datetime.now()
            self.last_updated_label.setText(f"Last updated: {self.last_refresh.strftime('%H:%M:%S')}")
            
            logger.info("Overview page refreshed successfully")
            
        except Exception as e:
            logger.error(f"Failed to refresh overview: {e}")

    def _update_quick_controls(self):
        """Update the quick control buttons with common entities."""
        # Find common controllable entities
        controllable_entities = [
            e for e in self.entities 
            if e.domain in ['light', 'switch', 'fan'] and e.is_available
        ]
        
        # Sort by friendly name
        controllable_entities.sort(key=lambda x: x.friendly_name)
        
        # Update buttons
        for i, button in enumerate(self.quick_control_buttons):
            if i < len(controllable_entities):
                entity = controllable_entities[i]
                button.setText(entity.friendly_name)
                button.setEnabled(True)
                button.setProperty("entity_id", entity.entity_id)
                
                # Set button style based on state
                if entity.is_on:
                    button.setStyleSheet("background-color: #4caf50; color: white;")
                else:
                    button.setStyleSheet("background-color: #666666; color: white;")
            else:
                button.setText("")
                button.setEnabled(False)
                button.setProperty("entity_id", "")

    def _update_energy_usage(self):
        """Update energy usage information."""
        # Find energy sensors
        energy_entities = [
            e for e in self.entities 
            if e.domain == 'sensor' and 'energy' in e.entity_id.lower()
        ]
        
        total_energy = 0
        for entity in energy_entities:
            try:
                if entity.unit_of_measurement == 'kWh':
                    total_energy += float(entity.state)
            except (ValueError, TypeError):
                continue
        
        self.today_usage_label.setText(f"{total_energy:.2f} kWh")
        self.month_usage_label.setText(f"{total_energy * 30:.2f} kWh")  # Rough estimate
        self.cost_label.setText(f"${total_energy * 0.12:.2f}")  # Rough estimate at $0.12/kWh

    def _on_quick_control_clicked(self, button_index):
        """Handle quick control button clicks."""
        button = self.quick_control_buttons[button_index]
        entity_id = button.property("entity_id")
        
        if entity_id:
            try:
                # Toggle the entity
                success = self.ha_api.toggle_entity(entity_id)
                if success:
                    # Update button state optimistically
                    self._update_quick_controls()
                    self.entity_clicked.emit(entity_id)
            except Exception as e:
                logger.error(f"Failed to toggle entity {entity_id}: {e}")

    def _on_entity_updated(self, entity_data: Dict[str, Any]):
        """Handle real-time entity updates."""
        entity_id = entity_data.get("entity_id")
        
        # Update the entity in our list
        for i, entity in enumerate(self.entities):
            if entity.entity_id == entity_id:
                entity.update_from_dict(entity_data)
                break
        
        # Refresh quick controls if this entity is shown
        self._update_quick_controls()

    def get_page_state(self) -> Dict[str, Any]:
        """Get the current state of the page for preservation."""
        return {
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "entities_count": len(self.entities),
            "connection_status": self.connection_status_label.text()
        }

    def restore_page_state(self, state: Dict[str, Any]):
        """Restore the page state."""
        if state.get("last_refresh"):
            try:
                self.last_refresh = datetime.fromisoformat(state["last_refresh"])
                self.last_updated_label.setText(f"Last updated: {self.last_refresh.strftime('%H:%M:%S')}")
            except ValueError:
                pass
