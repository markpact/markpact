"""markpact portal — markpact.com registry client subcommand."""

from __future__ import annotations

from ..portal.client import main as portal_main


def handle_portal_cli(argv: list[str]) -> int:
    return portal_main(argv)
