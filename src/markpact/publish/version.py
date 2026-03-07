"""Version management — bump, extract, update."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


def bump_version(version: str, bump_type: str = "patch") -> str:
    """Bump semantic version.

    Args:
        version: Current version (e.g., "1.2.3")
        bump_type: Type of bump ("major", "minor", "patch")

    Returns:
        New version string
    """
    # Remove 'v' prefix if present
    v = version.lstrip("v")

    parts = v.split(".")
    if len(parts) != 3:
        parts = ["0", "0", "0"]

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2].split("-")[0])

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def extract_version_from_readme(readme_path: Path) -> Optional[str]:
    """Extract version from README markpact:publish block."""
    content = readme_path.read_text()

    # Look for version in publish block
    match = re.search(r'```(?:[^\s]+\s+)?markpact:publish[^\n]*\n(.*?)```', content, re.DOTALL)
    if match:
        block = match.group(1)
        version_match = re.search(r'version\s*[=:]\s*["\']?([^"\'\n]+)', block)
        if version_match:
            return version_match.group(1).strip()

    # Look for version in pyproject.toml style
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        return version_match.group(1)

    return "0.1.0"


def update_version_in_readme(readme_path: Path, new_version: str) -> bool:
    """Update version in README file."""
    content = readme_path.read_text()

    # Update version in publish block
    new_content = re.sub(
        r'(version\s*[=:]\s*["\']?)[\d\.]+(["\']?)',
        f'\\g<1>{new_version}\\g<2>',
        content
    )

    if new_content != content:
        readme_path.write_text(new_content)
        return True

    return False
