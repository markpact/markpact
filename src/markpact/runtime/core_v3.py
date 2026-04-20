"""
Markpact Runtime v3: State Reconciliation Engine

Mini-Terraform dla RPi/Edge deployment z prawdziwą idempotencją.

Key features:
- Step hashing for true idempotency (detects changes)
- State reconciliation mindset (current → desired)
- Check commands for conditional execution
- Atomic state writes
- Facts gatherer for current state inspection
- Plan mode (preview changes)

Inspired by Terraform and Ansible patterns.
"""

import re
import os
import sys
import time
import yaml
import toml
import json
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
from enum import Enum
import subprocess

from .models import Step, DeploymentConfig, DeployState, StepResult, StepStatus, ExecutionSummary
from .state import StateManager, ConditionChecker
from .ssh_manager import SSHSessionManager
from .exceptions import ExecutionError, ValidationError, RollbackError
from .executors import ExecutorRegistry
from .parser import MarkpactParser, BlockType

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


class RuntimeConfigV3:
    """Configuration for RuntimeV3."""
    
    def __init__(
        self,
        dry_run: bool = False,
        verbose: bool = True,
        stop_on_error: bool = True,
        plugin_paths: Optional[List[Path]] = None,
        ssh_key: Optional[str] = None,
        timeout_default: int = 300,
        retry_default: int = 0,
        state_file: str = ".deploy-state.json",
        reset_state: bool = False,
        plan_mode: bool = False,  # v3: preview changes without executing
    ):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stop_on_error = stop_on_error
        self.plugin_paths = plugin_paths or []
        self.ssh_key = ssh_key
        self.timeout_default = timeout_default
        self.retry_default = retry_default
        self.state_file = state_file
        self.reset_state = reset_state
        self.plan_mode = plan_mode


@dataclass
class StepExecutionRecord:
    """Record of executed step for rollback stack."""
    step_id: str
    step_hash: str
    rollback_cmd: Optional[str]
    timestamp: float = field(default_factory=time.time)


class FactsGatherer:
    """
    Gathers current state facts from target host.
    
    This enables true idempotency by checking actual state
    rather than just execution history.
    """
    
    def __init__(self, runtime: 'RuntimeV3'):
        self.runtime = runtime
        self._cache: Dict[str, Any] = {}
    
    def clear_cache(self):
        """Clear fact cache."""
        self._cache.clear()
    
    def check(self, condition: str) -> bool:
        """
        Check a condition against current facts.
        
        Supported conditions:
        - docker_installed
        - docker_running[:container_name]
        - file_exists:/path
        - dir_exists:/path
        - command_succeeds:"command"
        """
        if condition in self._cache:
            return self._cache[condition]
        
        result = self._eval_condition(condition)
        self._cache[condition] = result
        return result
    
    def _eval_condition(self, condition: str) -> bool:
        """Evaluate a single condition."""
        # Docker checks
        if condition == "docker_installed":
            return self._check_docker_installed()
        
        if condition.startswith("docker_running:"):
            container = condition.split(":", 1)[1]
            return self._check_container_running(container)
        
        # File/directory checks
        if condition.startswith("file_exists:"):
            path = condition.split(":", 1)[1]
            return self._check_file_exists(path)
        
        if condition.startswith("dir_exists:"):
            path = condition.split(":", 1)[1]
            return self._check_dir_exists(path)
        
        # Command check
        if condition.startswith("command_succeeds:"):
            cmd = condition.split(":", 1)[1].strip('"')
            return self._check_command_succeeds(cmd)
        
        # Fallback: try as shell command
        return self._check_command_succeeds(f"test {condition}")
    
    def _check_docker_installed(self) -> bool:
        """Check if docker is installed on target."""
        try:
            exit_code = self.runtime._exec_remote("command -v docker > /dev/null 2>&1", timeout=10)
            return exit_code == 0
        except:
            return False
    
    def _check_container_running(self, name: str) -> bool:
        """Check if docker container is running."""
        try:
            cmd = f'docker ps --filter "name={name}" --format "{{{{.Names}}}}" | grep -q "{name}"'
            exit_code = self.runtime._exec_remote(cmd, timeout=10)
            return exit_code == 0
        except:
            return False
    
    def _check_file_exists(self, path: str) -> bool:
        """Check if file exists on target."""
        try:
            exit_code = self.runtime._exec_remote(f'test -f "{path}"', timeout=10)
            return exit_code == 0
        except:
            return False
    
    def _check_dir_exists(self, path: str) -> bool:
        """Check if directory exists on target."""
        try:
            exit_code = self.runtime._exec_remote(f'test -d "{path}"', timeout=10)
            return exit_code == 0
        except:
            return False
    
    def _check_command_succeeds(self, cmd: str) -> bool:
        """Check if command succeeds."""
        try:
            exit_code = self.runtime._exec_remote(cmd, timeout=30)
            return exit_code == 0
        except:
            return False


