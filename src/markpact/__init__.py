"""Markpact – Executable Markdown Runtime"""

__version__ = "0.1.20"

from .converter import convert_markdown_to_markpact, ConversionResult
from .parser import Block, parse_blocks
from .runner import run_cmd, ensure_venv
from .sandbox import Sandbox, find_free_port

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
    "run_cmd",
    "ensure_venv",
    "Sandbox",
    "find_free_port",
    "convert_markdown_to_markpact",
    "ConversionResult",
    "generate_contract",
    "GeneratorConfig",
    "EXAMPLE_PROMPTS",
    "__version__",
]
