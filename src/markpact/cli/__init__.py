"""Markpact CLI — thin dispatch to subcommand modules.

Refactored from monolithic cli.py (808L, CC=46/31) into a package:
    cli/
    ├── __init__.py      — main() dispatch (CC≤5)
    ├── sync_cmd.py      — handle_sync_cli (CC≤8)
    ├── pack_cmd.py      — handle_pack_cli
    ├── config_cmd.py    — handle_config_cli
    ├── publish_cmd.py   — publish mode handlers
    ├── run_cmd.py       — normal run, Docker, test modes
    ├── convert_cmd.py   — notebook, markdown, LLM conversion
    └── helpers.py       — _parse_blocks_to_state, _resolve_file_body
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import __version__
from ..parser import parse_blocks
from ..sandbox import Sandbox

# Backward compat re-exports (used by tests)
from .sync_cmd import handle_sync_cli  # noqa: F401
from .pack_cmd import handle_pack_cli  # noqa: F401
from .config_cmd import handle_config_cli  # noqa: F401
from .portal_cmd import handle_portal_cli  # noqa: F401


# ─── Subcommand dispatch ─────────────────────────────────────────────────────

_SUBCOMMANDS = {"config", "pack", "sync", "portal"}


def main(argv: list[str] | None = None) -> int:
    """Main entry point for markpact CLI. CC≤5."""
    args_list = argv if argv is not None else sys.argv[1:]

    # Dispatch subcommands early
    if args_list and args_list[0] in _SUBCOMMANDS:
        return _dispatch_subcommand(args_list[0], args_list[1:])

    # Main argument parser
    args = _parse_main_args(args_list)
    verbose = not args.quiet

    # Handle early-exit flags
    from .convert_cmd import _handle_list_examples, _handle_list_notebook_formats
    if args.list_examples:
        return _handle_list_examples(verbose)
    if args.list_notebook_formats:
        return _handle_list_notebook_formats(verbose)

    # Handle generation/conversion that produces a README
    readme_path = _handle_generation_phase(args, verbose)
    if isinstance(readme_path, int):
        return readme_path  # error exit code

    # Process the README
    return _process_readme(args, readme_path, verbose)


# ─── Internals ───────────────────────────────────────────────────────────────


def _dispatch_subcommand(cmd: str, argv: list[str]) -> int:
    """Dispatch to subcommand handler."""
    if cmd == "config":
        return handle_config_cli(argv)
    if cmd == "pack":
        return handle_pack_cli(argv)
    if cmd == "sync":
        return handle_sync_cli(argv)
    if cmd == "portal":
        return handle_portal_cli(argv)
    return 1


def _parse_main_args(args_list: list[str]) -> argparse.Namespace:
    """Build and parse the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="markpact",
        description="Executable Markdown Runtime – run projects from README.md",
    )
    parser.add_argument("readme", nargs="?", default="README.md", help="Path to README.md")
    parser.add_argument("--sandbox", "-s", help="Sandbox directory (default: ./sandbox)")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be done")
    parser.add_argument("--convert", "-c", action="store_true", help="Convert regular Markdown to markpact")
    parser.add_argument("--convert-only", action="store_true", help="Only convert and print result")
    parser.add_argument("--save-converted", metavar="FILE", help="Save converted markpact to file")
    parser.add_argument("--auto", "-a", action="store_true", help="Auto-detect and convert if no markpact blocks")
    parser.add_argument("--from-notebook", metavar="FILE", help="Convert notebook to markpact")
    parser.add_argument("--list-notebook-formats", action="store_true", help="List supported notebook formats")
    parser.add_argument("--version", "-V", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")

    # LLM generation options
    parser.add_argument("--prompt", "-p", metavar="TEXT", help="Generate contract from prompt")
    parser.add_argument("--output", "-o", metavar="FILE", help="Output file (default: README.md)")
    parser.add_argument("--model", "-m", metavar="MODEL", help="LLM model to use")
    parser.add_argument("--api-base", metavar="URL", help="API base URL")
    parser.add_argument("--api-key", metavar="KEY", help="API key")
    parser.add_argument("--list-examples", action="store_true", help="List available example prompts")
    parser.add_argument("--example", "-e", metavar="NAME", help="Use example prompt by name")
    parser.add_argument("--run", "-r", action="store_true", help="Run immediately after generating")
    parser.add_argument("--docker", action="store_true", help="Run in Docker container")
    parser.add_argument("--auto-fix", action="store_true", default=True, help="Auto-fix runtime errors")
    parser.add_argument("--no-auto-fix", action="store_true", help="Disable auto-fix")
    parser.add_argument("--auto-fix-llm", action="store_true", help="Use LLM to fix complex errors")
    parser.add_argument("--test", "-t", action="store_true", help="Run tests from markpact:test blocks")
    parser.add_argument("--test-only", action="store_true", help="Only run tests, don't keep service")
    parser.add_argument("--publish", action="store_true", help="Publish to registry")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], help="Bump version before publishing")
    parser.add_argument("--no-bump", action="store_true", help="Disable automatic version bump")
    parser.add_argument("--registry", metavar="NAME", help="Override registry")
    parser.add_argument("--publish-llm", action="store_true", help="Generate publish config using LLM")
    parser.add_argument("--no-interactive", action="store_true", help="Disable interactive prompts")
    parser.add_argument("--yes", action="store_true", help="Assume defaults for missing config")
    parser.add_argument("--recursive", "-R", action="store_true", help="Resolve markpact:include directives from sub-READMEs")

    return parser.parse_args(args_list)


