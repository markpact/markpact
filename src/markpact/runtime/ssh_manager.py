"""Persistent SSH session management."""
from contextlib import contextmanager
from typing import Optional


class SSHSessionManager:
    """Manages persistent SSH sessions for performance.
    
    Avoids reconnecting for each step - reuses single session.
    """
    
    def __init__(self, host: str, user: str, key_file: Optional[str] = None):
        self.host = host
        self.user = user
        self.key_file = key_file
        self._client = None
        self._connected = False
    
    def connect(self) -> bool:
        """Establish SSH connection."""
        if self._connected:
            return True
        
        try:
            import paramiko
            
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": self.host,
                "username": self.user,
                "timeout": 30,
            }
            
            if self.key_file:
                connect_kwargs["key_filename"] = self.key_file
            
            self._client.connect(**connect_kwargs)
            self._connected = True
            
            print(f"[SSH] Connected to {self.user}@{self.host}")
            return True
            
        except ImportError:
            # Fallback to subprocess if paramiko not available
            print(f"[SSH] Using subprocess fallback (paramiko not installed)")
            return False
        except Exception as e:
            print(f"[SSH] Connection failed: {e}")
            return False
    
    def exec_command(self, command: str, timeout: int = 300) -> tuple:
        """Execute command via SSH.
        
        Returns: (stdout, stderr, exit_code)
        """
        if self._connected and self._client:
            # Use paramiko
            stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            exit_code = stdout.channel.recv_exit_status()
            return out, err, exit_code
        else:
            # Fallback to subprocess
            import subprocess
            
            ssh_cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=10",
            ]
            
            if self.key_file:
                ssh_cmd.extend(["-i", self.key_file])
            
            ssh_cmd.append(f"{self.user}@{self.host}")
            ssh_cmd.append(command)
            
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.stdout, result.stderr, result.returncode
    
    def close(self) -> None:
        """Close SSH connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._connected = False
            print(f"[SSH] Disconnected from {self.host}")
    
    @contextmanager
    def session(self):
        """Context manager for SSH session."""
        self.connect()
        try:
            yield self
        finally:
            pass  # Keep connection open for reuse
    
    def __del__(self):
        """Cleanup on garbage collection."""
        self.close()


def get_ssh_manager(host: str, user: str, key_file: Optional[str] = None) -> SSHSessionManager:
    """Factory for SSH session manager."""
    return SSHSessionManager(host, user, key_file)
