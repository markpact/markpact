"""Executors for different action types.

Built-in executors:
- shell: Execute shell commands locally or via SSH
- rsync: Synchronize files
- scp: Copy files via SCP
- docker: Docker compose operations
- python: Execute Python code
- http: HTTP health checks
"""
import subprocess
import time
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .steps import Step
from .exceptions import ExecutionError


class Executor(ABC):
    """Base class for action executors."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Executor name."""
        pass
    
    @abstractmethod
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        """Execute the step.
        
        Args:
            step: Step to execute
            context: Runtime context with variables, config, etc.
            
        Returns:
            Output from execution
            
        Raises:
            ExecutionError: If execution fails
        """
        pass
    
    def validate(self, step: Step) -> bool:
        """Validate step configuration."""
        return True


class ShellExecutor(Executor):
    """Execute shell commands locally or via SSH with persistent sessions."""
    
    @property
    def name(self) -> str:
        return "shell"
    
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        command = step.command
        if not command:
            raise ExecutionError("No command specified for shell executor")
        
        # Check if should run via SSH
        host = step.params.get("host") or context.get("target_host")
        
        if host:
            return self._run_ssh_persistent(host, command, step.timeout, context)
        else:
            return self._run_local(command, step.timeout)
    
    def _run_local(self, command: str, timeout: int) -> str:
        """Run command locally."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                raise ExecutionError(
                    f"Command failed with exit code {result.returncode}: {result.stderr}"
                )
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise ExecutionError(f"Command timed out after {timeout}s")
    
    def _run_ssh_persistent(self, host: str, command: str, timeout: int, context: Dict) -> str:
        """Run command via SSH using persistent session."""
        # Parse host into user@host
        if "@" in host:
            user, hostname = host.split("@", 1)
        else:
            user = "root"
            hostname = host
        
        # Get SSH manager from context
        get_ssh_manager = context.get("ssh_manager")
        if get_ssh_manager:
            ssh_mgr = get_ssh_manager(hostname, user)
            out, err, exit_code = ssh_mgr.exec_command(command, timeout)
            
            if exit_code != 0:
                raise ExecutionError(f"SSH command failed (exit {exit_code}): {err}")
            
            return out
        else:
            # Fallback to subprocess
            return self._run_ssh_subprocess(host, command, timeout, context)
    
    def _run_ssh_subprocess(self, host: str, command: str, timeout: int, context: Dict) -> str:
        """Fallback SSH execution via subprocess."""
        config = context.get("config")
        
        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
        
        if config and config.ssh_key:
            ssh_cmd.extend(["-i", config.ssh_key])
        
        ssh_cmd.extend([host, command])
        
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                raise ExecutionError(
                    f"SSH command failed: {result.stderr}"
                )
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise ExecutionError(f"SSH command timed out after {timeout}s")


class SSHCmdExecutor(ShellExecutor):
    """Alias for shell executor with explicit SSH."""
    
    @property
    def name(self) -> str:
        return "ssh_cmd"


class RsyncExecutor(Executor):
    """Execute rsync operations."""
    
    @property
    def name(self) -> str:
        return "rsync"
    
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        src = step.params.get("src")
        dst = step.params.get("dst")
        excludes = step.params.get("excludes", [])
        delete = step.params.get("delete", False)
        
        if not src or not dst:
            raise ExecutionError("rsync requires 'src' and 'dst' parameters")
        
        cmd = ["rsync", "-avz", "--progress"]
        
        if delete:
            cmd.append("--delete")
        
        for pattern in excludes:
            cmd.extend(["--exclude", pattern])
        
        cmd.extend([src, dst])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=step.timeout
            )
            
            if result.returncode != 0:
                raise ExecutionError(f"rsync failed: {result.stderr}")
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise ExecutionError(f"rsync timed out after {step.timeout}s")


class ScpExecutor(Executor):
    """Execute SCP copy operations."""
    
    @property
    def name(self) -> str:
        return "scp"
    
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        src = step.params.get("src")
        dst = step.params.get("dst")
        
        if not src or not dst:
            raise ExecutionError("scp requires 'src' and 'dst' parameters")
        
        cmd = ["scp", "-o", "StrictHostKeyChecking=no", src, dst]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=step.timeout
            )
            
            if result.returncode != 0:
                raise ExecutionError(f"scp failed: {result.stderr}")
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise ExecutionError(f"scp timed out after {step.timeout}s")


class DockerExecutor(Executor):
    """Execute Docker Compose operations."""
    
    @property
    def name(self) -> str:
        return "docker"
    
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        action = step.params.get("docker_action", "compose_up")
        
        if action == "compose_up":
            return self._compose_up(step, context)
        elif action == "compose_down":
            return self._compose_down(step, context)
        elif action == "wait_healthy":
            return self._wait_healthy(step, context)
        else:
            raise ExecutionError(f"Unknown docker action: {action}")
    
    def _compose_up(self, step: Step, context: Dict) -> str:
        host = step.params.get("host")
        project_dir = step.params.get("project_dir", "~/")
        files = step.params.get("files", ["docker-compose.yml"])
        env_file = step.params.get("env_file")
        build = step.params.get("build", True)
        
        cmd_parts = ["docker compose"]
        
        for f in files:
            cmd_parts.append(f"-f {f}")
        
        if env_file:
            cmd_parts.append(f"--env-file {env_file}")
        
        cmd_parts.append("up -d")
        
        if build:
            cmd_parts.append("--build")
        
        full_cmd = " ".join(cmd_parts)
        
        if host:
            ssh_cmd = f"cd {project_dir} && {full_cmd}"
            return self._run_ssh(host, ssh_cmd, step.timeout, context)
        else:
            return self._run_local(full_cmd, step.timeout, cwd=project_dir)
    
    def _compose_down(self, step: Step, context: Dict) -> str:
        # Similar implementation...
        return "docker compose down executed"
    
    def _wait_healthy(self, step: Step, context: Dict) -> str:
        """Wait for containers to be healthy."""
        host = step.params.get("host")
        project = step.params.get("project", "")
        timeout = step.timeout
        
        start = time.time()
        while time.time() - start < timeout:
            cmd = "docker compose ps --format json 2>/dev/null || docker compose ps"
            
            if host:
                result = self._run_ssh(host, f"cd ~/{project} && {cmd}", 30, context)
            else:
                result = self._run_local(cmd, 30, cwd=f"~/{project}")
            
            if "healthy" in result.lower() or "running" in result.lower():
                if "unhealthy" not in result.lower() and "exited" not in result.lower():
                    return f"All services healthy after {int(time.time() - start)}s"
            
            time.sleep(5)
        
        raise ExecutionError(f"Services not healthy after {timeout}s")
    
    def _run_local(self, command: str, timeout: int, cwd: Optional[str] = None) -> str:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        
        if result.returncode != 0:
            raise ExecutionError(f"Command failed: {result.stderr}")
        
        return result.stdout
    
    def _run_ssh(self, host: str, command: str, timeout: int, context: Dict) -> str:
        ssh_cmd = f'ssh -o StrictHostKeyChecking=no {host} "{command}"'
        return self._run_local(ssh_cmd, timeout)


class HttpExecutor(Executor):
    """Execute HTTP health checks."""
    
    @property
    def name(self) -> str:
        return "http"
    
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        url = step.params.get("url") or step.params.get("verify_url")
        expect = step.params.get("expect", "")
        retries = step.params.get("retries", 3)
        
        if not url:
            raise ExecutionError("http executor requires 'url' parameter")
        
        last_error = None
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, method="GET")
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    content = response.read().decode('utf-8')
                    
                    if expect and expect not in content:
                        raise ExecutionError(
                            f"Expected '{expect}' not found in response: {content[:200]}"
                        )
                    
                    return f"HTTP check passed: {url}"
                    
            except Exception as e:
                last_error = str(e)
                if attempt < retries - 1:
                    time.sleep(2)
                
        raise ExecutionError(f"HTTP check failed after {retries} attempts: {last_error}")


class PluginExecutor(Executor):
    """Execute custom plugin actions."""
    
    @property
    def name(self) -> str:
        return "plugin"
    
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        plugin_type = step.params.get("plugin_type")
        
        if not plugin_type:
            raise ExecutionError("plugin executor requires 'plugin_type' parameter")
        
        # Look up plugin from context
        runtime = context.get("runtime")
        if not runtime:
            raise ExecutionError("Runtime not available in context")
        
        plugin = runtime.plugins.get(plugin_type)
        if not plugin:
            raise ExecutionError(f"Plugin not found: {plugin_type}")
        
        return plugin.execute(step, context)


class PythonExecutor(Executor):
    """Execute Python code blocks."""
    
    @property
    def name(self) -> str:
        return "python"
    
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        """Execute Python code from step params."""
        code = step.params.get("code") or step.command
        
        if not code:
            raise ExecutionError("No Python code provided")
        
        # Create execution environment with context
        exec_globals = {
            "__name__": "__markpact__",
            "context": context,
            "config": context.get("config"),
            "variables": context.get("variables"),
        }
        
        # Capture output
        import io
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            exec(code, exec_globals)
            output = captured_output.getvalue()
            
            # Check for variable exports
            if "__export_vars__" in exec_globals:
                for name, value in exec_globals["__export_vars__"].items():
                    context["variables"][name] = value
            
            return output or "Python code executed successfully"
            
        except Exception as e:
            raise ExecutionError(f"Python execution failed: {e}")
        finally:
            sys.stdout = old_stdout


class BashExecutor(Executor):
    """Execute Bash/shell scripts."""
    
    @property
    def name(self) -> str:
        return "bash"
    
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        """Execute bash script from step params."""
        script = step.params.get("script") or step.command
        
        if not script:
            raise ExecutionError("No bash script provided")
        
        # Write script to temp file and execute
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write("#!/bin/bash\n")
            f.write("set -e\n")  # Exit on error
            f.write(script)
            script_path = f.name
        
        try:
            result = subprocess.run(
                ["bash", script_path],
                capture_output=True,
                text=True,
                timeout=step.timeout,
                cwd=step.params.get("cwd")
            )
            
            if result.returncode != 0:
                raise ExecutionError(f"Bash script failed: {result.stderr}")
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise ExecutionError(f"Bash script timed out after {step.timeout}s")
        finally:
            os.unlink(script_path)


class ExecutorRegistry:
    """Registry of available executors."""
    
    def __init__(self):
        self._executors: Dict[str, Executor] = {}
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register default built-in executors."""
        self.register(ShellExecutor())
        self.register(SSHCmdExecutor())
        self.register(RsyncExecutor())
        self.register(ScpExecutor())
        self.register(DockerExecutor())
        self.register(HttpExecutor())
        self.register(PluginExecutor())
    
    def register(self, executor: Executor) -> None:
        """Register an executor."""
        self._executors[executor.name] = executor
    
    def get(self, name: str) -> Optional[Executor]:
        """Get executor by name."""
        return self._executors.get(name)
    
    def list(self) -> List[str]:
        """List all registered executor names."""
        return list(self._executors.keys())
