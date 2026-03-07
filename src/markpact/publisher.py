"""Backward-compat shim — re-exports from publish/ package.

All functionality has been moved to markpact.publish subpackage.
This file exists solely so existing ``from markpact.publisher import X`` works.
"""

from .publish import *  # noqa: F401,F403
from .publish import (  # explicit re-exports used by CLI
    PublishConfig,
    PublishResult,
    parse_publish_block,
    publish,
    infer_publish_config,
    prompt_publish_config,
    generate_publish_config_with_llm,
    bump_version,
    update_version_in_readme,
    extract_version_from_readme,
    ensure_publish_block_in_readme,
    publish_pypi,
    publish_npm,
    publish_docker,
    publish_github_packages,
    generate_pyproject_toml,
    generate_package_json,
    generate_dockerfile,
)
