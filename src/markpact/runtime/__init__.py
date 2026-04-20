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

# Runtime v3: State Reconciliation Engine (Terraform-style for RPi/Edge)
from .core_v3 import RuntimeV3, RuntimeConfigV3
# Keep v2 for backward compatibility
from .core_v2 import RuntimeV2, RuntimeConfig as RuntimeConfigV2
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

# Default: v3 with state reconciliation
Runtime = RuntimeV3
RuntimeConfig = RuntimeConfigV3

__version__ = "0.1.39"
__all__ = [
    # Main runtime (v3 default)
    "Runtime",
    "RuntimeConfig",
    # v3 explicit
    "RuntimeV3",
    "RuntimeConfigV3",
    # v2 backward compatibility
    "RuntimeV2",
    "RuntimeConfigV2",
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
