"""Pack directory contents into markpact README.md format.

Converts an existing project directory into a markpact-formatted README.md
with all files as markpact:file blocks.
"""

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Default patterns to exclude
DEFAULT_EXCLUDE = {
    ".git", "__pycache__", "venv", ".venv", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dylib", "*.dll",
    ".DS_Store", "Thumbs.db", ".env", ".env.*",
    "*.egg-info", "build", "dist", ".gitignore",
}

# Language mapping for file extensions
LANG_EXTENSIONS = {
    ".py": "python",
    ".pyw": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".ps1": "powershell",
    ".md": "markdown",
    ".txt": "text",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".kt": "kotlin",
    ".scala": "scala",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".rb": "ruby",
    ".r": "r",
    ".swift": "swift",
    ".sql": "sql",
    ".dockerfile": "dockerfile",
    "dockerfile": "dockerfile",
    ".xml": "xml",
    ".svg": "svg",
    ".graphql": "graphql",
    ".gql": "graphql",
}


@dataclass
class PackResult:
    """Result of packing a directory."""
    source_dir: Path
    output_path: Path
    files_packed: int
    files_skipped: int
    blocks: list[dict] = field(default_factory=list)
    dry_run: bool = False
    success: bool = True
    message: str = ""

    def summary(self) -> str:
        """Return human-readable summary."""
        mode = "[DRY-RUN] " if self.dry_run else ""
        lines = [
            f"{mode}Packed {self.source_dir} → {self.output_path}",
            f"  Files packed: {self.files_packed}",
            f"  Files skipped: {self.files_skipped}",
        ]
        if self.message:
            lines.append(f"  Message: {self.message}")
        return "\n".join(lines)


def _should_include(path: Path, exclude_patterns: set[str]) -> bool:
    """Check if file should be included based on exclude patterns."""
    # Check path parts
    for part in path.parts:
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(part, pattern):
                return False
    # Check full filename
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(path.name, pattern):
            return False
    return True


def _get_language(path: Path) -> str:
    """Determine language for file path."""
    lower_name = path.name.lower()
    if lower_name == "dockerfile":
        return "dockerfile"
    if lower_name == "makefile":
        return "makefile"
    return LANG_EXTENSIONS.get(path.suffix.lower(), "text")


def _detect_file_indicators(files: list[Path]) -> dict[str, bool]:
    """Detect framework indicators based on file names."""
    return {
        "has_main_py": any(f.name.lower() == "main.py" for f in files),
        "has_app_py": any(f.name.lower() == "app.py" for f in files),
        "has_package_json": any(f.name.lower() == "package.json" for f in files),
        "has_requirements": any(f.name.lower() == "requirements.txt" for f in files),
    }


def _detect_framework_from_content(files: list[Path]) -> tuple[bool, bool]:
    """Detect FastAPI and Flask from Python file content."""
    has_fastapi = False
    has_flask = False
    
    for f in files:
        if f.suffix == ".py":
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")[:2000]
                if "FastAPI" in content:
                    has_fastapi = True
                if "Flask(" in content:
                    has_flask = True
            except Exception:
                pass
    
    return has_fastapi, has_flask


def _build_run_command(indicators: dict[str, bool], has_fastapi: bool, has_flask: bool) -> Optional[str]:
    """Build run command based on detected indicators."""
    if has_fastapi:
        if indicators["has_main_py"]:
            return "uvicorn main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}"
        if indicators["has_app_py"]:
            return "uvicorn app:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}"
        return "uvicorn main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}"
    
    if has_flask:
        return "flask run --host 0.0.0.0 --port ${MARKPACT_PORT:-5000}"
    
    if indicators["has_package_json"]:
        return "npm start"
    
    if indicators["has_main_py"]:
        return "python main.py"
    
    if indicators["has_app_py"]:
        return "python app.py"
    
    return None


def _detect_run_command(files: list[Path]) -> Optional[str]:
    """Try to detect run command based on project files."""
    indicators = _detect_file_indicators(files)
    has_fastapi, has_flask = _detect_framework_from_content(files)
    return _build_run_command(indicators, has_fastapi, has_flask)


def _collect_files(
    src: Path,
    output_path: Path,
    exclude_patterns: set[str],
    include_patterns: Optional[list[str]],
    verbose: bool
) -> list[Path]:
    """Collect files to pack, applying exclude/include filters."""
    files_to_pack: list[Path] = []
    for file_path in sorted(src.rglob("*")):
        if not file_path.is_file():
            continue
        
        # Skip output file
        if file_path.resolve() == output_path.resolve():
            continue
        
        # Check if file is inside source dir (in case of symlinks)
        try:
            rel_path = file_path.relative_to(src)
        except ValueError:
            continue
        
        # Apply exclude patterns
        if not _should_include(rel_path, exclude_patterns):
            continue
        
        # Apply include patterns if specified
        if include_patterns:
            matched = any(fnmatch.fnmatch(str(rel_path), p) for p in include_patterns)
            if not matched:
                continue
        
        files_to_pack.append(file_path)
    
    if verbose:
        print(f"[markpact] Found {len(files_to_pack)} files to pack")
    
    return files_to_pack


