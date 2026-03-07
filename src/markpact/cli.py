#!/usr/bin/env python3
"""Markpact CLI"""

import argparse
import re
import sys
from pathlib import Path

from . import __version__
from .converter import convert_markdown_to_markpact, print_conversion_report
from .packer import pack_directory, print_pack_report
from .parser import parse_blocks
from .runner import install_deps, run_cmd
from .sandbox import Sandbox
from .syncer import (
    sync_readme, print_sync_report, list_tracked_paths, find_untracked_files,
    create_backup, list_backups, restore_backup,
)


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


def handle_sync_cli(argv: list[str]) -> int:
    """Handle sync subcommand - sync source files into README markpact blocks."""
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
    parser.add_argument("-R", "--recursive", action="store_true",
                        help="Also sync sub-READMEs referenced by markpact:include directives")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress output")

    args = parser.parse_args(argv)
    verbose = not args.quiet

    readme_path = Path(args.readme).resolve()
    if not readme_path.exists():
        print(f"[markpact] ERROR: {readme_path} not found", file=sys.stderr)
        return 1

    # Auto-detect source dir: look for sandbox/ next to README
    if args.source:
        source_dir = Path(args.source).resolve()
    else:
        source_dir = readme_path.parent / "sandbox"

    if not source_dir.exists():
        print(f"[markpact] ERROR: Source directory not found: {source_dir}", file=sys.stderr)
        print(f"[markpact] Use --source DIR to specify source directory", file=sys.stderr)
        return 1

    # --backups mode
    if args.backups:
        backups = list_backups(readme_path)
        if not backups:
            print("[markpact] No backups found")
            return 0
        print(f"[markpact] Available backups ({len(backups)}):")
        for i, bak in enumerate(backups):
            label = " (latest)" if i == 0 else ""
            ts = bak.name.replace("README.md.bak.", "")
            size_kb = bak.stat().st_size / 1024
            print(f"  {i+1}. {bak.name}  ({size_kb:.1f} KB){label}")
        return 0

    # --rollback mode
    if args.rollback or args.rollback_to:
        bak_path = Path(args.rollback_to) if args.rollback_to else None
        ok = restore_backup(readme_path, bak_path, verbose=verbose)
        if ok:
            print("[markpact] Rollback successful")
            return 0
        else:
            print("[markpact] ERROR: No backup available to restore", file=sys.stderr)
            return 1

    text = readme_path.read_text(encoding="utf-8")

    # --list mode
    if args.list:
        tracked = list_tracked_paths(text)
        print(f"[markpact] Tracked files in README ({len(tracked)}):")
        for p in tracked:
            exists = (source_dir / p).exists()
            status = "✓" if exists else "✗"
            print(f"  {status} {p}")
        return 0

    # --missing mode
    if args.missing:
        untracked = find_untracked_files(text, source_dir)
        if not untracked:
            print("[markpact] All source files are tracked in README")
            return 0
        print(f"[markpact] Untracked source files ({len(untracked)}):")
        for p in untracked:
            print(f"  + {p}")
        return 0

    # Sync mode
    exclude_sync = set(args.exclude) if args.exclude else set()
    dry_run = args.dry_run or args.check

    if verbose:
        mode = "Checking" if args.check else ("Previewing" if args.dry_run else "Syncing")
        print(f"[markpact] {mode} {source_dir.name}/ → {readme_path.name}")

    if getattr(args, 'recursive', False):
        from .syncer import sync_readme_recursive
        results = sync_readme_recursive(
            readme_path=readme_path,
            source_dir=source_dir,
            exclude_sync=exclude_sync,
            dry_run=dry_run,
            verbose=verbose,
            hash_blocks=getattr(args, 'hash', False),
        )
        any_failed = any(not r.success for r in results)
        total_updated = sum(r.updated for r in results)

        if any_failed:
            for r in results:
                if not r.success:
                    print(f"[markpact] ERROR: {r.message}", file=sys.stderr)
            return 1

        for r in results:
            if verbose or args.dry_run:
                print_sync_report(r)

        if args.check and total_updated > 0:
            return 1
        return 0

    result = sync_readme(
        readme_path=readme_path,
        source_dir=source_dir,
        exclude_sync=exclude_sync,
        dry_run=dry_run,
        verbose=verbose,
        hash_blocks=getattr(args, 'hash', False),
    )

    if not result.success:
        print(f"[markpact] ERROR: {result.message}", file=sys.stderr)
        return 1

    # Show diffs if requested
    if args.diff and result.details:
        from .syncer import diff_block
        for detail in result.details:
            if detail["status"] == "updated":
                rel_path = detail["path"]
                # Re-read to compute diff (bodies are not stored in details)
                old_text = readme_path.read_text(encoding="utf-8") if dry_run else text
                file_content = (source_dir / rel_path).read_text(encoding="utf-8").rstrip("\n")
                # Find old body from original text
                import re as _re
                pattern = _re.compile(
                    r"```(?:\w+\s+)?markpact:file\s+path=" + _re.escape(rel_path) + r"\n([\s\S]*?)\n```"
                )
                m = pattern.search(text)
                if m:
                    d = diff_block(rel_path, m.group(1), file_content)
                    if d:
                        print(d)
                        print()

    if verbose or args.dry_run:
        print_sync_report(result)

    # --check mode exit code
    if args.check:
        if result.updated > 0:
            return 1
        return 0

    return 0


