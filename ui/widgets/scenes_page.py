# ui/widgets/scenes_page.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QFrame, QScrollArea, QGroupBox, QListWidget,
    QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SceneCard(QWidget):
    """Widget for displaying and controlling a scene."""
    
    scene_activated = pyqtSignal(str)  # scene_id
    
    def __init__(self, scene_data: Dict[str, Any], ha_api):
        super().__init__()
        self.scene_data = scene_data
        self.ha_api = ha_api
        self.scene_id = scene_data.get("entity_id", "")
        
        self._init_ui()

    def _init_ui(self):
        """Initialize the scene card UI."""
        self.setObjectName("deviceCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Scene name
        self.name_label = QLabel()
        self.name_label.setObjectName("deviceName")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
        
        # Scene state
        self.state_label = QLabel()
        self.state_label.setObjectName("deviceState")
        self.state_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.state_label)
        
        # Activate button
        self.activate_button = QPushButton("Activate Scene")
        self.activate_button.setObjectName("deviceToggle")
        self.activate_button.clicked.connect(self._activate_scene)
        layout.addWidget(self.activate_button)
        
        # Add stretch
        layout.addStretch()
        
        self._update_display()

    def _update_display(self):
        """Update the display with current scene information."""
        # Update name
        friendly_name = self.scene_data.get("attributes", {}).get("friendly_name", self.scene_id)
        self.name_label.setText(friendly_name)
        
        # Update state
        state = self.scene_data.get("state", "unknown")
        self.state_label.setText(f"State: {state}")
        
        # Set state color
        if state == "on":
            self.state_label.setProperty("class", "statusOnline")
        else:
            self.state_label.setProperty("class", "statusOffline")

    def _activate_scene(self):
        """Activate the scene."""
        try:
            success = self.ha_api.call_service("scene", "turn_on", {"entity_id": self.scene_id})
            if success:
                self.scene_activated.emit(self.scene_id)
                QMessageBox.information(self, "Success", f"Scene '{self.name_label.text()}' activated successfully!")
            else:
                QMessageBox.warning(self, "Error", f"Failed to activate scene '{self.name_label.text()}'")
        except Exception as e:
            logger.error(f"Error activating scene {self.scene_id}: {e}")
            QMessageBox.warning(self, "Error", f"Error activating scene: {str(e)}")

    def update_scene_data(self, scene_data: Dict[str, Any]):
        """Update the scene data."""
        self.scene_data = scene_data
        self._update_display()

class ScenesPage(QWidget):
    """Page for managing Home Assistant scenes."""
    
    def __init__(self, ha_api):
        super().__init__()
        self.ha_api = ha_api
        self.scenes: List[Dict[str, Any]] = []
        self.scene_cards: Dict[str, SceneCard] = {}
        
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        """Initialize the scenes page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        self._create_header(layout)
        
        # Main content
        self._create_content(layout)

    def _create_header(self, parent_layout):
        """Create the page header."""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Scenes")
        title_label.setObjectName("pageTitle")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Scene count
        self.scene_count_label = QLabel("0 scenes")
        self.scene_count_label.setStyleSheet("color: #888888; font-size: 14px;")
        header_layout.addWidget(self.scene_count_label)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_button)
        
        parent_layout.addWidget(header_frame)

    def _create_content(self, parent_layout):
        """Create the main content area."""
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content widget
        self.content_widget = QWidget()
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area.setWidget(self.content_widget)
        parent_layout.addWidget(scroll_area)

    def refresh(self):
        """Refresh the scenes list from Home Assistant."""
        try:
            # Skip network calls if offline
            if hasattr(self.ha_api, 'is_connected') and not self.ha_api.is_connected:
                self.scenes = []
                self._update_scene_cards()
                return

            # Get all entities and filter for scenes
            states_data = self.ha_api.get_states()
            self.scenes = []
            
            for state_data in states_data:
                if state_data.get("entity_id", "").startswith("scene."):
                    self.scenes.append(state_data)
            
            # Update scene count
            self.scene_count_label.setText(f"{len(self.scenes)} scenes")
            
            # Update scene cards
            self._update_scene_cards()
            
            logger.info(f"Refreshed {len(self.scenes)} scenes")
            
        except Exception as e:
            logger.error(f"Failed to refresh scenes: {e}")
            QMessageBox.warning(self, "Error", f"Failed to refresh scenes:\n{str(e)}")

    def _update_scene_cards(self):
        """Update the scene cards in the grid."""
        # Clear existing cards
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        self.scene_cards.clear()
        
        # Create scene cards
        row = 0
        col = 0
        max_cols = 4  # Maximum number of columns
        
        for scene_data in self.scenes:
            scene_id = scene_data.get("entity_id", "")
            
            # Create scene card
            scene_card = SceneCard(scene_data, self.ha_api)
            scene_card.scene_activated.connect(self._on_scene_activated)
            self.scene_cards[scene_id] = scene_card
            
            # Add to grid
            self.grid_layout.addWidget(scene_card, row, col)
            
            # Update position
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _on_scene_activated(self, scene_id: str):
        """Handle scene activation."""
        logger.info(f"Scene {scene_id} activated")
        # Could add additional logic here, like updating other UI elements

    def get_page_state(self) -> Dict[str, Any]:
        """Get the current state of the page for preservation."""
        return {
            "scenes_count": len(self.scenes),
            "scene_ids": [scene.get("entity_id") for scene in self.scenes]
        }

    def restore_page_state(self, state: Dict[str, Any]):
        """Restore the page state."""
        # The page state is automatically restored when refresh() is called
        pass