class RuntimeV3:
    """
    Markpact Runtime v3: State Reconciliation Engine
    
    Terraform-style deployment with:
    - Step hashing for true idempotency
    - Current state inspection (facts)
    - Desired state reconciliation
    - Atomic state management
    - Plan mode for previewing changes
    
    Usage:
        runtime = RuntimeV3("migration.md", config=RuntimeConfigV3())
        runtime.reconcile()  # Apply desired state
        # or
        runtime.plan()       # Preview changes only
    """
    
    def __init__(self, file_path: str, config: Optional[RuntimeConfigV3] = None):
        self.file_path = Path(file_path)
        self.config = config or RuntimeConfigV3()
        
        # State management
        self.state_manager = StateManager(self.config.state_file)
        if self.config.reset_state:
            self.state_manager.reset()
        
        # Components
        self.parser = MarkpactParser()
        self.executors = ExecutorRegistry()
        self.facts = FactsGatherer(self)
        self.condition_checker = ConditionChecker(self.state_manager)
        
        # SSH sessions cache
        self._ssh_sessions: Dict[str, SSHSessionManager] = {}
        
        # Execution tracking
        self.steps: List[Step] = []
        self.config_data: Optional[DeploymentConfig] = None
        self.rollback_steps: List[Step] = []
        self.executed_stack: List[StepExecutionRecord] = []
        
        # Results
        self.results: List[StepResult] = []
        self.summary: Optional[ExecutionSummary] = None
        
        # v3: Step hash tracking
        self.step_hashes: Dict[str, str] = self.state_manager.state.step_hashes
    
    # ==================== PARSING ====================
    
    def parse(self) -> List[Any]:
        """Parse markdown file into blocks."""
        return self.parser.parse_file(str(self.file_path))
    
    def _process_blocks(self, blocks: List[Any]) -> None:
        """Process parsed blocks into steps and config."""
        for block in blocks:
            if block.type == BlockType.CONFIG:
                self._load_config(block)
            elif block.type == BlockType.STEPS:
                self._load_steps(block)
            elif block.type == BlockType.ROLLBACK:
                self._load_rollback(block)
    
    def _load_config(self, block) -> None:
        """Load configuration from block."""
        if block.format == "yaml":
            data = yaml.safe_load(block.content)
        elif block.format == "toml":
            data = toml.loads(block.content)
        elif block.format == "json":
            data = json.loads(block.content)
        else:
            return
        
        self.config_data = DeploymentConfig(**data)
        
        # Apply global defaults
        if self.config_data.timeout and not self.config.timeout_default:
            self.config.timeout_default = self.config_data.timeout
        if self.config_data.retry is not None:
            self.config.retry_default = self.config_data.retry
    
    def _load_steps(self, block) -> None:
        """Load steps from block."""
        if block.format == "yaml":
            data = yaml.safe_load(block.content)
        elif block.format == "toml":
            data = toml.loads(block.content)
        elif block.format == "json":
            data = json.loads(block.content)
        else:
            return
        
        extra_steps = data.get("extra_steps", [])
        for step_data in extra_steps:
            # Apply defaults
            if "timeout" not in step_data and self.config.timeout_default:
                step_data["timeout"] = self.config.timeout_default
            if "retry" not in step_data and self.config.retry_default:
                step_data["retry"] = self.config.retry_default
            
            step = Step(**step_data)
            self.steps.append(step)
    
    def _load_rollback(self, block) -> None:
        """Load rollback steps from block."""
        if block.format == "yaml":
            data = yaml.safe_load(block.content)
        elif block.format == "toml":
            data = toml.loads(block.content)
        elif block.format == "json":
            data = json.loads(block.content)
        else:
            return
        
        rollback_data = data.get("steps", [])
        for step_data in rollback_data:
            step = Step(**step_data)
            self.rollback_steps.append(step)
    
    # ==================== CORE RECONCILIATION ====================
    
    def plan(self) -> ExecutionSummary:
        """
        Preview changes without executing (Terraform-style plan).
        
        Returns summary showing what would change and why.
        """
        self.config.plan_mode = True
        return self.reconcile()
    
    def reconcile(self, step_filter: Optional[str] = None) -> ExecutionSummary:
        """
        Reconcile current state with desired state.
        
        This is the main v3 entry point - instead of just executing steps,
        it checks current state and only applies changes when needed.
        """
        start_time = time.time()
        
        # Parse
        blocks = self.parse()
        self._process_blocks(blocks)
        
        # Filter steps if requested
        steps_to_process = self._filter_steps(self.steps, step_filter)
        
        total = len(steps_to_process)
        executed = 0
        skipped = 0
        failed = 0
        
        if self.config.verbose:
            mode_str = "[PLAN]" if self.config.plan_mode else "[RECONCILE]"
            print(f"{mode_str} Processing {total} steps...")
        
        for i, step in enumerate(steps_to_process, 1):
            # Check if step needs execution
            need_execution, reason = self._should_execute(step)
            
            if not need_execution:
                skipped += 1
                if self.config.verbose:
                    print(f"  [{i}/{total}] SKIP {step.id}: {reason}")
                
                result = StepResult(
                    step_id=step.id,
                    status=StepStatus.SKIPPED,
                    message=reason,
                )
                self.results.append(result)
                continue
            
            # Execute or simulate
            if self.config.plan_mode:
                executed += 1
                if self.config.verbose:
                    print(f"  [{i}/{total}] PLAN {step.id}: would {step.action} ({reason})")
                
                result = StepResult(
                    step_id=step.id,
                    status=StepStatus.PLANNED,
                    message=f"Would execute: {reason}",
                )
                self.results.append(result)
                continue
            
            # Real execution
            success = self._execute_step_with_retry(step)
            
            if success:
                executed += 1
                # Update state
                step_hash = self._compute_step_hash(step)
                self.state_manager.mark_step_done(step.id, step_hash)
                
                # Push to rollback stack
                if step.rollback_cmd or self.rollback_steps:
                    record = StepExecutionRecord(
                        step_id=step.id,
                        step_hash=step_hash,
                        rollback_cmd=step.rollback_cmd,
                    )
                    self.executed_stack.append(record)
            else:
                failed += 1
                if self.config.stop_on_error:
                    break
        
        # Build summary
        self.summary = ExecutionSummary(
            total_steps=total,
            successful=executed,
            failed=failed,
            skipped=skipped,
            duration=time.time() - start_time,
            step_results=self.results,
        )
        
        return self.summary
    
    def _should_execute(self, step: Step) -> tuple[bool, str]:
        """
        Determine if step needs execution.
        
        Returns: (should_execute, reason)
        
        Priority:
        1. Hash mismatch (step definition changed)
        2. Check condition fails (current state differs from desired)
        3. skip_if condition
        4. History-based (fallback)
        """
        # Compute current hash
        current_hash = self._compute_step_hash(step)
        
        # 1. Check if step definition changed (v3: true idempotency)
        if step.id in self.step_hashes:
            stored_hash = self.step_hashes[step.id]
            if stored_hash != current_hash:
                return True, f"definition changed (hash: {stored_hash[:8]} → {current_hash[:8]})"
        
        # 2. Check current state with check_cmd (v3: reconciliation)
        if step.check_cmd:
            check_passed = self.facts.check(step.check_cmd)
            if check_passed:
                # Desired state already achieved
                if step.id not in self.step_hashes:
                    # Record hash for future change detection
                    self.state_manager.mark_step_done(step.id, current_hash)
                return False, f"check passed: {step.check_cmd}"
            else:
                return True, f"check failed: {step.check_cmd}"
        
        # 3. Check skip_if condition
        if step.skip_if:
            skip = self.facts.check(step.skip_if)
            if skip:
                return False, f"skip_if: {step.skip_if}"
        
        # 4. Check when condition
        if step.when:
            should_run = self.facts.check(step.when)
            if not should_run:
                return False, f"when condition false: {step.when}"
        
        # 5. History-based (fallback for steps without check_cmd)
        if self.state_manager.is_step_done(step.id):
            return False, "already executed (hash unchanged)"
        
        return True, "needs execution"
    
    def _compute_step_hash(self, step: Step) -> str:
        """
        Compute hash of step definition for change detection.
        
        This enables true idempotency - if step definition changes,
        it will be re-executed even if previously completed.
        """
        # Create deterministic representation
        step_dict = {
            "id": step.id,
            "action": step.action,
            "command": step.command,
            "src": step.src,
            "dst": step.dst,
            "host": step.host,
            "docker_action": step.docker_action,
            "params": step.params,
            "when": step.when,
            "skip_if": step.skip_if,
            "check_cmd": step.check_cmd,
        }
        
        # Hash it
        json_str = json.dumps(step_dict, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    # ==================== STEP EXECUTION ====================
    
    def _execute_step_with_retry(self, step: Step) -> bool:
        """Execute step with retry logic."""
        max_attempts = step.retry + 1 if step.retry else 1
        
        for attempt in range(1, max_attempts + 1):
            try:
                self._execute_step(step)
                return True
            except Exception as e:
                if attempt < max_attempts:
                    delay = 2 ** (attempt - 1)  # Exponential backoff
                    if self.config.verbose:
                        print(f"    [RETRY {attempt}/{step.retry}] {step.id}: {e}")
                        print(f"    Waiting {delay}s...")
                    time.sleep(delay)
                else:
                    # Final failure
                    self.state_manager.mark_step_failed(step.id, str(e))
                    
                    result = StepResult(
                        step_id=step.id,
                        status=StepStatus.FAILED,
                        message=str(e),
                        attempt=attempt,
                    )
                    self.results.append(result)
                    
                    if self.config.verbose:
                        print(f"    [FAILED] {step.id} after {attempt} attempts: {e}")
                    
                    # Attempt rollback
                    if self.config.stop_on_error:
                        self._rollback(step)
                    
                    return False
        
        return False
    
    def _execute_step(self, step: Step) -> None:
        """Execute a single step."""
        if self.config.verbose:
            print(f"    [EXEC] {step.id}: {step.action}")
        
        # Get executor
        executor = self.executors.get(step.action)
        if not executor:
            raise ExecutionError(f"Unknown action: {step.action}")
        
        # Build context
        context = {
            "config": self.config,
            "step": step,
            "ssh_manager": self._get_ssh_manager,
            "facts": self.facts,
        }
        
        # Execute
        output = executor.execute(step, context)
        
        # Record result
        result = StepResult(
            step_id=step.id,
            status=StepStatus.SUCCESS,
            output=output,
        )
        self.results.append(result)
    
    def _get_ssh_manager(self, host: str, user: str = "root") -> SSHSessionManager:
        """Get or create SSH session manager."""
        key = f"{user}@{host}"
        if key not in self._ssh_sessions:
            self._ssh_sessions[key] = SSHSessionManager(host, user, key_path=self.config.ssh_key)
            self._ssh_sessions[key].connect()
        return self._ssh_sessions[key]
    
    def _exec_remote(self, command: str, timeout: int = 30) -> int:
        """Execute command on remote and return exit code."""
        if not self.config_data or not self.config_data.target:
            raise ExecutionError("No target host configured")
        
        host = self.config_data.target.host
        if "@" in host:
            user, hostname = host.split("@", 1)
        else:
            user = "root"
            hostname = host
        
        ssh_mgr = self._get_ssh_manager(hostname, user)
        _, _, exit_code = ssh_mgr.exec_command(command, timeout)
        return exit_code
    
    # ==================== ROLLBACK ====================
    
    def _rollback(self, failed_step: Step) -> None:
        """Rollback executed steps in reverse order."""
        if self.config.dry_run:
            return
        
        if self.config.verbose:
            print("\n[ROLLBACK] Starting rollback...")
        
        # First: failed step's own rollback command
        if failed_step.rollback_cmd:
            if self.config.verbose:
                print(f"  [ROLLBACK] {failed_step.id}: {failed_step.rollback_cmd}")
            try:
                self._exec_remote(failed_step.rollback_cmd)
            except Exception as e:
                if self.config.verbose:
                    print(f"    Warning: rollback command failed: {e}")
        
        # Then: rollback stack in reverse order
        for record in reversed(self.executed_stack):
            if record.rollback_cmd:
                if self.config.verbose:
                    print(f"  [ROLLBACK] {record.step_id}: {record.rollback_cmd}")
                try:
                    self._exec_remote(record.rollback_cmd)
                except Exception as e:
                    if self.config.verbose:
                        print(f"    Warning: rollback failed: {e}")
        
        # Finally: dedicated rollback blocks
        for step in reversed(self.rollback_steps):
            if self.config.verbose:
                print(f"  [ROLLBACK-BLOCK] {step.id}")
            try:
                self._execute_step(step)
            except Exception as e:
                if self.config.verbose:
                    print(f"    Warning: rollback block failed: {e}")
        
        if self.config.verbose:
            print("[ROLLBACK] Complete\n")
    
    # ==================== UTILITIES ====================
    
    def _filter_steps(self, steps: List[Step], pattern: Optional[str]) -> List[Step]:
        """Filter steps by pattern."""
        if not pattern:
            return steps
        import re
        regex = re.compile(pattern)
        return [s for s in steps if regex.search(s.id)]
    
    def close(self) -> None:
        """Close all resources."""
        for ssh_mgr in self._ssh_sessions.values():
            try:
                ssh_mgr.close()
            except:
                pass
        self._ssh_sessions.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Backward compatibility
Runtime = RuntimeV3
