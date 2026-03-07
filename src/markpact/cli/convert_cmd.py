"""Conversion handlers — notebook, markdown, LLM generation."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from ..converter import convert_markdown_to_markpact, print_conversion_report


def _handle_list_examples(verbose: bool) -> int:
    """Handle --list-examples flag."""
    from ..generator import list_example_prompts
    print("\n[markpact] Available example prompts:\n")
    for name, desc in list_example_prompts().items():
        print(f"  {name:15} - {desc}")
    print(f"\nUsage: markpact -e todo-api -o my-project/README.md")
    return 0


def _handle_list_notebook_formats(verbose: bool) -> int:
    """Handle --list-notebook-formats flag."""
    from ..notebook_converter import get_supported_formats
    print("\n[markpact] Supported notebook formats:\n")
    for ext, name in get_supported_formats().items():
        print(f"  {ext:8} - {name}")
    print(f"\nUsage: markpact --from-notebook notebook.ipynb -o project/README.md")
    return 0


def _handle_from_notebook(args, verbose: bool) -> tuple[int, Path | None]:
    """Handle --from-notebook conversion. Returns (exit_code, readme_path_or_none)."""
    from ..notebook_converter import convert_notebook
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
        from ..generator import generate_contract, GeneratorConfig, get_example_prompt
        from ..config import load_env, init_env
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
