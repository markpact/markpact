"""Core runtime v2 with idempotency, SSH persistence, retry, rollback."""
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from .parser import MarkpactParser, Block, BlockType
from .executors import ExecutorRegistry
from .plugins import PluginLoader
from .models import Step, StepResult, DeployState, DeploymentConfig
from .state import StateManager, ConditionChecker
from .ssh_manager import SSHSessionManager
from .exceptions import ExecutionError, ValidationError


@dataclass
class RuntimeConfig:
    """Configuration for the runtime."""
    dry_run: bool = False
    verbose: bool = True
    stop_on_error: bool = True
    plugin_paths: List[Path] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    timeout_default: int = 300
    
    # SSH defaults
    ssh_key: Optional[str] = None
    ssh_timeout: int = 30
    
    # Docker defaults  
    docker_timeout: int = 600
    
    # State management
    state_file: str = ".deploy-state.json"
    reset_state: bool = False
    
    # Retry defaults
    retry_default: int = 0
    retry_backoff: bool = True


class RuntimeV2:
    """Production-grade runtime for executing markpact deployments.
    
    Features:
    - Pydantic validation
    - Idempotency with state persistence
    - Persistent SSH sessions
    - Retry with exponential backoff
    - Automatic rollback on failure
    - Condition checking (when/skip_if)
    
    Example:
        runtime = RuntimeV2("deployment.md", config=RuntimeConfig(dry_run=True))
        result = runtime.execute()
    """
    
    def __init__(
        self,
        file_path: str,
        config: Optional[RuntimeConfig] = None,
        **kwargs
    ):
        """Initialize runtime."""
        self.file_path = Path(file_path)
        self.config = config or RuntimeConfig()
        
        # Override with kwargs
        for key, value in kwargs.items():
            setattr(self.config, key, value)
        
        # Components
        self.parser = MarkpactParser()
        self.executors = ExecutorRegistry()
        self.plugins = PluginLoader()
        
        # State management
        self.state_manager = StateManager(self.config.state_file)
        if self.config.reset_state:
            self.state_manager.reset()
        
        # SSH session management
        self._ssh_sessions: Dict[str, SSHSessionManager] = {}
        
        # Execution data
        self.config_data: Dict[str, Any] = {}
        self.steps: List[Step] = []
        self.rollback_steps: List[Step] = []
        self.results: List[StepResult] = []
        self.variables: Dict[str, Any] = {}
        
        # Load plugins
        self._load_plugins()
    
    def _load_plugins(self) -> None:
        """Load plugins from configured paths."""
        for path in self.config.plugin_paths:
            self.plugins.load_from_path(path)
        
        # Also check for plugins specified in environment
        import os
        env_paths = os.environ.get("MARKPACT_PLUGINS", "")
        if env_paths:
            for path in env_paths.split(":"):
                if path.strip():
                    self.plugins.load_from_path(Path(path.strip()))
    
    def parse(self) -> List[Block]:
        """Parse the markdown file into blocks."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Migration file not found: {self.file_path}")
        
        content = self.file_path.read_text(encoding='utf-8')
        blocks = self.parser.parse(content)
        
        if self.config.verbose:
            print(f"[markpact] Parsed {len(blocks)} blocks from {self.file_path.name}")
        
        return blocks
    
    def execute(self, step_filter: Optional[str] = None) -> bool:
        """Execute all or filtered steps with idempotency, retry, rollback."""
        blocks = self.parse()
        
        # Process blocks
        self._process_blocks(blocks)
        
        # Filter steps if requested
        steps_to_run = self.steps
        if step_filter:
            import re
            pattern = re.compile(step_filter)
            steps_to_run = [s for s in steps_to_run if pattern.search(s.id)]
        
        if self.config.verbose:
            print(f"\n[markpact] Executing {len(steps_to_run)} steps")
            print(f"[markpact] State: {len(self.state_manager.state.steps_done)} done")
            if self.config.dry_run:
                print("[markpact] DRY RUN - no changes will be made\n")
            else:
                print()
        
        # Mark deployment start
        self.state_manager.start_deployment()
        
        # Execute steps
        success = True
        failed_step = None
        
        for step in steps_to_run:
            # Check idempotency - skip if already done
            if self.state_manager.is_step_done(step.id):
                if self.config.verbose:
                    print(f"  → [{step.id}] [SKIP - already completed]")
                self.results.append(StepResult(
                    step_id=step.id,
                    status="skipped",
                    duration=0,
                    output="Step already completed"
                ))
                continue
            
            # Check conditions
            if not self._should_run_step(step):
                if self.config.verbose:
                    print(f"  → [{step.id}] [SKIP - condition not met]")
                self.results.append(StepResult(
                    step_id=step.id,
                    status="skipped",
                    duration=0,
                    output="Condition not met"
                ))
                continue
            
            # Execute with retry
            result = self._execute_step_with_retry(step)
            self.results.append(result)
            
            if result.success:
                self.state_manager.mark_step_done(step.id)
            else:
                success = False
                failed_step = step
                if self.config.stop_on_error:
                    break
        
        # Handle failure - rollback
        if not success and failed_step:
            self._rollback(failed_step)
        
        # Mark deployment end
        self.state_manager.end_deployment("success" if success else "failed")
        
        # Summary
        self._print_summary()
        
        return success
    
    def _should_run_step(self, step: Step) -> bool:
        """Check if step should run based on conditions."""
        context = {
            "runtime": self,
            "state_manager": self.state_manager,
            "variables": self.variables,
        }
        
        checker = ConditionChecker(context)
        
        # Check skip_if condition
        if step.skip_if and checker.check_skip_if(step.skip_if):
            return False
        
        # Check when condition
        if step.when and not checker.check_when(step.when):
            return False
        
        return True
    
    def _execute_step_with_retry(self, step: Step) -> StepResult:
        """Execute step with retry logic and exponential backoff."""
        max_retries = step.retry or self.config.retry_default
        last_error = None
        
        for attempt in range(max_retries + 1):
            result = self._execute_step_single(step, attempt + 1)
            
            if result.success:
                # Store attempt count in result
                result.attempts = attempt + 1
                return result
            
            last_error = result.error
            
            if attempt < max_retries:
                # Exponential backoff
                delay = 2 ** attempt if self.config.retry_backoff else 1
                if self.config.verbose:
                    print(f"     [RETRY {attempt + 1}/{max_retries}] in {delay}s...")
                time.sleep(delay)
        
        # All retries failed
        return StepResult(
            step_id=step.id,
            status="failed",
            duration=sum(r.duration for r in self.results if r.step_id == step.id),
            error=f"Failed after {max_retries + 1} attempts: {last_error}",
            attempts=max_retries + 1
        )
    
    def _execute_step_single(self, step: Step, attempt: int) -> StepResult:
        """Execute a single step attempt."""
        start_time = time.time()
        
        if self.config.verbose:
            prefix = f"  → [{step.id}]" if attempt == 1 else f"     [Attempt {attempt}]"
            print(f"{prefix} {step.description}")
            if step.risk != "low":
                print(f"     (risk: {step.risk}, timeout: {step.timeout}s)")
        
        if self.config.dry_run:
            return StepResult(
                step_id=step.id,
                status="success",
                duration=0,
                output="[DRY RUN] Would execute: " + step.action
            )
        
        # Get executor
        executor = self.executors.get(step.action)
        if not executor:
            return StepResult(
                step_id=step.id,
                status="failed",
                duration=time.time() - start_time,
                error=f"No executor for action: {step.action}"
            )
        
        # Execute
        try:
            context = {
                "variables": self.variables,
                "config": self.config,
                "runtime": self,
                "ssh_manager": self._get_ssh_manager,
            }
            
            output = executor.execute(step, context)
            duration = time.time() - start_time
            
            if self.config.verbose:
                print(f"     ✓ Success ({duration:.1f}s)")
            
            return StepResult(
                step_id=step.id,
                status="success",
                duration=duration,
                output=output,
                attempts=attempt
            )
            
        except Exception as e:
            duration = time.time() - start_time
            
            if self.config.verbose:
                print(f"     ✗ Failed: {e}")
            
            return StepResult(
                step_id=step.id,
                status="failed",
                duration=duration,
                error=str(e),
                attempts=attempt
            )
    
    def _rollback(self, failed_step: Step) -> None:
        """Execute rollback steps after failure."""
        if not self.rollback_steps and not failed_step.rollback_cmd:
            return
        
        print(f"\n[markpact] ROLLBACK: Executing rollback steps")
        
        # First, execute failed step's rollback command if available
        if failed_step.rollback_cmd:
            print(f"  [Rollback] {failed_step.id}: {failed_step.rollback_cmd}")
            try:
                import subprocess
                subprocess.run(failed_step.rollback_cmd, shell=True, check=False)
            except Exception as e:
                print(f"  [Rollback Warning] Failed: {e}")
        
        # Then execute rollback steps in reverse order
        for rb_step in reversed(self.rollback_steps):
            print(f"  [Rollback] {rb_step.id}")
            try:
                result = self._execute_step_single(rb_step, 1)
                if not result.success:
                    print(f"  [Rollback Warning] {rb_step.id} failed: {result.error}")
            except Exception as e:
                print(f"  [Rollback Warning] {rb_step.id} error: {e}")
        
        print("[markpact] Rollback complete")
    
    def _get_ssh_manager(self, host: str, user: str) -> SSHSessionManager:
        """Get or create SSH session manager."""
        key = f"{user}@{host}"
        
        if key not in self._ssh_sessions:
            self._ssh_sessions[key] = SSHSessionManager(
                host, user, self.config.ssh_key
            )
        
        return self._ssh_sessions[key]
    
    def _process_blocks(self, blocks: List[Block]) -> None:
        """Process parsed blocks to extract config and steps."""
        for block in blocks:
            if block.type == BlockType.CONFIG:
                self._process_config(block)
            elif block.type == BlockType.STEPS:
                self._process_steps(block)
            elif block.type == BlockType.ROLLBACK:
                self._process_rollback(block)
            elif block.type == BlockType.PYTHON:
                self._process_python_block(block)
            elif block.type == BlockType.BASH:
                self._process_bash_block(block)
            elif block.type == BlockType.RUN:
                self._process_run_block(block)
    
    def _process_python_block(self, block: Block) -> None:
        """Process Python code block as executable step."""
        # Generate unique ID for this block
        import hashlib
        block_id = f"python_{hashlib.md5(block.content.encode()).hexdigest()[:8]}"
        
        self.steps.append(Step(
            id=block_id,
            action="python",
            description=f"Python block (lines {block.line_start}-{block.line_end})",
            params={"code": block.content},
            risk="medium",
            timeout=300
        ))
    
    def _process_bash_block(self, block: Block) -> None:
        """Process Bash code block as executable step."""
        import hashlib
        block_id = f"bash_{hashlib.md5(block.content.encode()).hexdigest()[:8]}"
        
        self.steps.append(Step(
            id=block_id,
            action="bash",
            description=f"Bash block (lines {block.line_start}-{block.line_end})",
            params={"script": block.content},
            risk="medium",
            timeout=300
        ))
    
    def _process_run_block(self, block: Block) -> None:
        """Process run block as bash executable step."""
        import hashlib
        block_id = f"run_{hashlib.md5(block.content.encode()).hexdigest()[:8]}"
        
        self.steps.append(Step(
            id=block_id,
            action="bash",
            description=f"Run block (lines {block.line_start}-{block.line_end})",
            params={"script": block.content},
            risk="medium",
            timeout=300
        ))
    
    def _process_config(self, block: Block) -> None:
        """Process configuration block."""
        import yaml
        
        try:
            config_data = yaml.safe_load(block.content)
            if isinstance(config_data, dict):
                # Validate with Pydantic
                self.config_data = config_data
                
                # Load plugins if specified
                if "plugins" in config_data:
                    for plugin_spec in config_data["plugins"]:
                        if isinstance(plugin_spec, dict):
                            if "path" in plugin_spec:
                                self.plugins.load_from_path(Path(plugin_spec["path"]))
                            elif "module" in plugin_spec:
                                self.plugins.load_from_module(plugin_spec["module"])
                        elif isinstance(plugin_spec, str):
                            self.plugins.load_from_path(Path(plugin_spec))
                
        except Exception as e:
            raise ValidationError(f"Failed to parse config block: {e}")
    
    def _process_steps(self, block: Block) -> None:
        """Process steps block with Pydantic validation."""
        import yaml
        
        try:
            steps_data = yaml.safe_load(block.content)
            
            if isinstance(steps_data, dict) and "extra_steps" in steps_data:
                for step_data in steps_data["extra_steps"]:
                    try:
                        self.steps.append(Step.from_dict(step_data))
                    except Exception as e:
                        raise ValidationError(f"Invalid step '{step_data.get('id', 'unknown')}': {e}")
            elif isinstance(steps_data, list):
                for step_data in steps_data:
                    try:
                        self.steps.append(Step.from_dict(step_data))
                    except Exception as e:
                        raise ValidationError(f"Invalid step '{step_data.get('id', 'unknown')}': {e}")
        except Exception as e:
            raise ValidationError(f"Failed to parse steps block: {e}")
    
    def _process_rollback(self, block: Block) -> None:
        """Process rollback block."""
        import yaml
        
        try:
            data = yaml.safe_load(block.content)
            if isinstance(data, dict) and "steps" in data:
                for step_data in data["steps"]:
                    self.rollback_steps.append(Step.from_dict(step_data))
        except Exception as e:
            raise ValidationError(f"Failed to parse rollback block: {e}")
    
    def _print_summary(self) -> None:
        """Print execution summary."""
        if not self.results:
            return
        
        total = len(self.results)
        success = sum(1 for r in self.results if r.status == "success")
        failed = sum(1 for r in self.results if r.status == "failed")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        
        total_time = sum(r.duration for r in self.results)
        
        print(f"\n[markpact] Summary: {success}/{total} steps succeeded")
        if failed:
            print(f"             {failed} failed")
        if skipped:
            print(f"             {skipped} skipped (idempotent or conditions)")
        print(f"             Total time: {total_time:.1f}s")
        
        # State persistence info
        done_count = len(self.state_manager.state.steps_done)
        print(f"[markpact] State saved: {done_count} steps completed")
        print(f"             State file: {self.config.state_file}")
    
    def reset_state(self) -> None:
        """Reset deployment state for fresh start."""
        self.state_manager.reset()
        print(f"[markpact] State reset: {self.config.state_file}")
    
    def close(self) -> None:
        """Cleanup resources."""
        # Close SSH sessions
        for session in self._ssh_sessions.values():
            session.close()
        self._ssh_sessions.clear()
