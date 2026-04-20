"""Exceptions for markpact runtime."""


class MarkpactError(Exception):
    """Base exception for all markpact errors."""
    pass


class ParseError(MarkpactError):
    """Error parsing markpact file."""
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"Parse error at line {line}: {message}" if line else message)


class ExecutionError(MarkpactError):
    """Error executing a step."""
    def __init__(self, message: str, step_id: str = ""):
        self.step_id = step_id
        prefix = f"Step '{step_id}': " if step_id else ""
        super().__init__(f"{prefix}{message}")


class PluginError(MarkpactError):
    """Error with plugin loading or execution."""
    def __init__(self, message: str, plugin_name: str = ""):
        self.plugin_name = plugin_name
        prefix = f"Plugin '{plugin_name}': " if plugin_name else ""
        super().__init__(f"{prefix}{message}")


class ValidationError(MarkpactError):
    """Error validating configuration or steps."""
    pass


class TimeoutError(ExecutionError):
    """Step execution timed out."""
    def __init__(self, step_id: str, timeout: int):
        super().__init__(f"Timed out after {timeout}s", step_id)
        self.timeout = timeout


class ConnectionError(ExecutionError):
    """Error connecting to remote host."""
    pass


class RollbackError(MarkpactError):
    """Error during rollback."""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error