def handle_config_cli(argv: list[str]) -> int:
    """Handle config subcommand with its own parser"""
    import argparse
    from .config import (
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


def _handle_list_examples(verbose: bool) -> int:
    """Handle --list-examples flag."""
    from .generator import list_example_prompts
    print("\n[markpact] Available example prompts:\n")
    for name, desc in list_example_prompts().items():
        print(f"  {name:15} - {desc}")
    print(f"\nUsage: markpact -e todo-api -o my-project/README.md")
    return 0


def _handle_list_notebook_formats(verbose: bool) -> int:
    """Handle --list-notebook-formats flag."""
    from .notebook_converter import get_supported_formats
    print("\n[markpact] Supported notebook formats:\n")
    for ext, name in get_supported_formats().items():
        print(f"  {ext:8} - {name}")
    print(f"\nUsage: markpact --from-notebook notebook.ipynb -o project/README.md")
    return 0


def _handle_from_notebook(args, verbose: bool) -> tuple[int, Path | None]:
    """Handle --from-notebook conversion. Returns (exit_code, readme_path_or_none)."""
    from .notebook_converter import convert_notebook
    notebook_path = Path(args.from_notebook)
    output_path = Path(args.output) if args.output else Path("README.md")
    try:
        content = convert_notebook(notebook_path, output_path, verbose=verbose)
        if args.convert_only:
            print("\n--- CONVERTED CONTENT ---\n")
            print(content)
            return 0, None
        if verbose:
            print(f"[markpact] Saved to: {output_path}")
        if args.run:
            return 0, output_path
        return 0, None
    except Exception as e:
        print(f"[markpact] ERROR: {e}", file=sys.stderr)
        return 1, None


def _handle_llm_generation(args, verbose: bool) -> tuple[int, Path | None]:
    """Handle --prompt or --example LLM generation. Returns (exit_code, readme_path_or_none)."""
    try:
        from .generator import generate_contract, GeneratorConfig, get_example_prompt
        from .config import load_env, init_env
    except ImportError:
        print("[markpact] ERROR: litellm not installed. Run: pip install markpact[llm]", file=sys.stderr)
        return 1, None
    init_env(force=False)
    prompt = args.prompt or get_example_prompt(args.example)
    env_config = load_env()
    config = GeneratorConfig(
        model=args.model or env_config.get("MARKPACT_MODEL", "ollama/qwen2.5-coder:14b"),
        api_base=args.api_base or env_config.get("MARKPACT_API_BASE", "http://localhost:11434"),
        api_key=getattr(args, 'api_key', None) or env_config.get("MARKPACT_API_KEY", ""),
        temperature=float(env_config.get("MARKPACT_TEMPERATURE", "0.7")),
        max_tokens=int(env_config.get("MARKPACT_MAX_TOKENS", "4096")),
    )
    print(f"[markpact] Generating contract with {config.model}...")
    print(f"[markpact] Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    try:
        content = generate_contract(prompt, config, verbose=verbose)
    except Exception as e:
        print(f"[markpact] ERROR: {e}", file=sys.stderr)
        return 1, None
    output_path = Path(args.output) if args.output else Path("README.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    print(f"[markpact] Generated contract saved to: {output_path}")
    if args.run:
        print(f"[markpact] Running generated contract...")
        return 0, output_path
    print(f"[markpact] Run with: markpact {output_path}")
    if args.docker:
        print(f"[markpact] Or with Docker: markpact {output_path} --docker")
    return 0, None


def _handle_markdown_conversion(args, original_text: str, verbose: bool) -> tuple[str, bool]:
    """Handle markdown conversion if needed. Returns (text_to_parse, should_exit)."""
    has_markpact = re.search(r"^```(?:[^\s]+\s+)?markpact:", original_text, re.MULTILINE) is not None
    if args.convert or args.convert_only or (args.auto and not has_markpact):
        if verbose:
            print(f"[markpact] Converting to markpact format...")
        result = convert_markdown_to_markpact(original_text)
        if verbose or args.convert_only:
            print_conversion_report(result)
        if args.save_converted:
            save_path = Path(args.save_converted)
            save_path.write_text(result.converted_text)
            print(f"[markpact] Saved converted file to {save_path}")
        if args.convert_only:
            print("\n--- CONVERTED CONTENT ---\n")
            print(result.converted_text)
            return result.converted_text, True
        return result.converted_text, False
    elif not has_markpact and verbose:
        print(f"[markpact] WARNING: No markpact blocks found")
        print(f"[markpact] TIP: Use --convert or --auto to convert regular Markdown")
    return original_text, False


def _resolve_file_body(block, verbose: bool) -> str:
    """Resolve template placeholders if block has template=true."""
    is_template = block.get_meta_value("template") in ("true", "yes", "1")
    if not is_template:
        return block.body

    from .template import resolve_template, load_secrets, has_template_placeholders

    if not has_template_placeholders(block.body):
        return block.body

    path = block.get_path() or "<unknown>"
    if verbose:
        print(f"[markpact] Resolving template: {path}")

    secrets = load_secrets()
    body, warnings = resolve_template(
        block.body,
        secrets=secrets,
        interactive=sys.stdin.isatty(),
        verbose=verbose,
    )
    for w in warnings:
        print(f"[markpact] WARNING: {path}: {w}", file=sys.stderr)
    return body


def _parse_blocks_to_state(blocks, sandbox: Sandbox, args, verbose: bool) -> dict:
    """Parse blocks and extract state. Returns state dict with error key if failed."""
    state = {"deps": [], "run_command": None, "test_blocks": [], "publish_config_block": None, "had_publish_block": False}
    for block in blocks:
        if block.kind == "bootstrap":
            continue
        if block.kind == "file":
            path = block.get_path()
            if not path:
                print(f"[markpact] ERROR: markpact:file requires path=..., got: {block.meta}", file=sys.stderr)
                return {"error": True}
            body = _resolve_file_body(block, verbose)
            if args.dry_run:
                is_tpl = block.get_meta_value("template") in ("true", "yes", "1")
                tpl_hint = " (template)" if is_tpl else ""
                print(f"[markpact] Would write {sandbox.path / path}{tpl_hint}")
            else:
                f = sandbox.write_file(path, body)
                if verbose:
                    print(f"[markpact] wrote {f}")
        elif block.kind == "deps" and "python" in block.meta:
            state["deps"].extend(line.strip() for line in block.body.splitlines() if line.strip())
        elif block.kind == "run":
            state["run_command"] = block.body
        elif block.kind == "test":
            state["test_blocks"].append((block.meta, block.body))
        elif block.kind == "publish":
            state["publish_config_block"] = (block.meta, block.body)
            state["had_publish_block"] = True
    return state


def _resolve_publish_config(args, text_to_parse, readme, blocks, run_command, verbose):
    """Resolve publish config from args, LLM, inference, or prompts."""
    from .publisher import infer_publish_config, prompt_publish_config
    from .publisher import generate_publish_config_with_llm
    
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
        from .publisher import bump_version
        new_ver = bump_version(config.version, bump_type)
        print(f"[markpact] Would bump version to {new_ver}")


def _execute_publish_result(result, readme, bump_type, verbose):
    """Handle publish result and return exit code."""
    from .publisher import update_version_in_readme
    
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
    from .publisher import parse_publish_block, publish
    
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


def _handle_docker_mode(args, sandbox: Sandbox, deps: list[str], run_command: str | None, verbose: bool) -> int:
    """Handle Docker mode. Returns exit code."""
    from .docker_runner import check_docker_available, generate_dockerfile, build_and_run_docker
    if not check_docker_available():
        print("[markpact] ERROR: Docker is not available. Install Docker first.", file=sys.stderr)
        return 1
    if args.dry_run:
        print(f"[markpact] Would build and run Docker container")
        print(f"[markpact] Deps: {', '.join(deps)}")
        print(f"[markpact] Run: {run_command}")
        return 0
    generate_dockerfile(sandbox.path, deps, run_command.strip() if run_command else "python -m http.server 8000")
    return build_and_run_docker(sandbox.path, verbose=verbose)


def _print_dry_run_tests(test_blocks: list) -> None:
    """Print dry-run test information."""
    print(f"[markpact] Would run tests:")
    for meta, body in test_blocks:
        print(f"  [{meta}]: {len(body.splitlines())} tests")


def _split_test_blocks(test_blocks: list) -> tuple[list, list]:
    """Split test blocks into HTTP and shell tests."""
    http_tests = [body for meta, body in test_blocks if "http" in meta.lower() or not meta]
    shell_tests = [body for meta, body in test_blocks if "shell" in meta.lower() or "bash" in meta.lower()]
    return http_tests, shell_tests


def _run_http_tests(run_command: str | None, http_tests: list, sandbox: Sandbox, 
                    port: int, verbose: bool, test_only: bool) -> int | None:
    """Run HTTP tests and return exit code if test_only, None otherwise."""
    if not http_tests or not run_command:
        return None
    
    from .tester import run_service_with_tests
    test_body = "\n".join(http_tests)
    exit_code, suite = run_service_with_tests(run_command, test_body, sandbox, port=port, verbose=verbose)
    if test_only:
        return exit_code
    return None


def _run_shell_tests(shell_tests: list, sandbox: Sandbox, verbose: bool) -> None:
    """Run shell tests and print summary."""
    if not shell_tests:
        return
    
    from .tester import run_shell_tests
    shell_body = "\n".join(shell_tests)
    shell_suite = run_shell_tests(shell_body, sandbox, verbose=verbose)
    shell_suite.print_summary()


def _handle_test_mode(args, sandbox: Sandbox, run_command: str | None, test_blocks: list, 
                      deps: list[str], verbose: bool) -> int:
    """Handle test mode. Returns exit code."""
    from .auto_fix import find_free_port
    
    if args.dry_run:
        _print_dry_run_tests(test_blocks)
        return 0
    
    if deps:
        install_deps(deps, sandbox, verbose)
    
    port = find_free_port()
    http_tests, shell_tests = _split_test_blocks(test_blocks)
    
    http_exit_code = _run_http_tests(run_command, http_tests, sandbox, port, verbose, args.test_only)
    if http_exit_code is not None:
        return http_exit_code
    
    _run_shell_tests(shell_tests, sandbox, verbose)
    
    return 0


def _handle_normal_run(args, sandbox: Sandbox, run_command: str | None, deps: list[str], readme: Path, verbose: bool) -> int:
    """Handle normal run mode. Returns exit code."""
    if args.dry_run:
        print(f"[markpact] Would run: {run_command}")
        return 0
    
    if deps:
        install_deps(deps, sandbox, verbose)
    
    use_auto_fix = args.auto_fix and not args.no_auto_fix
    if use_auto_fix:
        from .auto_fix import run_with_auto_fix_llm
        run_with_auto_fix_llm(run_command, sandbox, readme_path=readme, verbose=verbose, use_llm=args.auto_fix_llm)
    else:
        run_cmd(run_command, sandbox, verbose)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point for markpact CLI."""
    args_list = argv if argv is not None else sys.argv[1:]
    
    # Handle subcommands early
    if args_list and args_list[0] == "config":
        return handle_config_cli(args_list[1:])
    if args_list and args_list[0] == "pack":
        return handle_pack_cli(args_list[1:])
    if args_list and args_list[0] == "sync":
        return handle_sync_cli(args_list[1:])
    
    # Main argument parser
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
    
    args = parser.parse_args(args_list)
    verbose = not args.quiet
    
    # Handle early-exit flags
    if args.list_examples:
        return _handle_list_examples(verbose)
    if args.list_notebook_formats:
        return _handle_list_notebook_formats(verbose)
    
    # Handle notebook conversion
    if args.from_notebook:
        exit_code, readme_path = _handle_from_notebook(args, verbose)
        if exit_code != 0 or readme_path is None:
            return exit_code
        args.readme = str(readme_path)
    
    # Handle LLM generation
    if args.prompt or args.example:
        exit_code, readme_path = _handle_llm_generation(args, verbose)
        if exit_code != 0 or readme_path is None:
            return exit_code
        args.readme = str(readme_path)
    
    # Now we need a README file to process
    readme = Path(args.readme)
    if not readme.exists():
        print(f"[markpact] ERROR: {readme} not found", file=sys.stderr)
        return 1
    
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
        from .parser import parse_blocks_recursive
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
        from .publisher import parse_publish_block
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


if __name__ == "__main__":
    sys.exit(main())
