"""GitHub Packages publisher — delegates to npm or Docker publishers."""

from __future__ import annotations

from ..sandbox import Sandbox
from .models import PublishConfig, PublishResult


def publish_github_packages(
    config: PublishConfig,
    sandbox: Sandbox,
    package_type: str = "npm",  # npm, docker, maven, nuget
    verbose: bool = True,
) -> PublishResult:
    """Publish to GitHub Packages."""

    if package_type == "npm":
        from .npm import publish_npm
        return publish_npm(
            config, sandbox,
            registry="https://npm.pkg.github.com",
            verbose=verbose,
        )
    elif package_type == "docker":
        from .docker_pub import publish_docker
        return publish_docker(
            config, sandbox,
            registry="ghcr.io",
            verbose=verbose,
        )
    else:
        return PublishResult(
            success=False,
            registry="github",
            message=f"Unsupported package type: {package_type}",
            version=config.version,
        )
