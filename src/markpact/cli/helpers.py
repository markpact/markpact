"""Shared CLI helpers — block parsing, template resolution."""

from __future__ import annotations

import sys

from ..sandbox import Sandbox


def _resolve_file_body(block, verbose: bool) -> str:
    """Resolve template placeholders if block has template=true."""
    is_template = block.get_meta_value("template") in ("true", "yes", "1")
    if not is_template:
        return block.body

    from ..template import resolve_template, load_secrets, has_template_placeholders

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
