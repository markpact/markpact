"""Publish mode — publish to PyPI, npm, Docker, GitHub Packages."""

from __future__ import annotations

import sys
from pathlib import Path

from ..sandbox import Sandbox


def _resolve_publish_config(args, text_to_parse, readme, blocks, run_command, verbose):
    """Resolve publish config from args, LLM, inference, or prompts."""
    from ..publisher import infer_publish_config, prompt_publish_config
    from ..publisher import generate_publish_config_with_llm

    config = None

    # Try LLM generation if requested
    if args.publish_llm:
        try:
            config = generate_publish_config_with_llm(text_to_parse, verbose=verbose)
        except Exception as e:
            if verbose:
                print(f"[markpact] LLM publish config generation failed: {e}")

    # Fallback to inference
    if config is None:
        config = infer_publish_config(readme_path=readme, markdown=text_to_parse, blocks=blocks, run_command=run_command)

    # Interactive prompt if allowed
    if (not args.no_interactive) and (not args.yes) and sys.stdin.isatty():
        config = prompt_publish_config(config)
    elif config.registry == "unknown" and not args.registry:
        print("[markpact] ERROR: Cannot infer publish registry. Add markpact:publish block or pass --registry", file=sys.stderr)
        return None

    return config


def _determine_bump_type(args):
    """Determine version bump type from args."""
    if args.bump:
        return args.bump
    if not args.no_bump:
        return "patch"
    return None


def _print_publish_dry_run(config, bump_type):
    """Print dry-run information for publish."""
    print(f"[markpact] Would publish {config.name} v{config.version} to {config.registry}")
    if bump_type:
        from ..publisher import bump_version
        new_ver = bump_version(config.version, bump_type)
        print(f"[markpact] Would bump version to {new_ver}")


def _execute_publish_result(result, readme, bump_type, verbose):
    """Handle publish result and return exit code."""
    from ..publisher import update_version_in_readme

    if result.success:
        print(f"[markpact] ✓ {result.message}")
        print(f"[markpact] Version: {result.version}")
        if result.url:
            print(f"[markpact] URL: {result.url}")
        if bump_type:
            update_version_in_readme(readme, result.version, verbose=verbose)
        return 0
    else:
        print(f"[markpact] ERROR: {result.message}", file=sys.stderr)
        return 1


def _handle_publish_mode(args, config, sandbox: Sandbox, readme: Path, text_to_parse: str,
                         blocks, run_command: str | None, verbose: bool) -> int:
    """Handle publish mode. Returns exit code."""
    from ..publisher import parse_publish_block, publish

    if config is None:
        config = _resolve_publish_config(args, text_to_parse, readme, blocks, run_command, verbose)
        if config is None:
            return 1

    if args.registry:
        config.registry = args.registry

    bump_type = _determine_bump_type(args)

    if args.dry_run:
        _print_publish_dry_run(config, bump_type)
        return 0

    result = publish(config, sandbox, bump=bump_type, verbose=verbose, source_readme_path=readme)
    return _execute_publish_result(result, readme, bump_type, verbose)