def _generate_readme_content(
    files_to_pack: list[Path],
    src: Path,
    project_title: str,
    desc: str,
    run_command: Optional[str],
    dry_run: bool
) -> tuple[list[str], list[dict]]:
    """Generate README content and block info. Returns (lines, blocks_info)."""
    lines: list[str] = [
        f"# {project_title}",
        "",
        desc,
        "",
        "## Files",
        "",
    ]
    
    blocks_info: list[dict] = []
    
    for file_path in files_to_pack:
        rel_path = file_path.relative_to(src)
        lang = _get_language(file_path)
        
        blocks_info.append({
            "path": str(rel_path),
            "language": lang,
        })
        
        if dry_run:
            continue
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            content = f"# Error reading file: {e}"
        
        lines.append(f"```\x60{lang} markpact:file path={rel_path}")
        lines.append(content)
        lines.append("```")
        lines.append("")
    
    # Add deps section placeholder
    lines.extend([
        "## Dependencies",
        "",
        "```text markpact:deps python",
        "# Add your dependencies here",
        "# fastapi",
        "# uvicorn",
        "```",
        "",
    ])
    
    # Determine and add run command
    final_run = run_command
    if not final_run and not dry_run:
        final_run = _detect_run_command(files_to_pack)
    
    if final_run:
        lines.extend([
            "## Run",
            "",
            "```bash markpact:run",
            final_run,
            "```",
            "",
        ])
    
    return lines, blocks_info


def _write_output(
    output_path: Path,
    lines: list[str],
    files_to_pack: list[Path],
    dry_run: bool,
    verbose: bool
) -> None:
    """Write output file if not dry run."""
    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        if verbose:
            print(f"[markpact] Written {len(files_to_pack)} file blocks to {output_path}")
    elif verbose:
        print(f"[markpact] Would write {len(files_to_pack)} file blocks to {output_path}")


def pack_directory(
    source_dir: str | Path,
    output: str | Path | None = None,
    *,
    exclude: Optional[set[str]] = None,
    include_patterns: Optional[list[str]] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    run_command: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> PackResult:
    """Pack a directory into markpact README.md format.
    
    Args:
        source_dir: Directory to pack
        output: Output README.md path (default: source_dir/README.md)
        exclude: Additional patterns to exclude
        include_patterns: Only include files matching these glob patterns
        title: Project title (default: directory name)
        description: Project description
        run_command: Custom run command (auto-detected if not provided)
        dry_run: Show what would be done without writing
        verbose: Print progress
        
    Returns:
        PackResult with details
    """
    src = Path(source_dir).resolve()
    if not src.exists():
        return PackResult(
            source_dir=src,
            output_path=Path("."),
            files_packed=0,
            files_skipped=0,
            success=False,
            message=f"Source directory not found: {src}",
        )
    
    if not src.is_dir():
        return PackResult(
            source_dir=src,
            output_path=Path("."),
            files_packed=0,
            files_skipped=0,
            success=False,
            message=f"Not a directory: {src}",
        )
    
    # Determine output path
    if output:
        output_path = Path(output).resolve()
    else:
        output_path = src / "README.md"
    
    # Merge exclude patterns
    exclude_patterns = DEFAULT_EXCLUDE.copy()
    if exclude:
        exclude_patterns.update(exclude)
    
    # Always exclude the output file itself
    output_relative = output_path.relative_to(src) if output_path.is_relative_to(src) else output_path
    
    if verbose and not dry_run:
        print(f"[markpact] Packing {src} → {output_path}")
    
    # Collect files
    files_to_pack = _collect_files(src, output_path, exclude_patterns, include_patterns, verbose and not dry_run)
    
    # Generate README content
    project_title = title or src.name
    desc = description or f"Project packed with markpact from {src.name}"
    
    lines, blocks_info = _generate_readme_content(
        files_to_pack, src, project_title, desc, run_command, dry_run
    )
    
    # Write output
    _write_output(output_path, lines, files_to_pack, dry_run, verbose)
    
    return PackResult(
        source_dir=src,
        output_path=output_path,
        files_packed=len(files_to_pack),
        files_skipped=0,  # We don't track this separately
        blocks=blocks_info,
        dry_run=dry_run,
        success=True,
    )


def print_pack_report(result: PackResult) -> None:
    """Print a report of the packing operation."""
    print("\n" + "=" * 60)
    if result.dry_run:
        print("MARKPACT PACK REPORT (DRY RUN)")
    else:
        print("MARKPACT PACK REPORT")
    print("=" * 60)
    
    if not result.success:
        print(f"\n✗ Failed: {result.message}")
        return
    
    print(f"\nSource: {result.source_dir}")
    print(f"Output: {result.output_path}")
    print(f"\n✓ Files packed: {result.files_packed}")
    
    if result.blocks:
        print("\nFiles:")
        for block in result.blocks:
            print(f"  • {block['path']} ({block['language']})")
    
    if result.dry_run:
        print("\n(Dry run - no files were written)")
    
    print("=" * 60 + "\n")
