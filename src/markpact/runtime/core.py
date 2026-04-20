"""Core runtime for executing markpact deployments."""
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from .parser import MarkpactParser, Block, BlockType
from .executors import ExecutorRegistry
from .plugins import PluginLoader
from .steps import Step, StepResult, StepStatus
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


class Runtime:
    """Main runtime for executing markpact markdown files.
    
    Supports multiple execution backends via plugins and handles
    multi-language specifications (YAML, TOML, JSON, Python, Bash).
    
    Example:
        runtime = Runtime("deployment.md", config=RuntimeConfig(dry_run=True))
        result = runtime.execute()
    """
    
    def __init__(
        self,
        file_path: str,
        config: Optional[RuntimeConfig] = None,
        **kwargs
    ):
        """Initialize runtime.
        
        Args:
            file_path: Path to .md file with markpact blocks
            config: Runtime configuration
            **kwargs: Override config options
        """
        self.file_path = Path(file_path)
        self.config = config or RuntimeConfig()
        
        # Override with kwargs
        for key, value in kwargs.items():
            setattr(self.config, key, value)
        
        # Components
        self.parser = MarkpactParser()
        self.executors = ExecutorRegistry()
        self.plugins = PluginLoader()
        
        # Execution state
        self.steps: List[Step] = []
        self.results: List[StepResult] = []
        self.variables: Dict[str, Any] = {}  # Runtime variables
        
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
        """Execute all or filtered steps.
        
        Args:
            step_filter: Optional regex to filter steps by id
            
        Returns:
            True if all steps succeeded
        """
        blocks = self.parse()
        
        # Process blocks to extract config and steps
        self._process_blocks(blocks)
        
        # Filter steps if requested
        steps_to_run = self.steps
        if step_filter:
            import re
            pattern = re.compile(step_filter)
            steps_to_run = [s for s in steps_to_run if pattern.search(s.id)]
        
        if self.config.verbose:
            print(f"\n[markpact] Executing {len(steps_to_run)} steps")
            if self.config.dry_run:
                print("[markpact] DRY RUN - no changes will be made\n")
            else:
                print()
        
        # Execute steps
        success = True
        for step in steps_to_run:
            result = self._execute_step(step)
            self.results.append(result)
            
            if not result.success:
                success = False
                if self.config.stop_on_error:
                    break
        
        # Summary
        self._print_summary()
        
        return success
    
    def _process_blocks(self, blocks: List[Block]) -> None:
        """Process parsed blocks to extract config and steps."""
        for block in blocks:
            if block.type == BlockType.CONFIG:
                self._process_config(block)
            elif block.type == BlockType.STEPS:
                self._process_steps(block)
            elif block.type == BlockType.RUN:
                self._process_run_block(block)
    
    def _process_config(self, block: Block) -> None:
        """Process configuration block."""
        import yaml
        
        try:
            config_data = yaml.safe_load(block.content)
            if isinstance(config_data, dict):
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
                
                # Store config for later use
                self.variables["_config"] = config_data
                
        except Exception as e:
            raise ValidationError(f"Failed to parse config block: {e}")
    
    def _process_steps(self, block: Block) -> None:
        """Process steps block."""
        import yaml
        
        try:
            steps_data = yaml.safe_load(block.content)
            if isinstance(steps_data, dict) and "extra_steps" in steps_data:
                for step_data in steps_data["extra_steps"]:
                    self.steps.append(Step.from_dict(step_data))
            elif isinstance(steps_data, list):
                for step_data in steps_data:
                    self.steps.append(Step.from_dict(step_data))
        except Exception as e:
            raise ValidationError(f"Failed to parse steps block: {e}")
    
    def _process_run_block(self, block: Block) -> None:
        """Process final run block."""
        # Add as final step
        self.steps.append(Step(
            id="final_run",
            action="shell",
            description="Final verification run",
            command=block.content,
            risk="low"
        ))
    
    def _execute_step(self, step: Step) -> StepResult:
        """Execute a single step."""
        start_time = time.time()
        
        if self.config.verbose:
            print(f"  → [{step.id}] {step.description}")
            if step.risk != "low":
                print(f"     (risk: {step.risk}, timeout: {step.timeout}s)")
        
        if self.config.dry_run:
            print(f"     [DRY] Would execute: {step.action}")
            return StepResult(
                step_id=step.id,
                status=StepStatus.SKIPPED,
                duration=0,
                output="Dry run - skipped"
            )
        
        # Get executor for action
        executor = self.executors.get(step.action)
        if not executor:
            error_msg = f"No executor registered for action: {step.action}"
            print(f"     ✗ {error_msg}")
            return StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                duration=time.time() - start_time,
                error=error_msg
            )
        
        # Execute with timeout
        try:
            context = {
                "variables": self.variables,
                "config": self.config,
                "runtime": self,
            }
            
            output = executor.execute(step, context)
            duration = time.time() - start_time
            
            print(f"     ✓ Success ({duration:.1f}s)")
            
            return StepResult(
                step_id=step.id,
                status=StepStatus.SUCCESS,
                duration=duration,
                output=output
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            print(f"     ✗ Failed: {error_msg}")
            
            return StepResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                duration=duration,
                error=error_msg
            )
    
    def _print_summary(self) -> None:
        """Print execution summary."""
        if not self.results:
            return
        
        total = len(self.results)
        success = sum(1 for r in self.results if r.status == StepStatus.SUCCESS)
        failed = sum(1 for r in self.results if r.status == StepStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == StepStatus.SKIPPED)
        
        total_time = sum(r.duration for r in self.results)
        
        print(f"\n[markpact] Summary: {success}/{total} steps succeeded")
        if failed:
            print(f"             {failed} failed")
        if skipped:
            print(f"             {skipped} skipped")
        print(f"             Total time: {total_time:.1f}s")
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a runtime variable."""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a runtime variable."""
        return self.variables.get(name, default)
