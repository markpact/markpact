"""Plugin system for extensible executors.

Plugins can be loaded from:
1. Filesystem paths (plugin directories)
2. Python modules
3. Entry points (for pip-installed plugins)

Example plugin structure:
    my_plugin/
    ├── __init__.py
    └── executor.py
"""
import importlib
import importlib.util
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from .steps import Step, StepResult


class Plugin(ABC):
    """Base class for plugins.
    
    Plugins provide custom executors for specific actions.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @abstractmethod
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        """Execute the step using this plugin.
        
        Args:
            step: Step to execute
            context: Runtime context
            
        Returns:
            Output from execution
        """
        pass
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration."""
        pass
    
    def shutdown(self) -> None:
        """Cleanup when plugin is unloaded."""
        pass


class PluginLoader:
    """Loads plugins from various sources."""
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._loaded_paths: set = set()
    
    def load_from_path(self, path: Path) -> List[Plugin]:
        """Load plugins from a filesystem path.
        
        The path can be:
        - A directory containing plugin packages
        - A single plugin file
        
        Args:
            path: Path to plugins
            
        Returns:
            List of loaded plugins
        """
        path = Path(path).expanduser().resolve()
        
        if not path.exists():
            print(f"[markpact] Plugin path not found: {path}")
            return []
        
        if path in self._loaded_paths:
            return []
        
        self._loaded_paths.add(path)
        
        loaded = []
        
        if path.is_dir():
            # Load all plugins from directory
            for item in path.iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    plugin = self._load_from_directory(item)
                    if plugin:
                        loaded.append(plugin)
                elif item.is_file() and item.suffix == ".py":
                    plugin = self._load_from_file(item)
                    if plugin:
                        loaded.append(plugin)
        elif path.is_file() and path.suffix == ".py":
            plugin = self._load_from_file(path)
            if plugin:
                loaded.append(plugin)
        
        return loaded
    
    def load_from_module(self, module_name: str) -> Optional[Plugin]:
        """Load plugin from Python module.
        
        Args:
            module_name: Full module path (e.g., "my_package.plugins.my_plugin")
            
        Returns:
            Loaded plugin or None
        """
        try:
            module = importlib.import_module(module_name)
            
            # Look for Plugin class or instance
            if hasattr(module, "Plugin"):
                plugin_class = module.Plugin
                if issubclass(plugin_class, Plugin):
                    plugin = plugin_class()
                    self._plugins[plugin.name] = plugin
                    print(f"[markpact] Loaded plugin from module: {plugin.name}")
                    return plugin
            
            # Look for any Plugin instance
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, Plugin):
                    self._plugins[obj.name] = obj
                    print(f"[markpact] Loaded plugin from module: {obj.name}")
                    return obj
                    
        except Exception as e:
            print(f"[markpact] Failed to load plugin from module {module_name}: {e}")
        
        return None
    
    def _load_from_directory(self, path: Path) -> Optional[Plugin]:
        """Load plugin from a directory."""
        try:
            # Add parent to path for imports
            parent = str(path.parent)
            if parent not in sys.path:
                sys.path.insert(0, parent)
            
            # Import the module
            module_name = path.name
            spec = importlib.util.spec_from_file_location(
                module_name,
                path / "__init__.py"
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Look for plugin
                return self._extract_plugin_from_module(module, path.name)
                
        except Exception as e:
            print(f"[markpact] Failed to load plugin from {path}: {e}")
        
        return None
    
    def _load_from_file(self, path: Path) -> Optional[Plugin]:
        """Load plugin from a single file."""
        try:
            module_name = path.stem
            spec = importlib.util.spec_from_file_location(module_name, path)
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                return self._extract_plugin_from_module(module, path.stem)
                
        except Exception as e:
            print(f"[markpact] Failed to load plugin from {path}: {e}")
        
        return None
    
    def _extract_plugin_from_module(self, module, name: str) -> Optional[Plugin]:
        """Extract plugin instance from loaded module."""
        # Look for Plugin class
        if hasattr(module, "Plugin"):
            plugin_class = module.Plugin
            if isinstance(plugin_class, type) and issubclass(plugin_class, Plugin):
                plugin = plugin_class()
                self._plugins[plugin.name] = plugin
                print(f"[markpact] Loaded plugin: {plugin.name} v{plugin.version}")
                return plugin
        
        # Look for plugin instance
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if isinstance(obj, Plugin):
                self._plugins[obj.name] = obj
                print(f"[markpact] Loaded plugin: {obj.name} v{obj.version}")
                return obj
        
        return None
    
    def get(self, name: str) -> Optional[Plugin]:
        """Get plugin by name."""
        return self._plugins.get(name)
    
    def list(self) -> List[str]:
        """List all loaded plugin names."""
        return list(self._plugins.keys())
    
    def get_all(self) -> Dict[str, Plugin]:
        """Get all loaded plugins."""
        return self._plugins.copy()
    
    def clear(self) -> None:
        """Unload all plugins."""
        for plugin in self._plugins.values():
            try:
                plugin.shutdown()
            except:
                pass
        self._plugins.clear()
        self._loaded_paths.clear()


# Example built-in plugins

class BrowserReloadPlugin(Plugin):
    """Plugin to reload browser via CDP (Chrome DevTools Protocol)."""
    
    @property
    def name(self) -> str:
        return "browser_reload"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def execute(self, step: Step, context: Dict[str, Any]) -> str:
        """Reload browser via CDP."""
        import urllib.request
        
        host = step.params.get("host", "localhost")
        port = step.params.get("port", 9222)
        
        # Get CDP page list
        url = f"http://{host}:{port}/json/list"
        
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                import json
                pages = json.loads(response.read())
                
                # Reload each page
                for page in pages:
                    page_id = page.get("id")
                    reload_url = f"http://{host}:{port}/json/reload/{page_id}"
                    
                    reload_req = urllib.request.Request(
                        reload_url,
                        data=b'{}',
                        headers={"Content-Type": "application/json"},
                        method="PUT"
                    )
                    urllib.request.urlopen(reload_req, timeout=5)
                
                return f"Reloaded {len(pages)} browser pages"
                
        except Exception as e:
            return f"Browser reload failed (CDP may not be available): {e}"
