# services/automation_manager.py

import logging
from typing import List, Dict, Any, Optional
from models.automation import Automation, Trigger, Action, Condition

logger = logging.getLogger(__name__)

class AutomationManager:
    """Manager for Home Assistant automations."""
    
    def __init__(self, ha_api):
        self.ha_api = ha_api
        self.automations: List[Automation] = []
    
    def get_automations(self) -> List[Automation]:
        """Get all automations from Home Assistant."""
        try:
            automations_data = self.ha_api.get_automations()
            self.automations = []
            
            for automation_data in automations_data:
                try:
                    automation = Automation.from_dict(automation_data)
                    self.automations.append(automation)
                except Exception as e:
                    logger.warning(f"Failed to parse automation: {e}")
            
            return self.automations
            
        except Exception as e:
            logger.error(f"Failed to get automations: {e}")
            return []
    
    def create_automation(self, automation: Automation) -> bool:
        """Create a new automation."""
        try:
            automation_data = automation.to_dict()
            result = self.ha_api.create_automation(automation_data)
            return result is not None
        except Exception as e:
            logger.error(f"Failed to create automation: {e}")
            return False
    
    def update_automation(self, automation: Automation) -> bool:
        """Update an existing automation."""
        try:
            # TODO: Implement automation update in API
            logger.warning("Automation update not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Failed to update automation: {e}")
            return False
    
    def delete_automation(self, automation_id: str) -> bool:
        """Delete an automation."""
        try:
            # TODO: Implement automation deletion in API
            logger.warning("Automation deletion not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Failed to delete automation: {e}")
            return False
    
    def toggle_automation(self, automation_id: str, enabled: bool) -> bool:
        """Enable or disable an automation."""
        try:
            # TODO: Implement automation toggle in API
            logger.warning("Automation toggle not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Failed to toggle automation: {e}")
            return False
    
    def get_automation_by_id(self, automation_id: str) -> Optional[Automation]:
        """Get an automation by its ID."""
        for automation in self.automations:
            if automation.id == automation_id:
                return automation
        return None
    
    def get_automation_by_alias(self, alias: str) -> Optional[Automation]:
        """Get an automation by its alias."""
        for automation in self.automations:
            if automation.alias == alias:
                return automation
        return None