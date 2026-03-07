#!/usr/bin/env python3
"""Sync .bumpversion.toml with pyproject.toml version before bumping."""
import re
import sys
import argparse
import subprocess
from pathlib import Path
from packaging import version

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

def set_pyproject_version(new_ver):
    """Set version in pyproject.toml."""
    pyproject = Path("pyproject.toml")
    content = pyproject.read_text()
    content = re.sub(
        r'^version = "[^"]+"',
        f'version = "{new_ver}"',
        content,
        flags=re.MULTILINE
    )
    pyproject.write_text(content)

def set_bumpversion_version(new_ver):
    """Set version in .bumpversion.toml."""
    bumpversion = Path(".bumpversion.toml")
    content = bumpversion.read_text()
    content = re.sub(
        r'^current_version = .+',
        f'current_version = {new_ver}',
        content,
        flags=re.MULTILINE
    )
    bumpversion.write_text(content)

def tag_exists(tag):
    """Check if git tag exists."""
    try:
        subprocess.check_output(['git', 'rev-parse', f'refs/tags/{tag}'], stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def get_next_version(current):
    """Get next patch version."""
    parts = current.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    return '.'.join(parts)

def sync_versions():
    """Sync both version files to the MAX version, ensuring next version tag doesn't exist."""
    pyproject_ver = get_pyproject_version()
    bumpversion_ver = get_bumpversion_version()
    
    # Take the higher version
    max_ver = max(pyproject_ver, bumpversion_ver, key=lambda x: version.parse(x))
    
    # Keep incrementing until we find a version without a git tag
    target_ver = max_ver
    while tag_exists(f'v{target_ver}'):
        target_ver = get_next_version(target_ver)
    
    changed = False
    if pyproject_ver != target_ver:
        set_pyproject_version(target_ver)
        print(f"Updated pyproject.toml: {pyproject_ver} -> {target_ver}")
        changed = True
    
    if bumpversion_ver != target_ver:
        set_bumpversion_version(target_ver)
        print(f"Updated .bumpversion.toml: {bumpversion_ver} -> {target_ver}")
        changed = True
    
    if not changed:
        print(f"Versions already synced at {target_ver}")
    
    return target_ver

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync version files")
    parser.add_argument("--get", action="store_true", help="Get current version from pyproject.toml")
    args = parser.parse_args()
    
    if args.get:
        print(get_pyproject_version())
        sys.exit(0)
    
    target = sync_versions()
    print(f"Ready to bump to: {get_next_version(target)}")
    sys.exit(0)
