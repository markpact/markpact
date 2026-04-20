"""Parser for markpact markdown files."""
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class BlockType(Enum):
    """Types of markpact blocks."""
    CONFIG = auto()      # markpact:config
    STEPS = auto()       # markpact:steps
    ROLLBACK = auto()    # markpact:rollback
    RUN = auto()         # markpact:run
    PYTHON = auto()      # markpact:python
    BASH = auto()        # markpact:bash or ```bash
    YAML = auto()        # markpact:yaml or ```yaml
    TOML = auto()        # markpact:toml or ```toml
    JSON = auto()        # markpact:json or ```json
    UNKNOWN = auto()     # Unrecognized


@dataclass
class Block:
    """A parsed markpact block."""
    type: BlockType
    content: str
    meta: str = ""        # Additional metadata from block header
    language: str = ""   # Language hint
    line_start: int = 0   # Starting line number
    line_end: int = 0     # Ending line number


class MarkpactParser:
    """Parser for markpact markdown files.
    
    Extracts markpact blocks from markdown files:
    - ```markpact:config ... ```
    - ```markpact:steps ... ```
    - ```markpact:run ... ```
    - ```markpact:python ... ```
    - And other language-specific blocks
    """
    
    # Regex to match markpact blocks
    MARKPACT_RE = re.compile(
        r'^```markpact:(?P<kind>\w+)(?:\s+(?P<meta>[^\n]*))?\n'
        r'(?P<content>.*?)'
        r'^```\s*$',
        re.MULTILINE | re.DOTALL
    )
    
    # Regex to match standard code blocks that might contain steps
    CODE_BLOCK_RE = re.compile(
        r'^```(?P<lang>\w+)(?:\s+(?P<meta>[^\n]*))?\n'
        r'(?P<content>.*?)'
        r'^```\s*$',
        re.MULTILINE | re.DOTALL
    )
    
    def __init__(self):
        self.blocks: List[Block] = []
    
    def parse(self, content: str) -> List[Block]:
        """Parse markdown content and extract markpact blocks.
        
        Args:
            content: Markdown content as string
            
        Returns:
            List of parsed Block objects
        """
        self.blocks = []
        
        # First, find all markpact blocks
        for match in self.MARKPACT_RE.finditer(content):
            kind = match.group('kind')
            meta = match.group('meta') or ""
            block_content = match.group('content')
            
            block_type = self._parse_block_type(kind)
            
            self.blocks.append(Block(
                type=block_type,
                content=block_content,
                meta=meta,
                language=kind,
                line_start=content[:match.start()].count('\n') + 1,
                line_end=content[:match.end()].count('\n') + 1,
            ))
        
        # Then find standard code blocks (for backward compatibility)
        # but only if they don't overlap with markpact blocks
        markpact_spans = set()
        for match in self.MARKPACT_RE.finditer(content):
            markpact_spans.update(range(match.start(), match.end()))
        
        for match in self.CODE_BLOCK_RE.finditer(content):
            # Skip if overlaps with markpact blocks
            if any(i in markpact_spans for i in range(match.start(), match.end())):
                continue
            
            lang = match.group('lang')
            if lang in ('yaml', 'toml', 'json', 'bash', 'python', 'shell'):
                block_content = match.group('content')
                
                # Map language to block type
                lang_to_type = {
                    'yaml': BlockType.YAML,
                    'toml': BlockType.TOML,
                    'json': BlockType.JSON,
                    'bash': BlockType.BASH,
                    'shell': BlockType.BASH,
                    'python': BlockType.PYTHON,
                    'py': BlockType.PYTHON,
                }
                
                self.blocks.append(Block(
                    type=lang_to_type.get(lang, BlockType.UNKNOWN),
                    content=block_content,
                    language=lang,
                    line_start=content[:match.start()].count('\n') + 1,
                    line_end=content[:match.end()].count('\n') + 1,
                ))
        
        # Sort by line number
        self.blocks.sort(key=lambda b: b.line_start)
        
        return self.blocks
    
    def _parse_block_type(self, kind: str) -> BlockType:
        """Parse block type from kind string."""
        kind_map = {
            'config': BlockType.CONFIG,
            'steps': BlockType.STEPS,
            'rollback': BlockType.ROLLBACK,
            'run': BlockType.RUN,
            'python': BlockType.PYTHON,
            'bash': BlockType.BASH,
            'shell': BlockType.BASH,
            'yaml': BlockType.YAML,
            'toml': BlockType.TOML,
            'json': BlockType.JSON,
        }
        return kind_map.get(kind.lower(), BlockType.UNKNOWN)
    
    def get_blocks_by_type(self, block_type: BlockType) -> List[Block]:
        """Get all blocks of a specific type."""
        return [b for b in self.blocks if b.type == block_type]
    
    def get_first_block(self, block_type: BlockType) -> Optional[Block]:
        """Get first block of a specific type."""
        blocks = self.get_blocks_by_type(block_type)
        return blocks[0] if blocks else None
