"""Docker publisher — generate Dockerfile, build and push images."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from ..sandbox import Sandbox
from .helpers import _format_subprocess_failure
from .models import PublishConfig, PublishResult
from .pypi import _build_description


def generate_dockerfile(config: PublishConfig, sandbox: Sandbox, base_image: str = "python:3.12-slim") -> Path:
    """Generate Dockerfile for Docker publishing."""
    description = _build_description(config, sandbox.path)

    content = f'''FROM {base_image}

LABEL maintainer="{config.author}"
LABEL version="{config.version}"
LABEL description="{description}"

WORKDIR /app

COPY . .

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

CMD ["python", "-m", "http.server", "8000"]
'''

    path = sandbox.path / "Dockerfile"
    path.write_text(content)
    return path


def publish_docker(
    config: PublishConfig,
    sandbox: Sandbox,
    registry: str = "docker.io",
    tag: Optional[str] = None,
    verbose: bool = True,
) -> PublishResult:
    """Build and push Docker image to registry."""

    image_name = f"{registry}/{config.name}" if registry != "docker.io" else config.name
    image_tag = tag or config.version
    full_image = f"{image_name}:{image_tag}"

    if verbose:
        print(f"[markpact] Building Docker image: {full_image}...")

    # Generate Dockerfile if not exists
    dockerfile = sandbox.path / "Dockerfile"
    if not dockerfile.exists():
        generate_dockerfile(config, sandbox)

    # Build image
    build_result = subprocess.run(
        ["docker", "build", "-t", full_image, "-t", f"{image_name}:latest", "."],
        cwd=sandbox.path,
        capture_output=True,
        text=True,
    )

    if build_result.returncode != 0:
        return PublishResult(
            success=False,
            registry="docker",
            message=f"Build failed: {_format_subprocess_failure(build_result)}",
            version=config.version,
        )

    if verbose:
        print(f"[markpact] Pushing to {registry}...")

    # Push image
    push_result = subprocess.run(
        ["docker", "push", full_image],
        cwd=sandbox.path,
        capture_output=True,
        text=True,
    )

    if push_result.returncode != 0:
        return PublishResult(
            success=False,
            registry="docker",
            message=f"Push failed: {_format_subprocess_failure(push_result)}\nHint: docker login and ensure repository exists",
            version=config.version,
        )

    # Also push latest
    subprocess.run(
        ["docker", "push", f"{image_name}:latest"],
        cwd=sandbox.path,
        capture_output=True,
    )

    return PublishResult(
        success=True,
        registry="docker",
        message=f"Pushed to {registry}",
        version=config.version,
        url=f"https://hub.docker.com/r/{config.name}" if registry == "docker.io" else f"{registry}/{config.name}",
    )
