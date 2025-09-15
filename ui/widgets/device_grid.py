# ui/widgets/device_grid.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from typing import List, Dict, Optional
import logging

from models.entity import Entity
from ui.widgets.device_card import DeviceCard

logger = logging.getLogger(__name__)

class DeviceGridView(QWidget):
    """Grid view for displaying Home Assistant devices."""
    
    def __init__(self, ha_api):
        super().__init__()
        self.ha_api = ha_api
        self.entities: List[Entity] = []
        self.device_cards: Dict[str, DeviceCard] = {}
        
        # Connect API signals
        self.ha_api.entity_updated.connect(self._on_entity_updated)
        
        self._init_ui()
        QTimer.singleShot(0, self.refresh)

    def _init_ui(self):
        """Initialize the device grid UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header with title and controls
        self._create_header(layout)
        
        # Scrollable content area
        self._create_scroll_area(layout)

    def _create_header(self, parent_layout):
        """Create the header with title and controls."""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Devices")
        title_label.setObjectName("pageTitle")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Filter controls
        self._create_filter_controls(header_layout)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_button)
        
        parent_layout.addWidget(header_frame)

    def _create_filter_controls(self, parent_layout):
        """Create filter controls for the device grid."""
        # Domain filter
        domain_label = QLabel("Domain:")
        parent_layout.addWidget(domain_label)
        
        self.domain_filter = QComboBox()
        self.domain_filter.addItem("All")
        self.domain_filter.currentTextChanged.connect(self._apply_filters)
        parent_layout.addWidget(self.domain_filter)
        
        # Search box
        search_label = QLabel("Search:")
        parent_layout.addWidget(search_label)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search devices...")
        self.search_box.textChanged.connect(self._apply_filters)
        parent_layout.addWidget(self.search_box)

    def _create_scroll_area(self, parent_layout):
        """Create the scrollable area for device cards."""
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content widget
        self.content_widget = QWidget()
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.content_widget)
        parent_layout.addWidget(self.scroll_area)

    def refresh(self):
        """Refresh the device list from Home Assistant."""
        try:
            # Skip network calls if offline
            if hasattr(self.ha_api, 'is_connected') and not self.ha_api.is_connected:
                self.entities = []
                self._update_domain_filter()
                self._update_device_cards()
                return

            # Fetch entities from Home Assistant
            states_data = self.ha_api.get_states()
            
            # Convert to Entity objects
            self.entities = []
            for state_data in states_data:
                try:
                    entity = Entity.from_dict(state_data)
                    self.entities.append(entity)
                except Exception as e:
                    logger.warning(f"Failed to parse entity {state_data.get('entity_id', 'unknown')}: {e}")
            
            # Update domain filter
            self._update_domain_filter()
            
            # Update device cards
            self._update_device_cards()
            
            logger.info(f"Refreshed {len(self.entities)} entities")
            
        except Exception as e:
            logger.error(f"Failed to refresh devices: {e}")

    def _update_domain_filter(self):
        """Update the domain filter dropdown with available domains."""
        current_text = self.domain_filter.currentText()
        
        # Get unique domains
        domains = set()
        for entity in self.entities:
            domains.add(entity.domain)
        
        # Update dropdown
        self.domain_filter.clear()
        self.domain_filter.addItem("All")
        self.domain_filter.addItems(sorted(domains))
        
        # Restore selection if possible
        if current_text in [self.domain_filter.itemText(i) for i in range(self.domain_filter.count())]:
            self.domain_filter.setCurrentText(current_text)

    def _update_device_cards(self):
        """Update the device cards in the grid."""
        # Clear existing cards
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        self.device_cards.clear()
        
        # Filter entities
        filtered_entities = self._filter_entities()
        
        # Create device cards
        row = 0
        col = 0
        max_cols = 4  # Maximum number of columns
        
        for entity in filtered_entities:
            # Skip hidden entities
            if entity.attributes.get("hidden", False):
                continue
                
            # Create device card
            device_card = DeviceCard(entity, self.ha_api)
            self.device_cards[entity.entity_id] = device_card
            
            # Add to grid
            self.grid_layout.addWidget(device_card, row, col)
            
            # Update position
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _filter_entities(self) -> List[Entity]:
        """Filter entities based on current filter settings."""
        filtered = []
        
        # Domain filter
        domain_filter = self.domain_filter.currentText()
        if domain_filter != "All":
            filtered = [e for e in self.entities if e.domain == domain_filter]
        else:
            filtered = self.entities.copy()
        
        # Search filter
        search_text = self.search_box.text().lower()
        if search_text:
            filtered = [
                e for e in filtered 
                if search_text in e.friendly_name.lower() or 
                   search_text in e.entity_id.lower()
            ]
        
        return filtered

    def _apply_filters(self):
        """Apply current filters and update the display."""
        self._update_device_cards()

    def _on_entity_updated(self, entity_data: Dict):
        """Handle real-time entity updates from WebSocket."""
        entity_id = entity_data.get("entity_id")
        if entity_id in self.device_cards:
            # Update the existing device card
            device_card = self.device_cards[entity_id]
            device_card.update_entity(entity_data)
        else:
            # Entity might be new, refresh the entire list
            self.refresh()

    def get_entity_count(self) -> int:
        """Get the total number of entities."""
        return len(self.entities)

    def get_filtered_count(self) -> int:
        """Get the number of entities after filtering."""
        return len(self._filter_entities())
