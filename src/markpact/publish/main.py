"""Main publish dispatch — parse_publish_block and publish facade."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..sandbox import Sandbox
from .models import PublishConfig, PublishResult
from .version import bump_version


def parse_publish_block(block_body: str, meta: str = "") -> PublishConfig:
    """Parse publish block content into config.

    Args:
        block_body: The body of the publish block
        meta: The meta line (first line after markpact:publish)
    """
    config = {
        "registry": "pypi",
        "name": "my-package",
        "version": "0.1.0",
        "description": "",
        "author": "",
        "license": "MIT",
        "repository": "",
        "keywords": [],
    }

    # Include meta in parsing if it contains config
    all_lines = []
    if meta and "=" in meta:
        all_lines.append(meta)
    all_lines.extend(block_body.strip().splitlines())

    for line in all_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, _, value = line.partition("=")
        elif ":" in line:
            key, _, value = line.partition(":")
        else:
            continue

        key = key.strip().lower()
        value = value.strip().strip('"\'')

        if key in config:
            if key == "keywords":
                config[key] = [k.strip() for k in value.split(",")]
            else:
                config[key] = value

    return PublishConfig(**config)


def publish(
    config: PublishConfig,
    sandbox: Sandbox,
    bump: Optional[str] = None,
    verbose: bool = True,
    source_readme_path: Optional[Path] = None,
) -> PublishResult:
    """Publish to specified registry.

    Args:
        config: Publish configuration
        sandbox: Sandbox with files to publish
        bump: Version bump type ("major", "minor", "patch") or None
        verbose: Print progress

    Returns:
        PublishResult
    """
    # Bump version if requested
    if bump:
        config.version = bump_version(config.version, bump)
        if verbose:
            print(f"[markpact] Bumped version to {config.version}")

    # Dispatch to appropriate publisher
    if config.registry == "pypi":
        from .pypi import publish_pypi
        return publish_pypi(config, sandbox, verbose=verbose, source_readme_path=source_readme_path)
    elif config.registry == "pypi-test":
        from .pypi import publish_pypi
        return publish_pypi(config, sandbox, test=True, verbose=verbose, source_readme_path=source_readme_path)
    elif config.registry == "npm":
        from .npm import publish_npm
        return publish_npm(config, sandbox, verbose=verbose)
    elif config.registry == "docker":
        from .docker_pub import publish_docker
        return publish_docker(config, sandbox, verbose=verbose)
    elif config.registry == "github":
        from .github import publish_github_packages
        return publish_github_packages(config, sandbox, verbose=verbose)
    elif config.registry == "ghcr":
        from .docker_pub import publish_docker
        return publish_docker(config, sandbox, registry="ghcr.io", verbose=verbose)
    else:
        return PublishResult(
            success=False,
            registry=config.registry,
            message=f"Unknown registry: {config.registry}",
            version=config.version,
        )
