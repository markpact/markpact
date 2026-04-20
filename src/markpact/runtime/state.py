"""State management for idempotent deployments."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import DeployState


class StateManager:
    """Manages deployment state for idempotency.
    
    Persists state to JSON file for resume capability.
    """
    
    def __init__(self, state_file: str = ".deploy-state.json"):
        self.state_file = Path(state_file)
        self.state: DeployState = DeployState()
        self._load()
    
    def _load(self) -> None:
        """Load state from file."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self.state = DeployState(**data)
            except Exception as e:
                print(f"[markpact] Warning: Failed to load state: {e}")
                self.state = DeployState()
    
    def _save(self) -> None:
        """Save state to file."""
        try:
            self.state_file.write_text(
                self.state.model_dump_json(indent=2)
            )
        except Exception as e:
            print(f"[markpact] Warning: Failed to save state: {e}")
    
    def is_step_done(self, step_id: str) -> bool:
        """Check if step was already completed."""
        return step_id in self.state.steps_done
    
    def mark_step_done(self, step_id: str) -> None:
        """Mark step as completed."""
        if step_id not in self.state.steps_done:
            self.state.steps_done.append(step_id)
            self._save()
    
    def mark_failed(self, step_id: str) -> None:
        """Mark step as failed."""
        self.state.failed_step = step_id
        self._save()
    
    def clear_failed(self) -> None:
        """Clear failed step marker."""
        self.state.failed_step = None
        self._save()
    
    def start_deployment(self) -> None:
        """Mark deployment start."""
        self.state.start_time = datetime.now().isoformat()
        self._save()
    
    def end_deployment(self, status: str = "completed") -> None:
        """Mark deployment end."""
        self.state.end_time = datetime.now().isoformat()
        self._save()
    
    def reset(self) -> None:
        """Clear all state for fresh deployment."""
        self.state = DeployState()
        if self.state_file.exists():
            self.state_file.unlink()
    
    def set_variable(self, name: str, value: any) -> None:
        """Set runtime variable."""
        self.state.variables[name] = value
        self._save()
    
    def get_variable(self, name: str, default: any = None) -> any:
        """Get runtime variable."""
        return self.state.variables.get(name, default)


class ConditionChecker:
    """Check step conditions (when/skip_if)."""
    
    def __init__(self, context: dict):
        self.context = context
        self.runtime = context.get("runtime")
    
    def check_when(self, condition: str) -> bool:
        """Check if 'when' condition is met.
        
        Supported conditions:
        - "docker_not_running" - Docker service not running
        - "file_not_exists:path" - File doesn't exist
        - "dir_not_exists:path" - Directory doesn't exist
        - "container_not_running:name" - Container not running
        """
        if not condition:
            return True
        
        # Parse condition
        parts = condition.split(":", 1)
        cond_type = parts[0]
        arg = parts[1] if len(parts) > 1 else ""
        
        # Check various conditions
        if cond_type == "docker_not_running":
            return not self._is_docker_running()
        elif cond_type == "file_not_exists":
            return not Path(arg).exists()
        elif cond_type == "dir_not_exists":
            return not Path(arg).is_dir()
        elif cond_type == "container_not_running":
            return not self._is_container_running(arg)
        elif cond_type == "always":
            return True
        else:
            # Unknown condition - allow execution
            return True
    
    def check_skip_if(self, condition: str) -> bool:
        """Check if 'skip_if' condition is met (should skip step)."""
        if not condition:
            return False
        
        # Parse condition (inverse logic from when)
        parts = condition.split(":", 1)
        cond_type = parts[0]
        arg = parts[1] if len(parts) > 1 else ""
        
        if cond_type == "docker_running":
            return self._is_docker_running()
        elif cond_type == "file_exists":
            return Path(arg).exists()
        elif cond_type == "dir_exists":
            return Path(arg).is_dir()
        elif cond_type == "container_running":
            return self._is_container_running(arg)
        elif cond_type == "step_completed":
            state = self.context.get("state_manager")
            if state:
                return state.is_step_done(arg)
            return False
        else:
            return False
    
    def _is_docker_running(self) -> bool:
        """Check if Docker is running."""
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _is_container_running(self, name: str) -> bool:
        """Check if Docker container is running."""
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return name in result.stdout
        except:
            return False