def _handle_generation_phase(args, verbose: bool) -> Path | int:
    """Handle notebook/LLM generation. Returns readme Path or error exit code."""
    from .convert_cmd import _handle_from_notebook, _handle_llm_generation

    if args.from_notebook:
        exit_code, readme_path = _handle_from_notebook(args, verbose)
        if exit_code != 0 or readme_path is None:
            return exit_code
        args.readme = str(readme_path)

    if args.prompt or args.example:
        exit_code, readme_path = _handle_llm_generation(args, verbose)
        if exit_code != 0 or readme_path is None:
            return exit_code
        args.readme = str(readme_path)

    readme = Path(args.readme)
    if not readme.exists():
        print(f"[markpact] ERROR: {readme} not found", file=sys.stderr)
        return 1

    return readme


def _process_readme(args, readme: Path, verbose: bool) -> int:
    """Parse blocks, extract state, dispatch to mode handler."""
    from .convert_cmd import _handle_markdown_conversion
    from .helpers import _parse_blocks_to_state
    from .publish_cmd import _handle_publish_mode
    from .run_cmd import _handle_docker_mode, _handle_test_mode, _handle_normal_run

    sandbox = Sandbox(args.sandbox)
    original_text = readme.read_text()

    # Handle markdown conversion
    text_to_parse, should_exit = _handle_markdown_conversion(args, original_text, verbose)
    if should_exit:
        return 0

    if verbose:
        print(f"[markpact] Parsing {readme}")

    # Parse blocks
    if getattr(args, 'recursive', False):
        from ..parser import parse_blocks_recursive
        blocks = parse_blocks_recursive(
            text_to_parse,
            base_dir=readme.resolve().parent,
            source_file=str(readme),
            verbose=verbose,
        )
    else:
        blocks = parse_blocks(text_to_parse)
    state = _parse_blocks_to_state(blocks, sandbox, args, verbose)
    if state.get("error"):
        return 1

    deps = state["deps"]
    run_command = state["run_command"]
    test_blocks = state["test_blocks"]
    publish_config_block = state["publish_config_block"]

    # Handle publish mode
    if args.publish:
        from ..publisher import parse_publish_block
        config = parse_publish_block(publish_config_block[1], publish_config_block[0]) if publish_config_block else None
        return _handle_publish_mode(args, config, sandbox, readme, text_to_parse, blocks, run_command, verbose)

    # Handle Docker mode
    if args.docker:
        return _handle_docker_mode(args, sandbox, deps, run_command, verbose)

    # Handle test mode
    if (args.test or args.test_only) and test_blocks and run_command:
        return _handle_test_mode(args, sandbox, run_command, test_blocks, deps, verbose)

    # Normal run mode
    if run_command:
        return _handle_normal_run(args, sandbox, run_command, deps, readme, verbose)
    elif verbose:
        print("[markpact] No run command defined")

    return 0
