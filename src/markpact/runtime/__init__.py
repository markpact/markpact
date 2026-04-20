"""Markpact Runtime - Universal Deployment Runtime for Multiple Languages.

A plugin-extensible runtime that can execute deployment specifications
written in various formats (YAML, TOML, JSON, Python, Bash) embedded in
markdown files using the markpact format.

Usage:
    # Standalone
    python -m markpact.runtime migration.md --dry-run
    
    # As library
    from markpact.runtime import Runtime
    runtime = Runtime("migration.md")
    runtime.execute()

Plugin System:
    Plugins can be loaded from filesystem paths:
    
    runtime = Runtime("migration.md", plugin_paths=["./plugins", "~/.markpact/plugins"])
    
    Or specify in markdown:
    ```markpact:config
    plugins:
      - path: ./custom_plugins
      - path: /usr/share/markpact/plugins
      - module: my_package.plugins
    ```
"""

# Runtime v2 with idempotency, SSH persistence, retry, rollback
from .core_v2 import RuntimeV2, RuntimeConfig
from .models import (
    Step,
    StepResult,
    DeploymentConfig,
    DeployState,
)
from .parser import MarkpactParser, BlockType
from .executors import ExecutorRegistry
from .plugins import PluginLoader, Plugin
from .state import StateManager, ConditionChecker
from .ssh_manager import SSHSessionManager
from .exceptions import (
    MarkpactError,
    ParseError,
    ExecutionError,
    PluginError,
    ValidationError,
)

# Backward compatibility - Runtime is now RuntimeV2
Runtime = RuntimeV2

__version__ = "0.1.38"
__all__ = [
    # Main runtime
    "Runtime",
    "RuntimeV2",
    "RuntimeConfig",
    # Models
    "Step",
    "StepResult",
    "DeploymentConfig",
    "DeployState",
    # Core
    "MarkpactParser",
    "BlockType",
    "ExecutorRegistry",
    "PluginLoader",
    "Plugin",
    # State & SSH
    "StateManager",
    "ConditionChecker",
    "SSHSessionManager",
    # Exceptions
    "MarkpactError",
    "ParseError",
    "ExecutionError",
    "PluginError",
    "ValidationError",
]
