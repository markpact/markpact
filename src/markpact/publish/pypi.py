"""PyPI publisher — build and upload Python packages."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from ..sandbox import Sandbox
from .helpers import _format_subprocess_failure
from .models import PublishConfig, PublishResult


def get_license_classifier(license_name: str) -> str:
    """Map license name to PyPI classifier."""
    license_mapping = {
        "MIT": "MIT License",
        "Apache-2.0": "Apache Software License",
        "GPL-3.0": "GNU General Public License v3 (GPLv3)",
        "BSD-3-Clause": "BSD License",
        "ISC": "ISC License",
        "LGPL-3.0": "GNU Lesser General Public License v3 (LGPLv3)",
        "MPL-2.0": "Mozilla Public License 2.0 (MPL 2.0)",
        "Unlicense": "Unlicense",
    }
    return license_mapping.get(license_name, license_name)


def _extract_readme_description(base_path: Path) -> list[str]:
    """Extract description lines from README.md, stripping titles and code blocks."""
    readme_path = base_path / "README.md"
    if not readme_path.exists():
        return []
    lines = readme_path.read_text().splitlines()
    parts: list[str] = []
    in_codeblock = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("```"):
            if stripped.startswith("```"):
                in_codeblock = not in_codeblock
            continue
        if in_codeblock:
            continue
        parts.append(stripped)
    return parts


def _build_description(config: PublishConfig, base_path: Path) -> str:
    """Build truncated description from config + README."""
    parts = []
    if config.description:
        parts.append(config.description)
    parts.extend(_extract_readme_description(base_path))
    description = " ".join(parts)
    if len(description) > 500:
        description = description[:497] + "..."
    return description


def generate_pyproject_toml(config, sandbox, base_path=None, verbose=True):
    """Generate pyproject.toml for PyPI publishing."""
    if base_path is None:
        package_dir = sandbox.path / config.name
        base_path = package_dir if package_dir.exists() else sandbox.path

    description = _build_description(config, base_path)
    license_classifier = get_license_classifier(config.license)

    content = f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{config.name}"
version = "{config.version}"
description = "{description}"
readme = "README.md"
license = "{config.license}"
authors = [{{ name = "{config.author}" }}]
keywords = {json.dumps(config.keywords)}
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: {license_classifier}",
    "Operating System :: OS Independent",
]
requires-python = ">=3.10"

[project.urls]
Homepage = "{config.repository}"

[project.scripts]
markpact-example-pypi = "markpact_example_pypi.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["markpact_example_pypi"]
'''

    path = base_path / "pyproject.toml"
    path.write_text(content)
    return path


def _normalize_package_name(config: PublishConfig, verbose: bool) -> None:
    """Normalize package name for PyPI (underscores to hyphens)."""
    if "_" in config.name:
        if verbose:
            print(f"[markpact] NOTE: Package name '{config.name}' contains underscores. PyPI normalizes them to hyphens.")
        config.name = config.name.replace("_", "-")
        if verbose:
            print(f"[markpact] Normalized name to: {config.name}")


def _determine_base_path(config: PublishConfig, sandbox: Sandbox, verbose: bool) -> Path:
    """Determine base path for package files."""
    package_dir = sandbox.path / config.name
    package_dir_underscores = sandbox.path / config.name.replace("-", "_")
    if verbose:
        print(f"[markpact] DEBUG: package_dir_underscores = {package_dir_underscores}")
        print(f"[markpact] DEBUG: package_dir_underscores.exists() = {package_dir_underscores.exists()}")
    if package_dir.exists() or package_dir_underscores.exists():
        return package_dir_underscores if package_dir_underscores.exists() else package_dir
    return sandbox.path


def _detect_build_backend(pyproject_path: Path) -> str | None:
    """Detect build backend from pyproject.toml."""
    try:
        import tomllib
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("build-system", {}).get("build-backend")
    except ImportError:
        try:
            import tomli
            with pyproject_path.open("rb") as f:
                data = tomli.load(f)
            return data.get("build-system", {}).get("build-backend")
        except ImportError:
            content = pyproject_path.read_text()
            m = re.search(r"build-backend\s*=\s*['\"]([^'\"]+)['\"]", content)
            if m:
                return m.group(1)
    except Exception:
        content = pyproject_path.read_text()
        m = re.search(r"build-backend\s*=\s*['\"]([^'\"]+)['\"]", content)
        if m:
            return m.group(1)
    return None


def _ensure_build_backend(build_backend: str | None, verbose: bool) -> None:
    """Install missing build backend if needed."""
    if build_backend == "hatchling.build":
        try:
            import hatchling
        except ImportError:
            if verbose:
                print("[markpact] Installing missing build backend: hatchling")
            install_result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "hatchling"],
                capture_output=True,
                text=True,
            )
            if install_result.returncode != 0 and verbose:
                print("[markpact] WARNING: Failed to auto-install hatchling:")
                print(install_result.stderr[-500:] if install_result.stderr else install_result.stdout[-500:])


def _copy_readme(source_readme_path: Path | None, base_path: Path, config: PublishConfig, verbose: bool) -> None:
    """Copy README from source to sandbox or create minimal one."""
    if verbose:
        print(f"[markpact] DEBUG: source_readme_path = {source_readme_path}")
        print(f"[markpact] DEBUG: source_readme_path.exists() = {source_readme_path.exists() if source_readme_path else 'None'}")
        print(f"[markpact] DEBUG: base_path = {base_path}")

    if source_readme_path and source_readme_path.exists():
        if verbose:
            print(f"[markpact] Copying README from {source_readme_path}")
            print(f"[markpact] To {base_path / 'README.md'}")
        readme = base_path / "README.md"
        content = source_readme_path.read_text()
        if verbose:
            print(f"[markpact] README content length: {len(content)}")
        readme.write_text(content)
        if verbose:
            print(f"[markpact] README written, exists: {readme.exists()}")
    else:
        if verbose:
            print(f"[markpact] Creating minimal README in sandbox")
        readme = base_path / "README.md"
        if not readme.exists():
            readme.write_text(f"# {config.name}\n\n{config.description}\n")


def _run_build_command(base_path: Path) -> subprocess.CompletedProcess:
    """Run the build command and return result."""
    return subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=base_path,
        capture_output=True,
        text=True,
    )


def _print_build_output(build_result: subprocess.CompletedProcess) -> None:
    """Print build stdout/stderr for debugging."""
    print("[markpact] Build stdout/stderr:")
    print("--- STDOUT ---")
    print(build_result.stdout[-1000:] if build_result.stdout else "(empty)")
    print("--- STDERR ---")
    print(build_result.stderr[-1000:] if build_result.stderr else "(empty)")
    print("--- END ---")


def _get_build_error_hint(stdout: str, stderr: str) -> str | None:
    """Generate hint based on build error output. Returns hint or None."""
    combined = (stdout or "") + (stderr or "")
    if "No module named 'build'" in combined:
        return "[markpact] HINT: 'build' package not found. Install it with: pip install build"
    elif "Cannot import 'hatchling.build'" in combined or "Backend 'hatchling.build' is not available" in combined:
        return "[markpact] HINT: 'hatchling' backend not found. Install it with: pip install hatchling"
    return None


def _build_package(base_path: Path, verbose: bool) -> subprocess.CompletedProcess | None:
    """Build package and return result. Returns None on success, result on failure."""
    if verbose:
        print("[markpact] Building package...")

    build_result = _run_build_command(base_path)

    if build_result.returncode != 0:
        if verbose:
            _print_build_output(build_result)
            hint = _get_build_error_hint(build_result.stdout, build_result.stderr)
            if hint:
                print(hint)
        return build_result
    return None


def _setup_env_creds(test: bool) -> tuple[dict, bool]:
    """Setup environment with PyPI credentials. Returns (env, has_env_creds)."""
    env = os.environ.copy()
    env.setdefault("TWINE_NON_INTERACTIVE", "1")
    token_env = "MARKPACT_TESTPYPI_TOKEN" if test else "MARKPACT_PYPI_TOKEN"
    token = env.get(token_env, "").strip()
    if token:
        env.setdefault("TWINE_USERNAME", "__token__")
        env.setdefault("TWINE_PASSWORD", token)

    has_env_creds = bool(env.get("TWINE_USERNAME")) and bool(env.get("TWINE_PASSWORD"))
    return env, has_env_creds


def _parse_pypirc_section(pypirc_path: Path, test: bool, verbose: bool) -> bool:
    """Parse ~/.pypirc and check for valid section. Returns True if valid creds found."""
    if not pypirc_path.exists():
        return False

    if verbose:
        print(f"[markpact] Found ~/.pypirc at: {pypirc_path}")

    try:
        import configparser
        cp = configparser.ConfigParser()
        cp.read(pypirc_path)
        section = "testpypi" if test else "pypi"

        if section not in cp:
            if verbose:
                print(f"[markpact] NOTE: ~/.pypirc exists but section [{section}] is missing")
            return False

        u = (cp.get(section, "username", fallback="") or "").strip()
        p = (cp.get(section, "password", fallback="") or "").strip()

        if verbose:
            print(f"[markpact] ~/.pypirc section [{section}] parsed:")
            print(f"    username = {u}")
            masked = (p[:8] + "...") if len(p) > 8 else ("***" if p else "(empty)")
            print(f"    password = {masked}")

        if not u or not p:
            print(f"[markpact] NOTE: ~/.pypirc section [{section}] is missing username/password. Ensure the INI keys are NOT indented.")
            return False

        return True

    except Exception as e:
        if verbose:
            print(f"[markpact] WARNING: Failed to parse ~/.pypirc: {e}")
        return False


def _check_pypi_credentials(test: bool, verbose: bool) -> tuple[bool, Path | None]:
    """Check PyPI credentials and return (has_creds, pypirc_path)."""
    env, has_env_creds = _setup_env_creds(test)

    pypirc_path = Path.home().joinpath(".pypirc")
    has_pypirc_creds = _parse_pypirc_section(pypirc_path, test, verbose)

    if not has_env_creds and not has_pypirc_creds and verbose:
        where = "TestPyPI" if test else "PyPI"
        token_env = "MARKPACT_TESTPYPI_TOKEN" if test else "MARKPACT_PYPI_TOKEN"
        print(f"[markpact] NOTE: No Twine credentials detected for {where}.")
        print(f"[markpact] TIP: set {token_env}=pypi-... or configure ~/.pypirc")

    return has_env_creds or has_pypirc_creds, pypirc_path if has_pypirc_creds or pypirc_path.exists() else None


def _setup_upload_env(test: bool) -> dict:
    """Setup environment for PyPI upload with token credentials."""
    env = os.environ.copy()
    env.setdefault("TWINE_NON_INTERACTIVE", "1")
    token_env = "MARKPACT_TESTPYPI_TOKEN" if test else "MARKPACT_PYPI_TOKEN"
    token = env.get(token_env, "").strip()
    if token:
        env.setdefault("TWINE_USERNAME", "__token__")
        env.setdefault("TWINE_PASSWORD", token)
    return env


def _build_upload_cmd(test: bool, pypirc_path: Path | None, verbose: bool) -> list[str]:
    """Build twine upload command with appropriate flags."""
    upload_cmd = [sys.executable, "-m", "twine", "upload"]
    if test:
        upload_cmd.extend(["--repository", "testpypi"])
    if pypirc_path and pypirc_path.exists():
        upload_cmd.extend(["--config-file", str(pypirc_path)])
    if verbose:
        upload_cmd.append("--verbose")
    upload_cmd.append("dist/*")
    return upload_cmd


def _get_upload_error_hint(payload: str, stdout: str, test: bool, config: PublishConfig) -> str:
    """Generate appropriate hint based on upload error."""
    where = "TestPyPI" if test else "PyPI"
    token_env = "MARKPACT_TESTPYPI_TOKEN" if test else "MARKPACT_PYPI_TOKEN"

    if "File already exists" in payload or "file-name-reuse" in payload or "File already exists" in stdout:
        return f"Hint: a file for this version already exists on {where}. Try bumping the version with --bump patch/minor/major."

    if "too similar to an existing project" in payload or "too similar to an existing project" in stdout:
        return f"Hint: the package name is too similar to an existing project on {where}. Change the 'name =' in the markpact:publish block."

    return f"Hint: configure ~/.pypirc or set TWINE_USERNAME/TWINE_PASSWORD (or {token_env}).\nTarget: {where}"


def _upload_to_pypi(base_path: Path, test: bool, config: PublishConfig, pypirc_path: Path | None, verbose: bool) -> PublishResult | None:
    """Upload package to PyPI. Returns None on success, PublishResult on failure."""
    if verbose:
        print("[markpact] Uploading to PyPI...")

    env = _setup_upload_env(test)
    upload_cmd = _build_upload_cmd(test, pypirc_path, verbose)

    if verbose:
        print(f"[markpact] Running twine command:")
        print(f"    {' '.join(upload_cmd)}")

    upload_result = subprocess.run(
        " ".join(upload_cmd),
        shell=True,
        cwd=base_path,
        capture_output=True,
        text=True,
        env=env,
    )

    if upload_result.returncode != 0:
        where = "TestPyPI" if test else "PyPI"
        if verbose:
            print("[markpact] Full twine stdout/stderr for debugging:")
            print("--- STDOUT ---")
            print(upload_result.stdout[-2000:] if upload_result.stdout else "(empty)")
            print("--- STDERR ---")
            print(upload_result.stderr[-2000:] if upload_result.stderr else "(empty)")
            print("--- END ---")

        payload = _format_subprocess_failure(upload_result)
        stdout = (upload_result.stdout or "")
        hint = _get_upload_error_hint(payload, stdout, test, config)

        return PublishResult(
            success=False,
            registry="pypi",
            message=f"Upload failed: {payload}\n{hint}",
            version=config.version,
        )
    return None


def publish_pypi(
    config: PublishConfig,
    sandbox: Sandbox,
    test: bool = False,
    verbose: bool = True,
    source_readme_path: Optional[Path] = None,
) -> PublishResult:
    """Publish package to PyPI."""

    if verbose:
        print(f"[markpact] Publishing {config.name} v{config.version} to {'TestPyPI' if test else 'PyPI'}...")

    _normalize_package_name(config, verbose)
    base_path = _determine_base_path(config, sandbox, verbose)
    generate_pyproject_toml(config, sandbox, base_path, verbose)

    pyproject_path = base_path / "pyproject.toml"
    if pyproject_path.exists():
        build_backend = _detect_build_backend(pyproject_path)
        _ensure_build_backend(build_backend, verbose)

    _copy_readme(source_readme_path, base_path, config, verbose)

    build_result = _build_package(base_path, verbose)
    if build_result:
        return PublishResult(
            success=False,
            registry="pypi",
            message=f"Build failed: {_format_subprocess_failure(build_result)}",
            version=config.version,
        )

    _, pypirc_path = _check_pypi_credentials(test, verbose)

    upload_result = _upload_to_pypi(base_path, test, config, pypirc_path, verbose)
    if upload_result:
        return upload_result

    url = f"https://{'test.' if test else ''}pypi.org/project/{config.name}/"
    return PublishResult(
        success=True,
        registry="pypi",
        message=f"Published to {'TestPyPI' if test else 'PyPI'}",
        version=config.version,
        url=url,
    )
