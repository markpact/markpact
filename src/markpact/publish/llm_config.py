"""LLM-based publish config generation."""

from __future__ import annotations

import os
import re
from typing import Optional

from .models import PublishConfig


def _setup_llm_for_publish() -> tuple:
    """Setup LLM configuration for publish config generation. Returns (cfg, litellm_module, available)."""
    try:
        from ..generator import GeneratorConfig, litellm, LITELLM_AVAILABLE
    except Exception:
        return None, None, False

    if not LITELLM_AVAILABLE:
        return None, None, False

    cfg = GeneratorConfig.from_env()
    return cfg, litellm, True


def _set_provider_api_key_for_publish(cfg) -> None:
    """Set provider-specific API key environment variables."""
    if not cfg.api_key:
        return

    model_lower = cfg.model.lower()
    if "openrouter" in model_lower:
        os.environ["OPENROUTER_API_KEY"] = cfg.api_key
    elif "openai" in model_lower or cfg.model.startswith("gpt"):
        os.environ["OPENAI_API_KEY"] = cfg.api_key
    elif "anthropic" in model_lower or "claude" in model_lower:
        os.environ["ANTHROPIC_API_KEY"] = cfg.api_key
    elif "groq" in model_lower:
        os.environ["GROQ_API_KEY"] = cfg.api_key


def _call_llm_for_publish_config(litellm, cfg, markdown: str) -> Optional[str]:
    """Call LLM to generate publish config. Returns content or None on failure."""
    system = (
        "You extract publishing metadata from a README. "
        "Return ONLY a single markpact:publish codeblock. "
        'Choose registry="docker" for web services (uvicorn/gunicorn/flask/node server). '
        'Choose registry="pypi" for Python libraries. '
        'Choose registry="npm" for Node libraries. '
        "Always include: registry, name, version, description, author, license."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": markdown[:12000]},
    ]

    try:
        resp = litellm.completion(
            model=cfg.model,
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )
        return resp.choices[0].message.content
    except Exception:
        return None


def _extract_publish_block_from_response(content: str) -> tuple[Optional[str], Optional[str]]:
    """Extract publish block meta and body from LLM response."""
    m = re.search(r"```(?:[^\s]+\s+)?markpact:publish(?P<meta>[^\n]*)\n(?P<body>.*?)\n```", content, re.DOTALL)
    if not m:
        return None, None
    meta = (m.group("meta") or "").strip()
    body = (m.group("body") or "").strip()
    return meta, body


def generate_publish_config_with_llm(markdown: str, verbose: bool = False) -> Optional[PublishConfig]:
    """Try to generate a publish config using LLM.

    Requires optional dependency markpact[llm].
    """
    from .main import parse_publish_block

    cfg, litellm, available = _setup_llm_for_publish()
    if not available or cfg is None:
        return None

    if cfg.api_base:
        litellm.api_base = cfg.api_base

    _set_provider_api_key_for_publish(cfg)

    content = _call_llm_for_publish_config(litellm, cfg, markdown)
    if content is None:
        return None

    meta, body = _extract_publish_block_from_response(content)
    if meta is None or body is None:
        return None

    try:
        return parse_publish_block(body, meta)
    except Exception:
        return None
