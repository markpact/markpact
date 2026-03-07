#!/usr/bin/env python3
"""Sync .bumpversion.toml with pyproject.toml version before bumping."""
import re
import sys
import argparse
from pathlib import Path

def get_pyproject_version():
    """Extract version from pyproject.toml."""
    pyproject = Path("pyproject.toml")
    content = pyproject.read_text()
    match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if match:
        return match.group(1)
    raise ValueError("Could not find version in pyproject.toml")

def get_bumpversion_version():
    """Extract version from .bumpversion.toml."""
    bumpversion = Path(".bumpversion.toml")
    content = bumpversion.read_text()
    match = re.search(r'^current_version = (.+)', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    raise ValueError("Could not find current_version in .bumpversion.toml")

def sync_bumpversion():
    """Sync .bumpversion.toml with pyproject.toml."""
    pyproject_ver = get_pyproject_version()
    bumpversion_ver = get_bumpversion_version()
    
    if pyproject_ver != bumpversion_ver:
        bumpversion = Path(".bumpversion.toml")
        content = bumpversion.read_text()
        content = re.sub(
            r'^current_version = .+',
            f'current_version = {pyproject_ver}',
            content,
            flags=re.MULTILINE
        )
        bumpversion.write_text(content)
        print(f"Synced .bumpversion.toml: {bumpversion_ver} -> {pyproject_ver}")
        return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync version files")
    parser.add_argument("--get", action="store_true", help="Get current version from pyproject.toml")
    args = parser.parse_args()
    
    if args.get:
        print(get_pyproject_version())
        sys.exit(0)
    
    changed = sync_bumpversion()
    sys.exit(0)
