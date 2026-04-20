"""Step definitions and results."""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional


class StepStatus(Enum):
    """Status of step execution."""
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()
    TIMEOUT = auto()


@dataclass
class Step:
    """A deployment step.
    
    Attributes:
        id: Unique step identifier
        action: Executor to use (shell, rsync, docker, etc.)
        description: Human-readable description
        command: Command to execute (for shell actions)
        params: Additional parameters
        risk: Risk level (low, medium, high)
        timeout: Maximum execution time in seconds
        retries: Number of retries on failure
    """
    id: str
    action: str
    description: str = ""
    command: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    risk: str = "low"
    timeout: int = 300
    retries: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Step":
        """Create Step from dictionary (YAML/TOML/JSON)."""
        # Handle extra_fields that map to params
        params = {}
        standard_fields = {'id', 'action', 'description', 'command', 'risk', 'timeout', 'retries'}
        
        for key, value in data.items():
            if key not in standard_fields:
                params[key] = value
        
        return cls(
            id=data.get("id", "unnamed"),
            action=data.get("action", "shell"),
            description=data.get("description", ""),
            command=data.get("command", ""),
            params=params,
            risk=data.get("risk", "low"),
            timeout=data.get("timeout", 300),
            retries=data.get("retries", 0),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Step to dictionary."""
        result = {
            "id": self.id,
            "action": self.action,
        }
        
        if self.description:
            result["description"] = self.description
        if self.command:
            result["command"] = self.command
        if self.params:
            result.update(self.params)
        if self.risk != "low":
            result["risk"] = self.risk
        if self.timeout != 300:
            result["timeout"] = self.timeout
        if self.retries:
            result["retries"] = self.retries
        
        return result


@dataclass
class StepResult:
    """Result of step execution."""
    step_id: str
    status: StepStatus
    duration: float
    output: str = ""
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if step succeeded."""
        return self.status == StepStatus.SUCCESS
    
    def __str__(self) -> str:
        if self.success:
            return f"✓ {self.step_id} ({self.duration:.1f}s)"
        else:
            return f"✗ {self.step_id}: {self.error}"
