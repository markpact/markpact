"""Publish package — multi-registry publisher for markpact projects.

Refactored from monolithic publisher.py (1227L, 48 funcs) into:
    publish/
    ├── __init__.py      — re-exports for backward compat
    ├── models.py        — PublishConfig, PublishResult
    ├── helpers.py       — inference, interactive config, text utils
    ├── version.py       — bump_version, extract/update version
    ├── llm_config.py    — LLM-based config generation
    ├── pypi.py          — PyPI publisher
    ├── npm.py           — npm publisher
    ├── docker_pub.py    — Docker publisher
    ├── github.py        — GitHub Packages publisher
    └── main.py          — parse_publish_block, publish dispatch
"""

from .models import PublishConfig, PublishResult
from .main import parse_publish_block, publish
from .helpers import (
    infer_publish_config,
    prompt_publish_config,
    ensure_publish_block_in_readme,
    _slugify,
    _first_heading,
    _first_paragraph,
    _format_subprocess_failure,
)
from .version import bump_version, extract_version_from_readme, update_version_in_readme
from .llm_config import generate_publish_config_with_llm
from .pypi import publish_pypi, generate_pyproject_toml
from .npm import publish_npm, generate_package_json
from .docker_pub import publish_docker, generate_dockerfile
from .github import publish_github_packages

__all__ = [
    "PublishConfig",
    "PublishResult",
    "parse_publish_block",
    "publish",
    "infer_publish_config",
    "prompt_publish_config",
    "ensure_publish_block_in_readme",
    "bump_version",
    "extract_version_from_readme",
    "update_version_in_readme",
    "generate_publish_config_with_llm",
    "publish_pypi",
    "publish_npm",
    "publish_docker",
    "publish_github_packages",
    "generate_pyproject_toml",
    "generate_package_json",
    "generate_dockerfile",
]
