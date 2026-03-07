"""Sync subcommand — sync source files into README markpact blocks.

Refactored from monolithic handle_sync_cli (CC=46) into a pipeline
of small steps, each with CC≤8.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..syncer import (
    sync_readme, print_sync_report, list_tracked_paths, find_untracked_files,
    create_backup, list_backups, restore_backup, add_untracked_blocks,
)


# ─── Argument parsing ────────────────────────────────────────────────────────


def _build_sync_parser() -> argparse.ArgumentParser:
    """Build the sync subcommand argument parser."""
    parser = argparse.ArgumentParser(
        prog="markpact sync",
        description="Sync source directory files into README.md markpact:file blocks"
    )
    parser.add_argument("readme", nargs="?", default="README.md",
                        help="Path to README.md (default: README.md)")
    parser.add_argument("--source", "-s", metavar="DIR",
                        help="Source directory (default: auto-detect sandbox/ next to README)")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="Show what would be done without writing files")
    parser.add_argument("-d", "--diff", action="store_true",
                        help="Show unified diff for each changed file")
    parser.add_argument("-c", "--check", action="store_true",
                        help="Exit with code 1 if any files are out of sync")
    parser.add_argument("-l", "--list", action="store_true",
                        help="List all tracked markpact:file paths")
    parser.add_argument("-m", "--missing", action="store_true",
                        help="Show source files not tracked in README")
    parser.add_argument("--exclude", metavar="PATH", action="append",
                        help="Exclude file path from sync (can be repeated)")
    parser.add_argument("--rollback", action="store_true",
                        help="Restore README from the latest backup")
    parser.add_argument("--rollback-to", metavar="FILE",
                        help="Restore README from a specific backup file")
    parser.add_argument("--backups", action="store_true",
                        help="List available backups")
    parser.add_argument("--hash", action="store_true",
                        help="Embed/update sha256= content hash in block headers")
    parser.add_argument("--add", metavar="PATH", nargs="*", default=None,
                        help="Add untracked files as new markpact:file blocks (no args = all untracked)")
    parser.add_argument("-R", "--recursive", action="store_true",
                        help="Also sync sub-READMEs referenced by markpact:include directives")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress output")
    return parser


# ─── Path resolution ─────────────────────────────────────────────────────────


def _resolve_paths(args) -> tuple[Path, Path] | None:
    """Resolve and validate readme_path and source_dir. Returns None on error."""
    readme_path = Path(args.readme).resolve()
    if not readme_path.exists():
        print(f"[markpact] ERROR: {readme_path} not found", file=sys.stderr)
        return None

    if args.source:
        source_dir = Path(args.source).resolve()
    else:
        source_dir = readme_path.parent / "sandbox"

    if not source_dir.exists():
        print(f"[markpact] ERROR: Source directory not found: {source_dir}", file=sys.stderr)
        print(f"[markpact] Use --source DIR to specify source directory", file=sys.stderr)
        return None

    return readme_path, source_dir


# ─── Info modes (no mutation) ────────────────────────────────────────────────


def _handle_backups_mode(readme_path: Path) -> int:
    """List available backups."""
    backups = list_backups(readme_path)
    if not backups:
        print("[markpact] No backups found")
        return 0
    print(f"[markpact] Available backups ({len(backups)}):")
    for i, bak in enumerate(backups):
        label = " (latest)" if i == 0 else ""
        size_kb = bak.stat().st_size / 1024
        print(f"  {i+1}. {bak.name}  ({size_kb:.1f} KB){label}")
    return 0


def _handle_rollback_mode(args, readme_path: Path, verbose: bool) -> int:
    """Restore README from backup."""
    bak_path = Path(args.rollback_to) if args.rollback_to else None
    ok = restore_backup(readme_path, bak_path, verbose=verbose)
    if ok:
        print("[markpact] Rollback successful")
        return 0
    print("[markpact] ERROR: No backup available to restore", file=sys.stderr)
    return 1


def _handle_list_mode(text: str, source_dir: Path) -> int:
    """List tracked files."""
    tracked = list_tracked_paths(text)
    print(f"[markpact] Tracked files in README ({len(tracked)}):")
    for p in tracked:
        exists = (source_dir / p).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {p}")
    return 0


def _handle_missing_mode(text: str, source_dir: Path) -> int:
    """Show untracked source files."""
    untracked = find_untracked_files(text, source_dir)
    if not untracked:
        print("[markpact] All source files are tracked in README")
        return 0
    print(f"[markpact] Untracked source files ({len(untracked)}):")
    for p in untracked:
        print(f"  + {p}")
    return 0


def _handle_add_mode(args, readme_path: Path, source_dir: Path, verbose: bool) -> int:
    """Add untracked files as new blocks."""
    text = readme_path.read_text(encoding="utf-8")
    if args.add:  # specific paths: --add file1 file2
        paths_to_add = args.add
    else:  # bare --add = all untracked
        paths_to_add = find_untracked_files(text, source_dir)
    if not paths_to_add:
        if verbose:
            print("[markpact] No untracked files to add")
        return 0
    if verbose:
        mode = "Previewing" if args.dry_run else "Adding"
        print(f"[markpact] {mode} {len(paths_to_add)} file(s) to {readme_path.name}")
    added = add_untracked_blocks(
        readme_path, source_dir, paths_to_add,
        dry_run=args.dry_run, verbose=verbose,
    )
    if verbose:
        if args.dry_run:
            print(f"[markpact] Would add {added} block(s)")
        else:
            print(f"[markpact] Added {added} block(s) to {readme_path.name}")
    return 0


# ─── Sync execution ─────────────────────────────────────────────────────────


def _execute_recursive_sync(args, readme_path: Path, source_dir: Path,
                            exclude_sync: set, dry_run: bool, verbose: bool) -> int:
    """Execute recursive sync across included sub-READMEs."""
    from ..syncer import sync_readme_recursive
    results = sync_readme_recursive(
        readme_path=readme_path,
        source_dir=source_dir,
        exclude_sync=exclude_sync,
        dry_run=dry_run,
        verbose=verbose,
        hash_blocks=args.hash,
    )
    if any(not r.success for r in results):
        for r in results:
            if not r.success:
                print(f"[markpact] ERROR: {r.message}", file=sys.stderr)
        return 1

    for r in results:
        if verbose or args.dry_run:
            print_sync_report(r)

    if args.check and sum(r.updated for r in results) > 0:
        return 1
    return 0


def _show_diffs(result, text: str, readme_path: Path, source_dir: Path, dry_run: bool) -> None:
    """Show unified diffs for updated blocks."""
    if not result.details:
        return
    from ..syncer import diff_block
    import re as _re
    for detail in result.details:
        if detail["status"] != "updated":
            continue
        rel_path = detail["path"]
        file_content = (source_dir / rel_path).read_text(encoding="utf-8").rstrip("\n")
        pattern = _re.compile(
            r"```(?:\w+\s+)?markpact:file\s+path=" + _re.escape(rel_path) + r"\n([\s\S]*?)\n```"
        )
        m = pattern.search(text)
        if m:
            d = diff_block(rel_path, m.group(1), file_content)
            if d:
                print(d)
                print()


def _execute_single_sync(args, readme_path: Path, source_dir: Path,
                         text: str, exclude_sync: set, dry_run: bool, verbose: bool) -> int:
    """Execute sync on a single README."""
    result = sync_readme(
        readme_path=readme_path,
        source_dir=source_dir,
        exclude_sync=exclude_sync,
        dry_run=dry_run,
        verbose=verbose,
        hash_blocks=args.hash,
    )

    if not result.success:
        print(f"[markpact] ERROR: {result.message}", file=sys.stderr)
        return 1

    if args.diff:
        _show_diffs(result, text, readme_path, source_dir, dry_run)

    if verbose or args.dry_run:
        print_sync_report(result)

    # Show untracked hint after sync
    if verbose and not args.check:
        text_after = readme_path.read_text(encoding="utf-8") if not dry_run and result.updated > 0 else text
        untracked = find_untracked_files(text_after, source_dir)
        if untracked:
            print(f"\n[markpact] {len(untracked)} untracked file(s) (use --add to track, --missing to list)")

    if args.check and result.updated > 0:
        return 1
    return 0


# ─── Main entry point ───────────────────────────────────────────────────────


def handle_sync_cli(argv: list[str]) -> int:
    """Handle sync subcommand — thin orchestrator dispatching to steps.

    CC: ~8 (parse → resolve → dispatch info mode or sync mode).
    """
    parser = _build_sync_parser()
    args = parser.parse_args(argv)
    verbose = not args.quiet

    # Resolve paths
    paths = _resolve_paths(args)
    if paths is None:
        return 1
    readme_path, source_dir = paths

    # Info/mutation modes that don't need sync
    if args.backups:
        return _handle_backups_mode(readme_path)
    if args.rollback or args.rollback_to:
        return _handle_rollback_mode(args, readme_path, verbose)

    text = readme_path.read_text(encoding="utf-8")

    if args.list:
        return _handle_list_mode(text, source_dir)
    if args.missing:
        return _handle_missing_mode(text, source_dir)
    if args.add is not None:
        return _handle_add_mode(args, readme_path, source_dir, verbose)

    # Sync execution
    exclude_sync = set(args.exclude) if args.exclude else set()
    dry_run = args.dry_run or args.check

    if verbose:
        mode = "Checking" if args.check else ("Previewing" if args.dry_run else "Syncing")
        print(f"[markpact] {mode} {source_dir.name}/ → {readme_path.name}")

    if args.recursive:
        return _execute_recursive_sync(args, readme_path, source_dir, exclude_sync, dry_run, verbose)

    return _execute_single_sync(args, readme_path, source_dir, text, exclude_sync, dry_run, verbose)
