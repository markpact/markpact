"""Markpact codeblock parser"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# New format: ```python markpact:file path=main.py
CODEBLOCK_NEW_RE = re.compile(
    r"```(?P<lang>\w+)\s+markpact:(?P<kind>\w+)(?:[ \t]+(?P<meta>[^\n]*))?\n(?P<body>[\s\S]*?)\n```",
)

# Old format: ```markpact:file python path=main.py
CODEBLOCK_OLD_RE = re.compile(
    r"```markpact:(?P<kind>\w+)(?:[ \t]+(?P<meta>[^\n]*))?\n(?P<body>[\s\S]*?)\n```",
)


@dataclass
class Block:
    kind: str
    meta: str
    body: str
    lang: str = ""
    source_file: str | None = None  # which README this block came from

    def get_path(self) -> str | None:
        """Extract path= from meta"""
        m = re.search(r"\bpath=(\S+)", self.meta)
        return m[1] if m else None

    def get_meta_value(self, key: str) -> Optional[str]:
        """Extract a key=value pair from the meta string."""
        m = re.search(rf"\b{re.escape(key)}=(\S+)", self.meta)
        return m[1] if m else None


def parse_blocks(text: str, *, source_file: str | None = None) -> list[Block]:
    """Parse all markpact:* codeblocks from markdown text.

    Supports both formats:
    - New: ```python markpact:file path=main.py
    - Old: ```markpact:file python path=main.py
    """
    blocks: list[Block] = []

    # Parse new format: ```python markpact:file path=main.py
    for m in CODEBLOCK_NEW_RE.finditer(text):
        blocks.append(Block(
            kind=m.group("kind"),
            meta=(m.group("meta") or "").strip(),
            body=m.group("body").strip(),
            lang=(m.group("lang") or "").strip(),
            source_file=source_file,
        ))

    # Parse old format: ```markpact:file python path=main.py
    for m in CODEBLOCK_OLD_RE.finditer(text):
        blocks.append(Block(
            kind=m.group("kind"),
            meta=(m.group("meta") or "").strip(),
            body=m.group("body").strip(),
            lang="",  # Old format doesn't have separate lang
            source_file=source_file,
        ))

    return blocks


# ─── Include directive ────────────────────────────────────────────────────────

# Inline include: <!-- markpact:include path=deploy/README.md -->
_INCLUDE_COMMENT_RE = re.compile(
    r"<!--\s*markpact:include\s+path=(\S+)\s*-->"
)


def parse_blocks_recursive(
    text: str,
    *,
    base_dir: Path | None = None,
    source_file: str | None = None,
    max_depth: int = 5,
    _depth: int = 0,
    _seen: set[str] | None = None,
    verbose: bool = False,
) -> list[Block]:
    """Parse blocks with recursive include resolution.

    Resolves ``<!-- markpact:include path=sub/README.md -->`` directives
    by loading the referenced file and recursively parsing its blocks.
    Include paths are relative to base_dir (or CWD).

    Circular includes are detected and skipped.

    Args:
        text: Markdown content.
        base_dir: Directory for resolving include paths.
        source_file: Label for this source (e.g., "README.md").
        max_depth: Maximum include nesting depth.
        verbose: Print include resolution.

    Returns:
        Flat list of blocks from this file and all includes.
    """
    if _seen is None:
        _seen = set()

    blocks = parse_blocks(text, source_file=source_file)

    if _depth >= max_depth:
        return blocks

    base = base_dir or Path.cwd()

    # Register root file as seen to prevent circular includes
    if source_file and _depth == 0:
        root_resolved = (base / source_file).resolve()
        _seen.add(str(root_resolved))

    for m in _INCLUDE_COMMENT_RE.finditer(text):
        include_path = m.group(1)
        resolved = (base / include_path).resolve()
        resolved_str = str(resolved)

        if resolved_str in _seen:
            if verbose:
                print(f"[markpact] Skipping circular include: {include_path}")
            continue

        if not resolved.exists():
            if verbose:
                print(f"[markpact] Include not found: {include_path} (from {source_file or 'root'})")
            continue

        _seen.add(resolved_str)
        if verbose:
            print(f"[markpact] Including: {include_path}")

        sub_text = resolved.read_text(encoding="utf-8")
        sub_blocks = parse_blocks_recursive(
            sub_text,
            base_dir=resolved.parent,
            source_file=include_path,
            max_depth=max_depth,
            _depth=_depth + 1,
            _seen=_seen,
            verbose=verbose,
        )
        blocks.extend(sub_blocks)

    return blocks
