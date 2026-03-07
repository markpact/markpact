"""Publish helpers — text extraction, inference, interactive config."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from .models import PublishConfig


def _slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "my-project"


def _first_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "My Project"


def _first_paragraph(markdown: str) -> str:
    lines = markdown.splitlines()
    started = False
    buf: list[str] = []
    for line in lines:
        if line.startswith("# "):
            started = True
            continue
        if not started:
            continue
        if line.strip() == "":
            if buf:
                break
            continue
        if line.startswith("## "):
            break
        buf.append(line.strip())
    return " ".join(buf).strip()


def _format_subprocess_failure(result) -> str:
    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()
    payload = stderr or stdout
    if not payload:
        return f"Command failed with exit code {result.returncode}"
    return payload[:400]


def _check_file_type(path: str) -> dict[str, bool]:
    """Check file type and return flags."""
    lower = path.lower()
    return {
        "package_json": lower.endswith("package.json"),
        "pyproject": lower.endswith("pyproject.toml") or lower.endswith("setup.py"),
        "dockerfile": lower.endswith("dockerfile"),
        "js": lower.endswith((".js", ".ts", ".mjs", ".cjs")),
        "python_pkg": lower.endswith("__init__.py"),
    }


def _analyze_blocks_for_types(blocks: list[object]) -> dict[str, bool]:
    """Analyze blocks to detect file types. Returns dict with flags."""
    flags = {
        "has_package_json": False,
        "has_pyproject": False,
        "has_dockerfile": False,
        "has_js": False,
        "has_python_pkg": False,
    }

    for b in blocks:
        kind = getattr(b, "kind", "")
        path = getattr(b, "get_path", lambda: None)()
        if kind == "file" and path:
            file_types = _check_file_type(path)
            flags["has_package_json"] |= file_types["package_json"]
            flags["has_pyproject"] |= file_types["pyproject"]
            flags["has_dockerfile"] |= file_types["dockerfile"]
            flags["has_js"] |= file_types["js"]
            flags["has_python_pkg"] |= file_types["python_pkg"]

    return flags


def _is_web_service(run_command: str | None) -> bool:
    """Check if run command indicates a web service."""
    if not run_command:
        return False
    web_indicators = ["uvicorn", "gunicorn", "flask run", "node ", "npm start"]
    return any(x in run_command for x in web_indicators)


def _detect_registry(flags: dict[str, bool], run_command: str | None) -> str:
    """Detect registry based on file types and run command."""
    if flags["has_package_json"] or flags["has_js"]:
        return "npm"

    if flags["has_dockerfile"] or _is_web_service(run_command):
        return "docker"

    if flags["has_pyproject"] or flags["has_python_pkg"]:
        return "pypi"

    return "unknown"


def _build_package_name(base_name: str, registry: str) -> str:
    """Build package name with registry-specific prefix/suffix."""
    # Add prefix to avoid PyPI collisions
    if not base_name.startswith("markpact-"):
        base_name = f"markpact-{base_name}"

    if registry == "docker":
        docker_ns = os.environ.get("MARKPACT_DOCKER_NAMESPACE") or os.environ.get("DOCKER_USERNAME") or ""
        return f"{docker_ns}/{base_name}".strip("/") if docker_ns else base_name

    if registry == "npm":
        npm_scope = os.environ.get("MARKPACT_NPM_SCOPE") or ""
        return f"@{npm_scope}/{base_name}" if npm_scope else base_name

    return base_name


def _get_default_author() -> str:
    """Get default author from environment variables."""
    return (
        os.environ.get("MARKPACT_AUTHOR")
        or os.environ.get("GIT_AUTHOR_NAME")
        or os.environ.get("USER")
        or ""
    )


def infer_publish_config(
    readme_path: Path,
    markdown: str,
    blocks: list[object],
    run_command: str | None,
) -> PublishConfig:
    """Infer a reasonable PublishConfig for READMEs without markpact:publish.

    Heuristics:
    - If package.json exists or there are JS/TS file blocks -> npm
    - If Dockerfile exists or run command indicates a web service -> docker
    - If pyproject/setup.py exists -> pypi
    """
    title = _first_heading(markdown)
    description = _first_paragraph(markdown)

    flags = _analyze_blocks_for_types(blocks)
    registry = _detect_registry(flags, run_command)

    base_name = _slugify(title)
    name = _build_package_name(base_name, registry)
    version = os.environ.get("MARKPACT_VERSION") or "0.1.0"

    return PublishConfig(
        registry=registry,
        name=name,
        version=version,
        description=description,
        author=_get_default_author(),
        license=os.environ.get("MARKPACT_LICENSE", "MIT"),
        repository=os.environ.get("MARKPACT_REPOSITORY", ""),
        keywords=[],
    )


def prompt_publish_config(config: PublishConfig) -> PublishConfig:
    """Interactively ask user for missing or important publish fields."""
    print("[markpact] No markpact:publish block found. Let's create one interactively.")
    print("[markpact] Press Enter to accept defaults.")

    def ask(label: str, current: str) -> str:
        value = input(f"{label} [{current}]: ").strip()
        return value or current

    config.registry = ask("Registry (pypi, pypi-test, npm, docker, github, ghcr)", config.registry)
    config.name = ask("Package/Image name", config.name)
    config.version = ask("Version", config.version)
    config.description = ask("Description", config.description)
    config.author = ask("Author", config.author)
    config.license = ask("License", config.license)
    config.repository = ask("Repository URL", config.repository)
    kw = ask("Keywords (comma-separated)", ",".join(config.keywords) if config.keywords else "")
    config.keywords = [k.strip() for k in kw.split(",") if k.strip()]
    return config


def ensure_publish_block_in_readme(readme_path: Path, config: PublishConfig) -> None:
    """Insert a markpact:publish block into README if none exists."""
    text = readme_path.read_text()
    if re.search(r"^```(?:[^\s]+\s+)?markpact:publish\b", text, re.MULTILINE):
        return

    lines: list[str] = [
        "```toml markpact:publish\n",
        f"registry = {config.registry}\n",
        f"name = {config.name}\n",
        f"version = {config.version}\n",
        f"description = {config.description}\n",
        f"author = {config.author}\n",
        f"license = {config.license}\n",
    ]
    if config.repository:
        lines.append(f"repository = {config.repository}\n")
    if config.keywords:
        lines.append(f"keywords = {', '.join(config.keywords)}\n")
    lines.append("```\n\n")

    block = "".join(lines)

    # Insert before first markpact:deps if possible
    m = re.search(r"^```(?:[^\s]+\s+)?markpact:deps\b", text, re.MULTILINE)
    if m:
        new_text = text[: m.start()] + block + text[m.start() :]
    else:
        new_text = text.rstrip() + "\n\n" + block
    readme_path.write_text(new_text)
