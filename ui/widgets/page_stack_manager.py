# ui/widgets/page_stack_manager.py

from PyQt5.QtWidgets import QStackedWidget, QWidget
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class PageStackManager(QObject):
    """Manages a stack of pages with state preservation."""
    
    # Signals
    page_changed = pyqtSignal(str)  # page_name
    page_state_saved = pyqtSignal(str, dict)  # page_name, state
    page_state_restored = pyqtSignal(str, dict)  # page_name, state
    
    def __init__(self, stacked_widget: QStackedWidget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.pages: Dict[str, QWidget] = {}
        self.page_states: Dict[str, Dict[str, Any]] = {}
        self.current_page_name: Optional[str] = None
        self.page_history: List[str] = []
        
        # Connect to stacked widget signals
        self.stacked_widget.currentChanged.connect(self._on_current_changed)

    def add_page(self, name: str, widget: QWidget) -> bool:
        """Add a page to the stack."""
        try:
            if name in self.pages:
                logger.warning(f"Page '{name}' already exists, replacing it")
                self.remove_page(name)
            
            # Add to stacked widget
            index = self.stacked_widget.addWidget(widget)
            self.pages[name] = widget
            
            # Initialize page state
            self.page_states[name] = {}
            
            logger.info(f"Added page '{name}' at index {index}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add page '{name}': {e}")
            return False

    def remove_page(self, name: str) -> bool:
        """Remove a page from the stack."""
        try:
            if name not in self.pages:
                logger.warning(f"Page '{name}' not found")
                return False
            
            widget = self.pages[name]
            
            # Save state before removing
            self._save_page_state(name)
            
            # Remove from stacked widget
            self.stacked_widget.removeWidget(widget)
            
            # Remove from our tracking
            del self.pages[name]
            if name in self.page_states:
                del self.page_states[name]
            
            # Update history
            if name in self.page_history:
                self.page_history.remove(name)
            
            # If this was the current page, switch to the first available page
            if self.current_page_name == name:
                if self.pages:
                    first_page = next(iter(self.pages.keys()))
                    self.switch_to_page(first_page)
                else:
                    self.current_page_name = None
            
            logger.info(f"Removed page '{name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove page '{name}': {e}")
            return False

    def switch_to_page(self, name: str) -> bool:
        """Switch to a specific page."""
        try:
            if name not in self.pages:
                logger.error(f"Page '{name}' not found")
                return False
            
            # Save current page state
            if self.current_page_name:
                self._save_page_state(self.current_page_name)
            
            # Get the widget and switch to it
            widget = self.pages[name]
            index = self.stacked_widget.indexOf(widget)
            
            if index == -1:
                logger.error(f"Widget for page '{name}' not found in stacked widget")
                return False
            
            # Switch to the page
            self.stacked_widget.setCurrentIndex(index)
            self.current_page_name = name
            
            # Add to history
            if name not in self.page_history:
                self.page_history.append(name)
            
            # Restore page state
            self._restore_page_state(name)
            
            # Emit signal
            self.page_changed.emit(name)
            
            logger.info(f"Switched to page '{name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to page '{name}': {e}")
            return False

    def go_back(self) -> bool:
        """Go back to the previous page in history."""
        if len(self.page_history) < 2:
            logger.warning("No previous page in history")
            return False
        
        # Remove current page from history
        current = self.page_history.pop()
        
        # Get previous page
        previous = self.page_history[-1]
        
        # Switch to previous page
        return self.switch_to_page(previous)

    def get_current_page_name(self) -> Optional[str]:
        """Get the name of the current page."""
        return self.current_page_name

    def get_page_names(self) -> List[str]:
        """Get a list of all page names."""
        return list(self.pages.keys())

    def get_page_widget(self, name: str) -> Optional[QWidget]:
        """Get the widget for a specific page."""
        return self.pages.get(name)

    def refresh_current_page(self):
        """Refresh the current page if it has a refresh method."""
        if self.current_page_name and self.current_page_name in self.pages:
            widget = self.pages[self.current_page_name]
            if hasattr(widget, 'refresh') and callable(getattr(widget, 'refresh')):
                try:
                    widget.refresh()
                    logger.info(f"Refreshed page '{self.current_page_name}'")
                except Exception as e:
                    logger.error(f"Failed to refresh page '{self.current_page_name}': {e}")

    def save_all_states(self):
        """Save the state of all pages."""
        for page_name in self.pages.keys():
            self._save_page_state(page_name)

    def restore_all_states(self):
        """Restore the state of all pages."""
        for page_name in self.pages.keys():
            self._restore_page_state(page_name)

    def _save_page_state(self, page_name: str):
        """Save the state of a specific page."""
        try:
            if page_name not in self.pages:
                return
            
            widget = self.pages[page_name]
            
            # Check if the widget has a get_page_state method
            if hasattr(widget, 'get_page_state') and callable(getattr(widget, 'get_page_state')):
                state = widget.get_page_state()
                self.page_states[page_name] = state
                self.page_state_saved.emit(page_name, state)
                logger.debug(f"Saved state for page '{page_name}'")
            
        except Exception as e:
            logger.error(f"Failed to save state for page '{page_name}': {e}")

    def _restore_page_state(self, page_name: str):
        """Restore the state of a specific page."""
        try:
            if page_name not in self.pages:
                return
            
            widget = self.pages[page_name]
            state = self.page_states.get(page_name, {})
            
            # Check if the widget has a restore_page_state method
            if hasattr(widget, 'restore_page_state') and callable(getattr(widget, 'restore_page_state')):
                widget.restore_page_state(state)
                self.page_state_restored.emit(page_name, state)
                logger.debug(f"Restored state for page '{page_name}'")
            
        except Exception as e:
            logger.error(f"Failed to restore state for page '{page_name}': {e}")

    def _on_current_changed(self, index: int):
        """Handle when the current widget in the stacked widget changes."""
        widget = self.stacked_widget.widget(index)
        if widget:
            # Find the page name for this widget
            for page_name, page_widget in self.pages.items():
                if page_widget == widget:
                    if self.current_page_name != page_name:
                        self.current_page_name = page_name
                        logger.debug(f"Current page changed to '{page_name}'")
                    break

    def get_page_state(self, page_name: str) -> Dict[str, Any]:
        """Get the saved state for a specific page."""
        return self.page_states.get(page_name, {})

    def set_page_state(self, page_name: str, state: Dict[str, Any]):
        """Set the state for a specific page."""
        self.page_states[page_name] = state

    def clear_page_state(self, page_name: str):
        """Clear the saved state for a specific page."""
        if page_name in self.page_states:
            del self.page_states[page_name]

    def clear_all_states(self):
        """Clear all saved page states."""
        self.page_states.clear()

    def get_page_history(self) -> List[str]:
        """Get the page navigation history."""
        return self.page_history.copy()

    def clear_history(self):
        """Clear the page navigation history."""
        self.page_history.clear()
