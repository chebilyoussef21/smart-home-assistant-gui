# models/automation.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum

class AutomationMode(Enum):
    """Automation mode enumeration."""
    SINGLE = "single"
    RESTART = "restart"
    QUEUE = "queue"
    PARALLEL = "parallel"

@dataclass
class Trigger:
    """Represents an automation trigger."""
    
    platform: str  # e.g., "state", "time", "event"
    entity_id: Optional[str] = None
    to: Optional[str] = None
    from_: Optional[str] = None
    for_: Optional[str] = None
    at: Optional[str] = None
    event: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trigger to dictionary."""
        data = {"platform": self.platform}
        
        if self.entity_id:
            data["entity_id"] = self.entity_id
        if self.to:
            data["to"] = self.to
        if self.from_:
            data["from"] = self.from_
        if self.for_:
            data["for"] = self.for_
        if self.at:
            data["at"] = self.at
        if self.event:
            data["event"] = self.event
            
        data.update(self.additional_data)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trigger':
        """Create trigger from dictionary."""
        return cls(
            platform=data["platform"],
            entity_id=data.get("entity_id"),
            to=data.get("to"),
            from_=data.get("from"),
            for_=data.get("for"),
            at=data.get("at"),
            event=data.get("event"),
            additional_data={k: v for k, v in data.items() 
                           if k not in ["platform", "entity_id", "to", "from", "for", "at", "event"]}
        )

@dataclass
class Action:
    """Represents an automation action."""
    
    service: str  # e.g., "light.turn_on"
    entity_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def domain(self) -> str:
        """Get the domain of the service."""
        return self.service.split('.')[0]
    
    @property
    def service_name(self) -> str:
        """Get the service name."""
        return self.service.split('.')[1] if '.' in self.service else self.service
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary."""
        data = {"service": self.service}
        
        if self.entity_id:
            data["entity_id"] = self.entity_id
        if self.data:
            data["data"] = self.data
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create action from dictionary."""
        return cls(
            service=data["service"],
            entity_id=data.get("entity_id"),
            data=data.get("data", {})
        )

@dataclass
class Condition:
    """Represents an automation condition."""
    
    condition: str  # e.g., "state", "time", "numeric_state"
    entity_id: Optional[str] = None
    state: Optional[str] = None
    above: Optional[float] = None
    below: Optional[float] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert condition to dictionary."""
        data = {"condition": self.condition}
        
        if self.entity_id:
            data["entity_id"] = self.entity_id
        if self.state:
            data["state"] = self.state
        if self.above is not None:
            data["above"] = self.above
        if self.below is not None:
            data["below"] = self.below
            
        data.update(self.additional_data)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition':
        """Create condition from dictionary."""
        return cls(
            condition=data["condition"],
            entity_id=data.get("entity_id"),
            state=data.get("state"),
            above=data.get("above"),
            below=data.get("below"),
            additional_data={k: v for k, v in data.items() 
                           if k not in ["condition", "entity_id", "state", "above", "below"]}
        )

@dataclass
class Automation:
    """Represents a Home Assistant automation."""
    
    alias: str
    description: Optional[str] = None
    trigger: List[Trigger] = field(default_factory=list)
    action: List[Action] = field(default_factory=list)
    condition: List[Condition] = field(default_factory=list)
    mode: AutomationMode = AutomationMode.SINGLE
    max_exceeded: str = "silent"
    enabled: bool = True
    id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert automation to dictionary."""
        data = {
            "alias": self.alias,
            "mode": self.mode.value,
            "max_exceeded": self.max_exceeded,
            "enabled": self.enabled
        }
        
        if self.description:
            data["description"] = self.description
        if self.trigger:
            data["trigger"] = [t.to_dict() for t in self.trigger]
        if self.action:
            data["action"] = [a.to_dict() for a in self.action]
        if self.condition:
            data["condition"] = [c.to_dict() for c in self.condition]
        if self.id:
            data["id"] = self.id
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Automation':
        """Create automation from dictionary."""
        triggers = []
        if "trigger" in data:
            triggers = [Trigger.from_dict(t) for t in data["trigger"]]
            
        actions = []
        if "action" in data:
            actions = [Action.from_dict(a) for a in data["action"]]
            
        conditions = []
        if "condition" in data:
            conditions = [Condition.from_dict(c) for c in data["condition"]]

        if "attributes" in data:
            # If data comes from /api/states, extract alias from attributes
            attributes = data.get("attributes", {})
            if "friendly_name" in attributes:
                alias = attributes.get("friendly_name", data.get("entity_id"))

        return cls(
            # alias=data["alias"],
            alias = alias,
            description=data.get("description"),
            trigger=triggers,
            action=actions,
            condition=conditions,
            mode=AutomationMode(data.get("mode", "single")),
            max_exceeded=data.get("max_exceeded", "silent"),
            enabled=data.get("enabled", True),
            id=data.get("id")
        )
