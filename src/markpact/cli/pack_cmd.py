"""Pack subcommand — pack directory into markpact README."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..packer import pack_directory, print_pack_report


def handle_pack_cli(argv: list[str]) -> int:
    """Handle pack subcommand - pack directory into markpact README."""
    parser = argparse.ArgumentParser(
        prog="markpact pack",
        description="Pack a directory into markpact README.md format"
    )
    parser.add_argument("source", nargs="?", default=".",
                        help="Source directory to pack (default: current directory)")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="Output README.md path (default: source/README.md)")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="Show what would be done without writing files")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress output")
    parser.add_argument("--title", metavar="NAME",
                        help="Project title (default: directory name)")
    parser.add_argument("--description", metavar="TEXT",
                        help="Project description")
    parser.add_argument("--run", metavar="COMMAND",
                        help="Run command (auto-detected if not provided)")
    parser.add_argument("--exclude", metavar="PATTERN", action="append",
                        help="Additional exclude pattern (can be used multiple times)")
    parser.add_argument("--include", metavar="PATTERN", action="append",
                        help="Only include files matching pattern (can be used multiple times)")

    args = parser.parse_args(argv)
    verbose = not args.quiet

    exclude = set(args.exclude) if args.exclude else None
    include = args.include if args.include else None

    result = pack_directory(
        source_dir=args.source,
        output=args.output,
        exclude=exclude,
        include_patterns=include,
        title=args.title,
        description=args.description,
        run_command=args.run,
        dry_run=args.dry_run,
        verbose=verbose,
    )

    if not result.success:
        print(f"[markpact] ERROR: {result.message}", file=sys.stderr)
        return 1

    if verbose or args.dry_run:
        print_pack_report(result)

    return 0
