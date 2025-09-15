# ui/widgets/scripts_page.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QFrame, QScrollArea, QGroupBox, QListWidget,
    QListWidgetItem, QMessageBox, QTextEdit, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ScriptCard(QWidget):
    """Widget for displaying and controlling a script."""
    
    script_executed = pyqtSignal(str)  # script_id
    
    def __init__(self, script_data: Dict[str, Any], ha_api):
        super().__init__()
        self.script_data = script_data
        self.ha_api = ha_api
        self.script_id = script_data.get("entity_id", "")
        
        self._init_ui()

    def _init_ui(self):
        """Initialize the script card UI."""
        self.setObjectName("deviceCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Script name
        self.name_label = QLabel()
        self.name_label.setObjectName("deviceName")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
        
        # Script state
        self.state_label = QLabel()
        self.state_label.setObjectName("deviceState")
        self.state_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.state_label)
        
        # Script description
        self.description_label = QLabel()
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        # Execute button
        self.execute_button = QPushButton("Execute Script")
        self.execute_button.setObjectName("deviceToggle")
        self.execute_button.clicked.connect(self._execute_script)
        layout.addWidget(self.execute_button)
        
        # Add stretch
        layout.addStretch()
        
        self._update_display()

    def _update_display(self):
        """Update the display with current script information."""
        # Update name
        friendly_name = self.script_data.get("attributes", {}).get("friendly_name", self.script_id)
        self.name_label.setText(friendly_name)
        
        # Update state
        state = self.script_data.get("state", "unknown")
        self.state_label.setText(f"State: {state}")
        
        # Set state color
        if state == "on":
            self.state_label.setProperty("class", "statusOnline")
        elif state == "off":
            self.state_label.setProperty("class", "statusOffline")
        else:
            self.state_label.setProperty("class", "statusUnknown")
        
        # Update description
        description = self.script_data.get("attributes", {}).get("description", "")
        if description:
            self.description_label.setText(description)
        else:
            self.description_label.setText("No description available")
        
        # Update button state
        if state == "on":
            self.execute_button.setText("Running...")
            self.execute_button.setEnabled(False)
        else:
            self.execute_button.setText("Execute Script")
            self.execute_button.setEnabled(True)

    def _execute_script(self):
        """Execute the script."""
        try:
            success = self.ha_api.call_service("script", "turn_on", {"entity_id": self.script_id})
            if success:
                self.script_executed.emit(self.script_id)
                QMessageBox.information(self, "Success", f"Script '{self.name_label.text()}' executed successfully!")
                # Update button state
                self.execute_button.setText("Running...")
                self.execute_button.setEnabled(False)
            else:
                QMessageBox.warning(self, "Error", f"Failed to execute script '{self.name_label.text()}'")
        except Exception as e:
            logger.error(f"Error executing script {self.script_id}: {e}")
            QMessageBox.warning(self, "Error", f"Error executing script: {str(e)}")

    def update_script_data(self, script_data: Dict[str, Any]):
        """Update the script data."""
        self.script_data = script_data
        self._update_display()

class ScriptDetailsDialog(QDialog):
    """Dialog for viewing script details."""
    
    def __init__(self, script_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.script_data = script_data
        self.setWindowTitle(f"Script Details: {script_data.get('attributes', {}).get('friendly_name', 'Unknown')}")
        self.setMinimumSize(500, 400)
        
        self._init_ui()

    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        # Name
        name_label = QLabel(self.script_data.get("attributes", {}).get("friendly_name", "Unknown"))
        basic_layout.addRow("Name:", name_label)
        
        # Entity ID
        entity_id_label = QLabel(self.script_data.get("entity_id", "Unknown"))
        basic_layout.addRow("Entity ID:", entity_id_label)
        
        # State
        state_label = QLabel(self.script_data.get("state", "Unknown"))
        basic_layout.addRow("State:", state_label)
        
        # Description
        description = self.script_data.get("attributes", {}).get("description", "No description")
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        basic_layout.addRow("Description:", description_label)
        
        layout.addWidget(basic_group)
        
        # Script content (if available)
        content_group = QGroupBox("Script Content")
        content_layout = QVBoxLayout(content_group)
        
        # Try to get script content from attributes
        script_content = self.script_data.get("attributes", {})
        content_text = ""
        
        if "sequence" in script_content:
            content_text = "Sequence:\n"
            for i, action in enumerate(script_content["sequence"], 1):
                content_text += f"{i}. {action}\n"
        else:
            content_text = "Script content not available in entity attributes."
        
        content_display = QTextEdit()
        content_display.setPlainText(content_text)
        content_display.setReadOnly(True)
        content_layout.addWidget(content_display)
        
        layout.addWidget(content_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

class ScriptsPage(QWidget):
    """Page for managing Home Assistant scripts."""
    
    def __init__(self, ha_api):
        super().__init__()
        self.ha_api = ha_api
        self.scripts: List[Dict[str, Any]] = []
        self.script_cards: Dict[str, ScriptCard] = {}
        
        self._init_ui()
        QTimer.singleShot(0, self.refresh)

    def _init_ui(self):
        """Initialize the scripts page UI."""
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
        title_label = QLabel("Scripts")
        title_label.setObjectName("pageTitle")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Script count
        self.script_count_label = QLabel("0 scripts")
        self.script_count_label.setStyleSheet("color: #888888; font-size: 14px;")
        header_layout.addWidget(self.script_count_label)
        
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
        """Refresh the scripts list from Home Assistant."""
        try:
            # Skip network calls if offline
            if hasattr(self.ha_api, 'is_connected') and not self.ha_api.is_connected:
                self.scripts = []
                self._update_script_cards()
                return

            # Get all entities and filter for scripts
            states_data = self.ha_api.get_states()
            self.scripts = []
            
            for state_data in states_data:
                if state_data.get("entity_id", "").startswith("script."):
                    self.scripts.append(state_data)
            
            # Update script count
            self.script_count_label.setText(f"{len(self.scripts)} scripts")
            
            # Update script cards
            self._update_script_cards()
            
            logger.info(f"Refreshed {len(self.scripts)} scripts")
            
        except Exception as e:
            logger.error(f"Failed to refresh scripts: {e}")
            QMessageBox.warning(self, "Error", f"Failed to refresh scripts:\n{str(e)}")

    def _update_script_cards(self):
        """Update the script cards in the grid."""
        # Clear existing cards
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        self.script_cards.clear()
        
        # Create script cards
        row = 0
        col = 0
        max_cols = 3  # Maximum number of columns (scripts can be wider)
        
        for script_data in self.scripts:
            script_id = script_data.get("entity_id", "")
            
            # Create script card
            script_card = ScriptCard(script_data, self.ha_api)
            script_card.script_executed.connect(self._on_script_executed)
            self.script_cards[script_id] = script_card
            
            # Add to grid
            self.grid_layout.addWidget(script_card, row, col)
            
            # Update position
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _on_script_executed(self, script_id: str):
        """Handle script execution."""
        logger.info(f"Script {script_id} executed")
        # Could add additional logic here, like updating other UI elements

    def get_page_state(self) -> Dict[str, Any]:
        """Get the current state of the page for preservation."""
        return {
            "scripts_count": len(self.scripts),
            "script_ids": [script.get("entity_id") for script in self.scripts]
        }

    def restore_page_state(self, state: Dict[str, Any]):
        """Restore the page state."""
        # The page state is automatically restored when refresh() is called
        pass
