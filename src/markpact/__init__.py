"""Markpact – Executable Markdown Runtime"""

__version__ = "0.1.37"

from .converter import convert_markdown_to_markpact, ConversionResult
from .packer import pack_directory, PackResult, print_pack_report
from .parser import Block, parse_blocks, parse_blocks_recursive
from .runner import run_cmd, ensure_venv
from .sandbox import Sandbox, find_free_port
from .syncer import (
    sync_readme, sync_readme_recursive, SyncResult, print_sync_report,
    list_tracked_paths, find_untracked_files, add_untracked_blocks,
    create_backup, list_backups, restore_backup,
)
from .template import resolve_template, has_template_placeholders

# Optional LLM generator (requires litellm)
try:
    from .generator import generate_contract, GeneratorConfig, EXAMPLE_PROMPTS
    _HAS_LLM = True
except ImportError:
    _HAS_LLM = False
    generate_contract = None
    GeneratorConfig = None
    EXAMPLE_PROMPTS = {}

__all__ = [
    "Block",
    "parse_blocks",
    "parse_blocks_recursive",
    "run_cmd",
    "ensure_venv",
    "Sandbox",
    "find_free_port",
    "convert_markdown_to_markpact",
    "ConversionResult",
    "pack_directory",
    "PackResult",
    "print_pack_report",
    "sync_readme",
    "sync_readme_recursive",
    "SyncResult",
    "print_sync_report",
    "list_tracked_paths",
    "find_untracked_files",
    "add_untracked_blocks",
    "create_backup",
    "list_backups",
    "restore_backup",
    "resolve_template",
    "has_template_placeholders",
    "generate_contract",
    "GeneratorConfig",
    "EXAMPLE_PROMPTS",
    "__version__",
]
