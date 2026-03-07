"""Tests for markpact.auto_fix — error detection, port fixing, module extraction."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from markpact.auto_fix import (
    detect_error_type,
    fix_port_in_readme,
    extract_module_name,
    add_missing_dependency,
)


# ── detect_error_type (fallback path, no fixop) ─────────────────────────────

class TestDetectErrorType:
    def test_port_in_use(self):
        assert detect_error_type("OSError: [Errno 98] Address already in use") == "port_in_use"

    def test_missing_module(self):
        assert detect_error_type("ModuleNotFoundError: No module named 'flask'") == "missing_module"

    def test_syntax_error(self):
        assert detect_error_type("SyntaxError: invalid syntax") == "syntax_error"

    def test_import_error(self):
        assert detect_error_type("ImportError: cannot import name 'foo'") == "import_error"

    def test_unknown_error(self):
        assert detect_error_type("Something completely different") is None

    def test_case_insensitive(self):
        assert detect_error_type("ADDRESS ALREADY IN USE") == "port_in_use"
        assert detect_error_type("MODULENOTFOUNDERROR: no module") == "missing_module"

    def test_empty_output(self):
        assert detect_error_type("") is None


# ── fix_port_in_readme ───────────────────────────────────────────────────────

class TestFixPortInReadme:
    def test_replaces_env_var_port(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("uvicorn app:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}\n")
        assert fix_port_in_readme(readme, 9000) is True
        assert "${MARKPACT_PORT:-9000}" in readme.read_text()

    def test_replaces_direct_port(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("uvicorn app:app --port 8000\n")
        assert fix_port_in_readme(readme, 9000) is True
        assert "--port 9000" in readme.read_text()

    def test_no_port_returns_false(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("python script.py\n")
        assert fix_port_in_readme(readme, 9000) is False


# ── extract_module_name ──────────────────────────────────────────────────────

class TestExtractModuleName:
    def test_single_module(self):
        assert extract_module_name("ModuleNotFoundError: No module named 'flask'") == "flask"

    def test_dotted_module(self):
        assert extract_module_name("No module named 'requests.auth'") == "requests"

    def test_double_quotes(self):
        assert extract_module_name('No module named "uvicorn"') == "uvicorn"

    def test_no_match(self):
        assert extract_module_name("Some other error") is None


# ── add_missing_dependency ───────────────────────────────────────────────────

class TestAddMissingDependency:
    def test_adds_to_deps_block(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Project\n\n"
            "```text markpact:deps python\n"
            "flask\n"
            "```\n"
        )
        assert add_missing_dependency(readme, "requests") is True
        text = readme.read_text()
        assert "requests" in text
        assert "flask" in text

    def test_already_present(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "```text markpact:deps python\n"
            "flask\n"
            "```\n"
        )
        assert add_missing_dependency(readme, "flask") is False

    def test_no_deps_block(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Project\nNo deps block here.\n")
        assert add_missing_dependency(readme, "flask") is False
