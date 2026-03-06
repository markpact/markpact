"""Sync source directory files into markpact README.md blocks.

The reverse of unpack: reads actual files from a source directory and
updates the corresponding markpact:file blocks in a README.md, preserving
all surrounding documentation and prose.

Supports both markpact block formats:
- New: ```python markpact:file path=main.py
- Old: ```markpact:file path=main.py
"""

from __future__ import annotations

import difflib
import fnmatch
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


# ─── Backup / Rollback ───────────────────────────────────────────────────────

BACKUP_DIR_NAME = ".markpact"
BACKUP_PREFIX = "README.md.bak."
MAX_BACKUPS = 10


def _backup_dir(readme_path: Path) -> Path:
    """Return .markpact/ directory next to README."""
    return readme_path.parent / BACKUP_DIR_NAME


def create_backup(readme_path: Path, *, verbose: bool = False) -> Path | None:
    """Create a timestamped backup of README before sync.

    Backups are stored in .markpact/ next to the README.
    Old backups beyond MAX_BACKUPS are pruned automatically.

    Args:
        readme_path: Path to README.md
        verbose: Print backup path

    Returns:
        Path to backup file, or None if README doesn't exist
    """
    readme = Path(readme_path).resolve()
    if not readme.exists():
        return None

    bak_dir = _backup_dir(readme)
    bak_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak_path = bak_dir / f"{BACKUP_PREFIX}{timestamp}"
    shutil.copy2(readme, bak_path)

    if verbose:
        print(f"[markpact] Backup: {bak_path}")

    # Prune old backups
    _prune_backups(bak_dir)

    return bak_path


def list_backups(readme_path: Path) -> list[Path]:
    """List all backup files, newest first.

    Args:
        readme_path: Path to README.md

    Returns:
        List of backup paths sorted newest-first
    """
    bak_dir = _backup_dir(Path(readme_path).resolve())
    if not bak_dir.exists():
        return []
    backups = sorted(bak_dir.glob(f"{BACKUP_PREFIX}*"), reverse=True)
    return backups


def restore_backup(
    readme_path: Path,
    backup_path: Path | None = None,
    *,
    verbose: bool = False,
) -> bool:
    """Restore README from a backup (rollback).

    Args:
        readme_path: Path to README.md to restore
        backup_path: Specific backup to restore (default: latest)
        verbose: Print progress

    Returns:
        True if restored, False if no backup available
    """
    readme = Path(readme_path).resolve()

    if backup_path is None:
        backups = list_backups(readme)
        if not backups:
            return False
        backup_path = backups[0]

    backup_path = Path(backup_path)
    if not backup_path.exists():
        return False

    shutil.copy2(backup_path, readme)
    if verbose:
        print(f"[markpact] Restored: {backup_path} → {readme}")
    return True


def _prune_backups(bak_dir: Path) -> None:
    """Remove oldest backups if count exceeds MAX_BACKUPS."""
    backups = sorted(bak_dir.glob(f"{BACKUP_PREFIX}*"), reverse=True)
    for old in backups[MAX_BACKUPS:]:
        old.unlink()



# ─── Block regex patterns ────────────────────────────────────────────────────
# These match the full block including fences, capturing groups for replacement.

# New format: ```lang markpact:file path=<path>\n<body>\n```
_BLOCK_NEW_RE = re.compile(
    r"(```\w+\s+markpact:file\s+path=)(\S+)(\n)([\s\S]*?)(\n```)"
)

# Old format: ```markpact:file path=<path>\n<body>\n```
_BLOCK_OLD_RE = re.compile(
    r"(```markpact:file\s+path=)(\S+)(\n)([\s\S]*?)(\n```)"
)

# Combined pattern matching both formats
_BLOCK_COMBINED_RE = re.compile(
    r"(```(?:\w+\s+)?markpact:file\s+path=)(\S+)(\n)([\s\S]*?)(\n```)"
)

# Default patterns to exclude from untracked file detection
DEFAULT_EXCLUDE_DIRS = {
    ".venv", "venv", "node_modules", "__pycache__", ".git",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "build", "dist", ".egg-info", "apps",
}

DEFAULT_EXCLUDE_FILES = {
    ".DS_Store", "Thumbs.db",
}


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class SyncResult:
    """Result of a sync operation."""
    readme_path: Path
    source_dir: Path
    updated: int = 0
    unchanged: int = 0
    excluded: int = 0
    missing: int = 0
    dry_run: bool = False
    success: bool = True
    message: str = ""
    details: list[dict] = field(default_factory=list)

    def summary(self) -> str:
        """Return human-readable summary."""
        mode = "[DRY-RUN] " if self.dry_run else ""
        lines = [
            f"{mode}Sync {self.source_dir} → {self.readme_path}",
            f"  Updated:   {self.updated}",
            f"  Unchanged: {self.unchanged}",
            f"  Excluded:  {self.excluded}",
            f"  Missing:   {self.missing}",
        ]
        if self.message:
            lines.append(f"  Message: {self.message}")
        return "\n".join(lines)


# ─── Core functions ───────────────────────────────────────────────────────────

def list_tracked_paths(text: str) -> list[str]:
    """List all file paths tracked in markpact:file blocks.

    Args:
        text: README.md content

    Returns:
        List of relative paths from markpact:file blocks
    """
    return [m.group(2) for m in _BLOCK_COMBINED_RE.finditer(text)]


