# ui/widgets/navigation_sidebar.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap
from typing import Dict, List, Optional
import logging
import os

logger = logging.getLogger(__name__)

class NavigationItem:
    """Represents a navigation item."""
    
    def __init__(self, name: str, display_name: str, icon_path: str = "", description: str = ""):
        self.name = name
        self.display_name = display_name
        self.icon_path = icon_path
        self.description = description
        self.enabled = True

class NavigationSidebar(QWidget):
    """Navigation sidebar with tabs for different Home Assistant sections."""
    
    # Signals
    page_requested = pyqtSignal(str)  # page_name
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.navigation_items: List[NavigationItem] = []
        self.current_page: Optional[str] = None
        
        self._init_ui()
        self._setup_navigation_items()

    def _init_ui(self):
        """Initialize the navigation sidebar UI."""
        self.setObjectName("navigationSidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self._create_header(layout)
        
        # Navigation list
        self._create_navigation_list(layout)
        
        # Footer
        self._create_footer(layout)

    def _create_header(self, parent_layout):
        """Create the sidebar header."""
        header_frame = QFrame()
        header_frame.setObjectName("sidebarHeader")
        header_frame.setFixedHeight(80)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setSpacing(8)
        
        # App title
        title_label = QLabel("Home Assistant")
        title_label.setObjectName("appTitle")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Smart Home Control")
        subtitle_label.setObjectName("appSubtitle")
        subtitle_label.setStyleSheet("color: #888888; font-size: 12px;")
        header_layout.addWidget(subtitle_label)
        
        parent_layout.addWidget(header_frame)

    def _create_navigation_list(self, parent_layout):
        """Create the navigation list."""
        # Scroll area for navigation
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(QFrame.NoFrame)
        
        # Navigation list widget
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navigationList")
        self.nav_list.setFrameStyle(QFrame.NoFrame)
        self.nav_list.setSpacing(4)
        
        # Connect selection change
        self.nav_list.currentRowChanged.connect(self._on_navigation_changed)
        
        scroll_area.setWidget(self.nav_list)
        parent_layout.addWidget(scroll_area)

    def _create_footer(self, parent_layout):
        """Create the sidebar footer."""
        footer_frame = QFrame()
        footer_frame.setObjectName("sidebarFooter")
        footer_frame.setFixedHeight(60)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(16, 8, 16, 8)
        footer_layout.setSpacing(8)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        footer_layout.addWidget(self.refresh_button)
        
        # Spacer
        footer_layout.addStretch()
        
        # Version info
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #666666; font-size: 10px;")
        footer_layout.addWidget(version_label)
        
        parent_layout.addWidget(footer_frame)

    def _setup_navigation_items(self):
        """Setup the navigation items for Home Assistant sections."""
        # Define navigation items based on Home Assistant structure
        items = [
            NavigationItem(
                name="overview",
                display_name="Overview",
                icon_path="assets/icons/home-automation.svg",
                description="System overview and quick controls"
            ),
            NavigationItem(
                name="devices",
                display_name="Devices",
                icon_path="assets/icons/lightbulb.svg",
                description="Control lights, switches, and devices"
            ),
            NavigationItem(
                name="automations",
                display_name="Automations",
                icon_path="assets/icons/playlist-play.svg",
                description="Manage automations and rules"
            ),
            NavigationItem(
                name="scenes",
                display_name="Scenes",
                icon_path="assets/icons/power.svg",
                description="Control and manage scenes"
            ),
            NavigationItem(
                name="scripts",
                display_name="Scripts",
                icon_path="assets/icons/cog.svg",
                description="Execute and manage scripts"
            ),
            NavigationItem(
                name="settings",
                display_name="Settings",
                icon_path="assets/icons/cog.svg",
                description="Configure connection and preferences"
            )
        ]
        
        self.navigation_items = items
        self._populate_navigation_list()

    def _populate_navigation_list(self):
        """Populate the navigation list with items."""
        self.nav_list.clear()
        
        for item in self.navigation_items:
            if not item.enabled:
                continue
            
            # Create list item
            list_item = QListWidgetItem(item.display_name)
            list_item.setData(Qt.UserRole, item.name)
            
            # Set tooltip
            list_item.setToolTip(item.description)
            
            # Add icon if available
            if item.icon_path and os.path.exists(item.icon_path):
                try:
                    icon = QIcon(item.icon_path)
                    list_item.setIcon(icon)
                except Exception as e:
                    logger.warning(f"Failed to load icon {item.icon_path}: {e}")
            
            # Set item properties
            list_item.setSizeHint(list_item.sizeHint())
            
            self.nav_list.addItem(list_item)
        
        # Set first item as current if none selected
        if self.nav_list.count() > 0 and not self.current_page:
            self.nav_list.setCurrentRow(0)

    def _on_navigation_changed(self, row: int):
        """Handle navigation selection change."""
        if row >= 0 and row < self.nav_list.count():
            item = self.nav_list.item(row)
            page_name = item.data(Qt.UserRole)
            
            if page_name and page_name != self.current_page:
                self.current_page = page_name
                self.page_requested.emit(page_name)
                logger.info(f"Navigation changed to: {page_name}")

    def set_current_page(self, page_name: str):
        """Set the current page without emitting signals."""
        if page_name == self.current_page:
            return
        
        # Find the item with the matching page name
        for i in range(self.nav_list.count()):
            item = self.nav_list.item(i)
            if item.data(Qt.UserRole) == page_name:
                self.nav_list.setCurrentRow(i)
                self.current_page = page_name
                break

    def get_current_page(self) -> Optional[str]:
        """Get the current page name."""
        return self.current_page

    def enable_page(self, page_name: str, enabled: bool = True):
        """Enable or disable a page."""
        for item in self.navigation_items:
            if item.name == page_name:
                item.enabled = enabled
                break
        
        # Refresh the navigation list
        self._populate_navigation_list()
        
        # If the current page was disabled, switch to the first enabled page
        if not enabled and self.current_page == page_name:
            if self.nav_list.count() > 0:
                first_item = self.nav_list.item(0)
                new_page = first_item.data(Qt.UserRole)
                self.set_current_page(new_page)

    def add_custom_page(self, name: str, display_name: str, icon_path: str = "", description: str = ""):
        """Add a custom page to the navigation."""
        item = NavigationItem(name, display_name, icon_path, description)
        self.navigation_items.append(item)
        self._populate_navigation_list()

    def remove_custom_page(self, page_name: str):
        """Remove a custom page from the navigation."""
        self.navigation_items = [item for item in self.navigation_items if item.name != page_name]
        self._populate_navigation_list()
        
        # If the current page was removed, switch to the first available page
        if self.current_page == page_name:
            if self.nav_list.count() > 0:
                first_item = self.nav_list.item(0)
                new_page = first_item.data(Qt.UserRole)
                self.set_current_page(new_page)

    def get_navigation_items(self) -> List[NavigationItem]:
        """Get all navigation items."""
        return self.navigation_items.copy()

    def set_navigation_items(self, items: List[NavigationItem]):
        """Set the navigation items."""
        self.navigation_items = items
        self._populate_navigation_list()

    def refresh_navigation(self):
        """Refresh the navigation list."""
        self._populate_navigation_list()
