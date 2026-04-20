"""Pydantic models for markpact runtime with validation."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class Step(BaseModel):
    """Pydantic-validated deployment step.
    
    Includes idempotency conditions (when/skip_if), retry logic, rollback.
    """
    id: str = Field(..., description="Unique step identifier")
    action: str = Field(..., description="Executor action type")
    description: str = Field(default="", description="Human-readable description")
    command: str = Field(default="", description="Command to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")
    risk: str = Field(default="low", description="Risk level: low/medium/high")
    timeout: int = Field(default=300, ge=1, description="Timeout in seconds")
    retry: int = Field(default=0, ge=0, description="Number of retries on failure")
    
    # Idempotency conditions
    when: Optional[str] = Field(default=None, description="Condition to run: 'docker_not_running'")
    skip_if: Optional[str] = Field(default=None, description="Condition to skip: 'container_exists'")
    check_cmd: Optional[str] = Field(default=None, description="v3: Check command for true idempotency")
    
    # Rollback support
    rollback_cmd: Optional[str] = Field(default=None, description="Command to rollback this step")

    @validator("risk")
    def validate_risk(cls, v):
        allowed = {"low", "medium", "high"}
        if v not in allowed:
            raise ValueError(f"risk must be one of {allowed}, got '{v}'")
        return v

    @validator("timeout", "retry")
    def positive_int(cls, v):
        if v < 0:
            raise ValueError("must be >= 0")
        return v

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Step":
        """Create Step from dictionary (YAML/TOML/JSON)."""
        # Separate standard fields from extra params
        standard_fields = {
            'id', 'action', 'description', 'command', 'risk', 
            'timeout', 'retry', 'when', 'skip_if', 'rollback_cmd'
        }
        
        params = {k: v for k, v in data.items() if k not in standard_fields}
        
        return cls(
            id=data.get("id", "unnamed"),
            action=data.get("action", "shell"),
            description=data.get("description", ""),
            command=data.get("command", ""),
            params=params,
            risk=data.get("risk", "low"),
            timeout=data.get("timeout", 300),
            retry=data.get("retry", 0),
            when=data.get("when"),
            skip_if=data.get("skip_if"),
            rollback_cmd=data.get("rollback_cmd"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Step to dictionary."""
        result = {"id": self.id, "action": self.action}
        
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
        if self.retry:
            result["retry"] = self.retry
        if self.when:
            result["when"] = self.when
        if self.skip_if:
            result["skip_if"] = self.skip_if
        if self.rollback_cmd:
            result["rollback_cmd"] = self.rollback_cmd
        
        return result


class DeploymentConfig(BaseModel):
    """Deployment configuration with validation."""
    name: str = Field(default="unnamed", description="Deployment name")
    version: str = Field(default="0.0.0", description="Deployment version")
    description: str = Field(default="", description="Deployment description")
    target: Dict[str, Any] = Field(default_factory=dict, description="Target configuration")
    
    # Plugin configuration
    plugins: List[Dict[str, Any]] = Field(default_factory=list, description="Plugin paths/modules")


class DeployState(BaseModel):
    """Deployment state for idempotency tracking."""
    steps_done: List[str] = Field(default_factory=list, description="Completed step IDs")
    step_hashes: Dict[str, str] = Field(default_factory=dict, description="v3: Step definition hashes")
    failed_step: Optional[str] = Field(default=None, description="Failed step ID")
    start_time: Optional[str] = Field(default=None, description="Deployment start timestamp")
    end_time: Optional[str] = Field(default=None, description="Deployment end timestamp")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Runtime variables")


class StepResult(BaseModel):
    """Result of step execution with structured logging."""
    step_id: str
    status: str = Field(default="pending", description="pending/running/success/failed/skipped/timeout")
    duration: float = Field(default=0.0, ge=0)
    output: str = Field(default="")
    error: Optional[str] = Field(default=None)
    attempts: int = Field(default=1, ge=1)
    timestamp: Optional[str] = Field(default=None)

    @property
    def success(self) -> bool:
        """Check if step succeeded."""
        return self.status == "success"

    @property
    def failed(self) -> bool:
        """Check if step failed."""
        return self.status in ("failed", "timeout")


class ExecutionSummary(BaseModel):
    """Summary of full deployment execution."""
    total_steps: int
    succeeded: int
    failed: int
    skipped: int
    total_duration: float
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str = Field(default="pending", description="pending/success/failed")
