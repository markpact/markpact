"""Markpact codeblock parser"""

from __future__ import annotations

import re
from dataclasses import dataclass
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

    def get_path(self) -> str | None:
        """Extract path= from meta"""
        m = re.search(r"\bpath=(\S+)", self.meta)
        return m[1] if m else None

    def get_meta_value(self, key: str) -> Optional[str]:
        """Extract a key=value pair from the meta string."""
        m = re.search(rf"\b{re.escape(key)}=(\S+)", self.meta)
        return m[1] if m else None


def parse_blocks(text: str) -> list[Block]:
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
        ))

    # Parse old format: ```markpact:file python path=main.py
    for m in CODEBLOCK_OLD_RE.finditer(text):
        blocks.append(Block(
            kind=m.group("kind"),
            meta=(m.group("meta") or "").strip(),
            body=m.group("body").strip(),
            lang="",  # Old format doesn't have separate lang
        ))

    return blocks
