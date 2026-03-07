"""Template variable resolution for markpact:file blocks.

When a markpact:file block has template=true in its meta, its body contains
placeholder expressions instead of real values. During extraction, these
placeholders are resolved by:

1. Environment variables (os.environ)
2. A secrets file (~/.config/markpact/secrets.env or .markpact/secrets.env)
3. Interactive prompts (if stdin is a TTY)
4. Left as-is if no value is found (with a warning)

Supported placeholder formats:
    ${ask:Label}              — prompt user with "Label"
    ${ask:Label:-default}     — prompt with default value
    ${env:VAR_NAME}           — read from environment
    ${env:VAR_NAME:-default}  — read from environment with default
    ${VAR_NAME}               — read from env or secrets file
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional


# ─── Placeholder regex ────────────────────────────────────────────────────────

# ${ask:Label} or ${ask:Label:-default}
_ASK_RE = re.compile(r'\$\{ask:([^}:]+?)(?::-([^}]*))?\}')

# ${env:VAR} or ${env:VAR:-default}
_ENV_RE = re.compile(r'\$\{env:([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}')

# ${VAR_NAME} — generic variable (env or secrets)
_VAR_RE = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')


# ─── Secrets file loading ────────────────────────────────────────────────────

def _find_secrets_file(project_dir: Path | None = None) -> Path | None:
    """Find secrets file in order of priority.

    Checks:
    1. .markpact/secrets.env (project-local)
    2. ~/.config/markpact/secrets.env (user-global)
    """
    if project_dir:
        local = project_dir / ".markpact" / "secrets.env"
        if local.exists():
            return local

    global_path = Path.home() / ".config" / "markpact" / "secrets.env"
    if global_path.exists():
        return global_path

    return None


def load_secrets(project_dir: Path | None = None) -> dict[str, str]:
    """Load secrets from the secrets file.

    Returns:
        Dict of KEY=VALUE pairs from the secrets file.
    """
    secrets_file = _find_secrets_file(project_dir)
    if not secrets_file:
        return {}

    secrets: dict[str, str] = {}
    for line in secrets_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            # Strip optional quotes
            value = value.strip().strip('"').strip("'")
            secrets[key.strip()] = value
    return secrets


# ─── Resolution ──────────────────────────────────────────────────────────────

def _prompt_value(label: str, default: str | None = None) -> str:
    """Prompt user for a value interactively."""
    if default:
        answer = input(f"  [{label}] ({default}): ").strip()
        return answer if answer else default
    return input(f"  [{label}]: ").strip()


def resolve_template(
    body: str,
    *,
    secrets: dict[str, str] | None = None,
    interactive: bool = True,
    verbose: bool = False,
) -> tuple[str, list[str]]:
    """Resolve template placeholders in a block body.

    Args:
        body: The template text with placeholders.
        secrets: Pre-loaded secrets dict (KEY→VALUE).
        interactive: Whether to prompt for ${ask:...} values.
        verbose: Print resolution info.

    Returns:
        (resolved_body, list_of_warnings) — warnings for unresolved placeholders.
    """
    if secrets is None:
        secrets = {}

    warnings: list[str] = []
    resolved = body

    # Pass 1: ${ask:Label} and ${ask:Label:-default}
    def _resolve_ask(m: re.Match) -> str:
        label = m.group(1)
        default = m.group(2)  # may be None

        # Check secrets first (label as key)
        if label in secrets:
            if verbose:
                print(f"  [template] {label} ← secrets file")
            return secrets[label]

        # Check env (label as var name)
        env_val = os.environ.get(label)
        if env_val:
            if verbose:
                print(f"  [template] {label} ← environment")
            return env_val

        # Interactive prompt
        if interactive and sys.stdin.isatty():
            return _prompt_value(label, default)

        # Use default or leave placeholder
        if default is not None:
            return default
        warnings.append(f"Unresolved: ${{ask:{label}}} — set interactively or in secrets.env")
        return m.group(0)

    resolved = _ASK_RE.sub(_resolve_ask, resolved)

    # Pass 2: ${env:VAR} and ${env:VAR:-default}
    def _resolve_env(m: re.Match) -> str:
        var_name = m.group(1)
        default = m.group(2)
        val = os.environ.get(var_name)
        if val:
            return val
        if default is not None:
            return default
        warnings.append(f"Unresolved: ${{env:{var_name}}} — set environment variable")
        return m.group(0)

    resolved = _ENV_RE.sub(_resolve_env, resolved)

    # Pass 3: ${VAR_NAME} — generic (env > secrets > warning)
    def _resolve_var(m: re.Match) -> str:
        var_name = m.group(1)
        # Skip if it looks like a shell/taskfile variable pattern (not a template)
        # Template vars use simple ${NAME}, shell vars often use ${NAME:-default}
        # We only resolve bare ${NAME} patterns
        val = os.environ.get(var_name)
        if val:
            return val
        if var_name in secrets:
            return secrets[var_name]
        # Don't warn for generic vars — they might be shell vars left intentionally
        return m.group(0)

    resolved = _VAR_RE.sub(_resolve_var, resolved)

    return resolved, warnings


def has_template_placeholders(body: str) -> bool:
    """Check if body contains any template placeholders."""
    return bool(_ASK_RE.search(body) or _ENV_RE.search(body))
