# models/entity.py

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class EntityState(Enum):
    """Entity state enumeration."""
    ON = "on"
    OFF = "off"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"

@dataclass
class Entity:
    """Represents a Home Assistant entity."""
    
    entity_id: str
    state: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    last_changed: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    @property
    def friendly_name(self) -> str:
        """Get the friendly name of the entity."""
        return self.attributes.get("friendly_name", self.entity_id)
    
    @property
    def domain(self) -> str:
        """Get the domain of the entity (e.g., 'light', 'switch')."""
        return self.entity_id.split('.')[0]
    
    @property
    def object_id(self) -> str:
        """Get the object ID of the entity."""
        return self.entity_id.split('.')[1] if '.' in self.entity_id else self.entity_id
    
    @property
    def is_on(self) -> bool:
        """Check if the entity is in 'on' state."""
        return self.state.lower() == "on"
    
    @property
    def is_off(self) -> bool:
        """Check if the entity is in 'off' state."""
        return self.state.lower() == "off"
    
    @property
    def is_available(self) -> bool:
        """Check if the entity is available."""
        return self.state.lower() != "unavailable"
    
    @property
    def icon(self) -> str:
        """Get the icon for the entity."""
        return self.attributes.get("icon", "mdi:help-circle")
    
    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Get the unit of measurement if applicable."""
        return self.attributes.get("unit_of_measurement")
    
    @property
    def device_class(self) -> Optional[str]:
        """Get the device class if applicable."""
        return self.attributes.get("device_class")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "entity_id": self.entity_id,
            "state": self.state,
            "attributes": self.attributes,
            "last_changed": self.last_changed.isoformat() if self.last_changed else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Create entity from dictionary."""
        last_changed = None
        last_updated = None
        
        if data.get("last_changed"):
            try:
                last_changed = datetime.fromisoformat(data["last_changed"].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
                
        if data.get("last_updated"):
            try:
                last_updated = datetime.fromisoformat(data["last_updated"].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        return cls(
            entity_id=data["entity_id"],
            state=data["state"],
            attributes=data.get("attributes", {}),
            last_changed=last_changed,
            last_updated=last_updated
        )
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update entity from dictionary."""
        self.state = data.get("state", self.state)
        self.attributes.update(data.get("attributes", {}))
        
        if data.get("last_changed"):
            try:
                self.last_changed = datetime.fromisoformat(data["last_changed"].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
                
        if data.get("last_updated"):
            try:
                self.last_updated = datetime.fromisoformat(data["last_updated"].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
