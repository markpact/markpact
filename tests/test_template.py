"""Tests for markpact.template — placeholder resolution for template=true blocks."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from markpact.template import (
    resolve_template,
    has_template_placeholders,
    load_secrets,
    _find_secrets_file,
)


class TestHasTemplatePlaceholders:
    def test_ask_placeholder(self):
        assert has_template_placeholders("KEY=${ask:API Key}")

    def test_ask_with_default(self):
        assert has_template_placeholders("HOST=${ask:Hostname:-localhost}")

    def test_env_placeholder(self):
        assert has_template_placeholders("KEY=${env:MY_API_KEY}")

    def test_env_with_default(self):
        assert has_template_placeholders("PORT=${env:PORT:-8080}")

    def test_no_placeholders(self):
        assert not has_template_placeholders("KEY=some_value")

    def test_generic_var_not_detected(self):
        # Generic ${VAR} is not considered a template placeholder
        # (it could be a shell variable)
        assert not has_template_placeholders("KEY=${HOME}")


class TestResolveTemplate:
    def test_ask_from_secrets(self):
        body = "API_KEY=${ask:OpenRouter API key}"
        secrets = {"OpenRouter API key": "sk-real-key"}
        result, warnings = resolve_template(body, secrets=secrets, interactive=False)
        assert result == "API_KEY=sk-real-key"
        assert not warnings

    def test_ask_from_env(self):
        body = "API_KEY=${ask:MY_KEY}"
        with patch.dict(os.environ, {"MY_KEY": "env-value"}):
            result, warnings = resolve_template(body, interactive=False)
        assert result == "API_KEY=env-value"
        assert not warnings

    def test_ask_with_default_no_input(self):
        body = "HOST=${ask:Production host:-example.com}"
        result, warnings = resolve_template(body, interactive=False)
        assert result == "HOST=example.com"
        assert not warnings

    def test_ask_unresolved_warning(self):
        body = "API_KEY=${ask:Secret Key}"
        result, warnings = resolve_template(body, interactive=False)
        assert result == "API_KEY=${ask:Secret Key}"
        assert len(warnings) == 1
        assert "Secret Key" in warnings[0]

    def test_env_resolved(self):
        body = "PORT=${env:MY_PORT}"
        with patch.dict(os.environ, {"MY_PORT": "9090"}):
            result, warnings = resolve_template(body, interactive=False)
        assert result == "PORT=9090"
        assert not warnings

    def test_env_with_default(self):
        body = "PORT=${env:NONEXISTENT_PORT:-3000}"
        result, warnings = resolve_template(body, interactive=False)
        assert result == "PORT=3000"
        assert not warnings

    def test_env_unresolved_warning(self):
        body = "KEY=${env:TOTALLY_MISSING_VAR}"
        # Make sure it's not in env
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TOTALLY_MISSING_VAR", None)
            result, warnings = resolve_template(body, interactive=False)
        assert "${env:TOTALLY_MISSING_VAR}" in result
        assert len(warnings) == 1

    def test_generic_var_from_env(self):
        body = "HOME=${HOME}"
        with patch.dict(os.environ, {"HOME": "/users/test"}):
            result, warnings = resolve_template(body, interactive=False)
        assert result == "HOME=/users/test"
        assert not warnings

    def test_generic_var_from_secrets(self):
        body = "TOKEN=${MY_TOKEN}"
        secrets = {"MY_TOKEN": "secret123"}
        result, warnings = resolve_template(body, secrets=secrets, interactive=False)
        assert result == "TOKEN=secret123"
        assert not warnings

    def test_generic_var_unresolved_no_warning(self):
        """Generic ${VAR} left as-is without warning (might be intentional shell var)."""
        body = "PATH=${SOME_PATH}"
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SOME_PATH", None)
            result, warnings = resolve_template(body, secrets={}, interactive=False)
        assert result == "PATH=${SOME_PATH}"
        assert not warnings

    def test_multiple_placeholders(self):
        body = (
            "API_KEY=${ask:API Key:-changeme}\n"
            "HOST=${env:PROD_HOST:-prod.example.com}\n"
            "PORT=8080\n"
        )
        result, warnings = resolve_template(body, interactive=False)
        assert "API_KEY=changeme" in result
        assert "HOST=prod.example.com" in result
        assert "PORT=8080" in result
        assert not warnings

    def test_interactive_prompt(self):
        body = "KEY=${ask:Enter API key}"
        with patch("markpact.template._prompt_value", return_value="user-input"):
            with patch("sys.stdin") as mock_stdin:
                mock_stdin.isatty.return_value = True
                result, warnings = resolve_template(body, interactive=True)
        assert result == "KEY=user-input"
        assert not warnings


class TestLoadSecrets:
    def test_load_from_project(self, tmp_path):
        secrets_dir = tmp_path / ".markpact"
        secrets_dir.mkdir()
        secrets_file = secrets_dir / "secrets.env"
        secrets_file.write_text("API_KEY=sk-123\nHOST=prod.example.com\n")

        result = load_secrets(tmp_path)
        assert result == {"API_KEY": "sk-123", "HOST": "prod.example.com"}

    def test_skip_comments_and_empty(self, tmp_path):
        secrets_dir = tmp_path / ".markpact"
        secrets_dir.mkdir()
        secrets_file = secrets_dir / "secrets.env"
        secrets_file.write_text("# comment\n\nKEY=val\n")

        result = load_secrets(tmp_path)
        assert result == {"KEY": "val"}

    def test_strip_quotes(self, tmp_path):
        secrets_dir = tmp_path / ".markpact"
        secrets_dir.mkdir()
        secrets_file = secrets_dir / "secrets.env"
        secrets_file.write_text('KEY="quoted-value"\nKEY2=\'single\'\n')

        result = load_secrets(tmp_path)
        assert result == {"KEY": "quoted-value", "KEY2": "single"}

    def test_no_secrets_file(self, tmp_path):
        result = load_secrets(tmp_path)
        assert result == {}


class TestFindSecretsFile:
    def test_project_local(self, tmp_path):
        secrets_dir = tmp_path / ".markpact"
        secrets_dir.mkdir()
        f = secrets_dir / "secrets.env"
        f.write_text("KEY=val")
        assert _find_secrets_file(tmp_path) == f

    def test_none_when_missing(self, tmp_path):
        assert _find_secrets_file(tmp_path) is None