def find_untracked_files(
    text: str,
    source_dir: Path,
    *,
    exclude_patterns: Optional[set[str]] = None,
    exclude_dirs: Optional[set[str]] = None,
) -> list[str]:
    """Find files in source directory not tracked in README markpact blocks.

    Args:
        text: README.md content
        source_dir: Directory to scan for files
        exclude_patterns: File patterns to exclude (glob format)
        exclude_dirs: Directory names to skip
    
    Returns:
        List of relative paths not tracked in README
    """
    tracked = set(list_tracked_paths(text))
    dirs_to_skip = exclude_dirs or DEFAULT_EXCLUDE_DIRS
    file_patterns = exclude_patterns or DEFAULT_EXCLUDE_FILES
    untracked = []

    if not source_dir.exists():
        return untracked

    for file_path in sorted(source_dir.rglob("*")):
        if not file_path.is_file():
            continue

        rel = file_path.relative_to(source_dir)

        # Skip excluded directories
        if any(part in dirs_to_skip for part in rel.parts):
            continue

        # Skip excluded file patterns
        if any(fnmatch.fnmatch(rel.name, p) for p in file_patterns):
            continue

        rel_str = str(rel)
        if rel_str not in tracked:
            untracked.append(rel_str)

    return untracked


def diff_block(
    rel_path: str,
    old_body: str,
    new_body: str,
) -> str:
    """Generate unified diff between old and new block content.

    Args:
        rel_path: Relative file path (for labels)
        old_body: Current content in README
        new_body: New content from source file

    Returns:
        Unified diff string (empty if identical)
    """
    diff = difflib.unified_diff(
        old_body.splitlines(keepends=True),
        new_body.splitlines(keepends=True),
        fromfile=f"README:{rel_path}",
        tofile=f"source/{rel_path}",
        lineterm=""
    )
    return "\n".join(diff)


def sync_readme(
    readme_path: str | Path,
    source_dir: str | Path,
    *,
    exclude_sync: Optional[set[str]] = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> SyncResult:
    """Sync source directory files into README.md markpact:file blocks.

    Reads all markpact:file blocks from README, finds corresponding files
    in source_dir, and updates block content to match actual files.

    Args:
        readme_path: Path to README.md
        source_dir: Path to source directory (e.g., sandbox/)
        exclude_sync: Set of relative paths to never sync (e.g., sensitive files)
        dry_run: If True, don't write changes
        verbose: If True, print progress

    Returns:
        SyncResult with details of the operation
    """
    readme = Path(readme_path).resolve()
    src = Path(source_dir).resolve()

    if not readme.exists():
        return SyncResult(
            readme_path=readme, source_dir=src,
            success=False, message=f"README not found: {readme}",
        )

    if not src.exists():
        return SyncResult(
            readme_path=readme, source_dir=src,
            success=False, message=f"Source directory not found: {src}",
        )

    text = readme.read_text(encoding="utf-8")
    excludes = exclude_sync or set()

    result = SyncResult(
        readme_path=readme,
        source_dir=src,
        dry_run=dry_run,
    )

    def _replacer(m: re.Match) -> str:
        prefix = m.group(1)     # ```[lang ]markpact:file path=
        rel_path = m.group(2)   # e.g. scripts/doctor.sh
        sep = m.group(3)        # \n
        old_body = m.group(4)   # current content
        suffix = m.group(5)     # \n```

        detail = {"path": rel_path, "status": "unchanged"}

        if rel_path in excludes:
            detail["status"] = "excluded"
            result.excluded += 1
            if verbose:
                print(f"  [skip] {rel_path} (excluded)")
            result.details.append(detail)
            return m.group(0)

        file_path = src / rel_path
        if not file_path.exists():
            detail["status"] = "missing"
            result.missing += 1
            if verbose:
                print(f"  [miss] {rel_path} (not found in {src.name}/)")
            result.details.append(detail)
            return m.group(0)

        try:
            new_body = file_path.read_text(encoding="utf-8").rstrip("\n")
        except Exception as e:
            detail["status"] = "error"
            detail["error"] = str(e)
            result.missing += 1
            if verbose:
                print(f"  [err]  {rel_path}: {e}")
            result.details.append(detail)
            return m.group(0)

        if old_body == new_body:
            result.unchanged += 1
            result.details.append(detail)
            return m.group(0)

        detail["status"] = "updated"
        result.updated += 1
        if verbose:
            label = "[dry] " if dry_run else "[sync]"
            print(f"  {label} {rel_path}")

        result.details.append(detail)
        return prefix + rel_path + sep + new_body + suffix

    new_text = _BLOCK_COMBINED_RE.sub(_replacer, text)

    if not dry_run and result.updated > 0:
        create_backup(readme, verbose=verbose)
        readme.write_text(new_text, encoding="utf-8")

    return result


def print_sync_report(result: SyncResult) -> None:
    """Print a formatted report of the sync operation."""
    print()
    print("=" * 60)
    if result.dry_run:
        print("MARKPACT SYNC REPORT (DRY RUN)")
    else:
        print("MARKPACT SYNC REPORT")
    print("=" * 60)

    if not result.success:
        print(f"\n✗ Failed: {result.message}")
        return

    print(f"\nSource:  {result.source_dir}")
    print(f"README:  {result.readme_path}")
    print(f"\n  Updated:   {result.updated}")
    print(f"  Unchanged: {result.unchanged}")
    print(f"  Excluded:  {result.excluded}")
    print(f"  Missing:   {result.missing}")

    if result.details:
        updated = [d for d in result.details if d["status"] == "updated"]
        if updated:
            print("\nUpdated files:")
            for d in updated:
                print(f"  • {d['path']}")

    if result.dry_run:
        print("\n(Dry run - no files were written)")
    elif result.updated > 0:
        print(f"\n✓ README updated ({result.updated} file(s))")
    else:
        print("\n✓ Everything already in sync")

    print("=" * 60)
