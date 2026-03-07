"""npm publisher — generate package.json and publish to npm."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..sandbox import Sandbox
from .helpers import _format_subprocess_failure
from .models import PublishConfig, PublishResult
from .pypi import _extract_readme_description


def _build_npm_description(config: PublishConfig, sandbox: Sandbox) -> str:
    """Build truncated description from config + README."""
    parts = []
    if config.description:
        parts.append(config.description)
    parts.extend(_extract_readme_description(sandbox.path))
    description = " ".join(parts)
    if len(description) > 500:
        description = description[:497] + "..."
    return description


def generate_package_json(config: PublishConfig, sandbox: Sandbox) -> Path:
    """Generate package.json for npm publishing."""
    description = _build_npm_description(config, sandbox)

    package = {
        "name": config.name,
        "version": config.version,
        "description": description,
        "main": "index.js",
        "scripts": {
            "test": 'echo "No tests specified" && exit 0'
        },
        "keywords": config.keywords,
        "author": config.author,
        "license": config.license,
        "repository": {
            "type": "git",
            "url": config.repository
        } if config.repository else {}
    }

    path = sandbox.path / "package.json"
    path.write_text(json.dumps(package, indent=2))
    return path


def publish_npm(
    config: PublishConfig,
    sandbox: Sandbox,
    registry: str = "https://registry.npmjs.org",
    verbose: bool = True,
) -> PublishResult:
    """Publish package to npm registry."""

    if verbose:
        print(f"[markpact] Publishing {config.name} v{config.version} to npm...")

    # Generate package.json if not exists
    package_json = sandbox.path / "package.json"
    if not package_json.exists():
        generate_package_json(config, sandbox)

    # Create index.js if not exists
    index_js = sandbox.path / "index.js"
    if not index_js.exists():
        index_js.write_text(f'module.exports = {{ name: "{config.name}", version: "{config.version}" }};\n')

    # Publish
    cmd = ["npm", "publish", "--access", "public"]
    if registry != "https://registry.npmjs.org":
        cmd.extend(["--registry", registry])

    result = subprocess.run(
        cmd,
        cwd=sandbox.path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return PublishResult(
            success=False,
            registry="npm",
            message=f"Publish failed: {_format_subprocess_failure(result)}\nHint: run npm login and ensure package name is valid",
            version=config.version,
        )

    return PublishResult(
        success=True,
        registry="npm",
        message="Published to npm",
        version=config.version,
        url=f"https://www.npmjs.com/package/{config.name}",
    )
