"""Config subcommand — manage LLM configuration."""

from __future__ import annotations

import argparse
import sys


def handle_config_cli(argv: list[str]) -> int:
    """Handle config subcommand with its own parser"""
    from ..config import (
        load_env, save_env, init_env, set_model, set_api_key, set_api_base,
        apply_preset, show_config, list_providers, get_env_path, PROVIDER_PRESETS
    )

    parser = argparse.ArgumentParser(prog="markpact config", description="Manage LLM configuration")
    parser.add_argument("--init", action="store_true", help="Initialize .env config file")
    parser.add_argument("--force", action="store_true", help="Overwrite existing config")
    parser.add_argument("--provider", metavar="NAME", help="Apply provider preset")
    parser.add_argument("--list-providers", action="store_true", help="List available provider presets")
    parser.add_argument("--model", dest="set_model", metavar="MODEL", help="Set LLM model")
    parser.add_argument("--api-key", dest="set_api_key", metavar="KEY", help="Set API key")
    parser.add_argument("--api-base", dest="set_api_base", metavar="URL", help="Set API base URL")

    args = parser.parse_args(argv)

    if args.init:
        path, created = init_env(force=args.force)
        if created:
            print(f"[markpact] Created config file: {path}")
        else:
            print(f"[markpact] Config file already exists: {path}")
            print(f"[markpact] Use --force to overwrite")
        return 0

    if args.list_providers:
        print(list_providers())
        return 0

    if args.provider:
        if args.provider not in PROVIDER_PRESETS:
            print(f"[markpact] ERROR: Unknown provider '{args.provider}'", file=sys.stderr)
            print(f"[markpact] Available: {', '.join(PROVIDER_PRESETS.keys())}", file=sys.stderr)
            return 1

        config = apply_preset(args.provider, args.set_api_key)
        print(f"[markpact] Applied preset: {args.provider}")
        if args.provider != "ollama" and not args.set_api_key:
            print(f"[markpact] NOTE: Don't forget to set API key with: markpact config --api-key YOUR_KEY")
        return 0

    if args.set_model:
        set_model(args.set_model)
        print(f"[markpact] Model set to: {args.set_model}")
        return 0

    if args.set_api_key:
        set_api_key(args.set_api_key)
        print(f"[markpact] API key updated")
        return 0

    if args.set_api_base:
        set_api_base(args.set_api_base)
        print(f"[markpact] API base set to: {args.set_api_base}")
        return 0

    env_path = get_env_path()
    if not env_path.exists():
        print(f"[markpact] No config file found at: {env_path}")
        print(f"[markpact] Run 'markpact config --init' to create one")
        print()

    print(show_config())
    return 0
