"""Tests for markpact:include directive — recursive sub-README parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from markpact.parser import parse_blocks, parse_blocks_recursive, Block


class TestParseBlocksRecursive:
    """Test recursive include resolution."""

    def test_no_includes(self):
        md = '''```python markpact:file path=main.py
print("hello")
```'''
        blocks = parse_blocks_recursive(md)
        assert len(blocks) == 1
        assert blocks[0].kind == "file"
        assert blocks[0].get_path() == "main.py"

    def test_single_include(self, tmp_path):
        # Create sub-README
        sub_readme = tmp_path / "deploy" / "README.md"
        sub_readme.parent.mkdir()
        sub_readme.write_text('''# Deploy files

```yaml markpact:file path=deploy/traefik.yml
entryPoints:
  web:
    address: ":80"
```
''')

        # Main README with include
        main_md = '''# Project

```python markpact:file path=main.py
print("hello")
```

<!-- markpact:include path=deploy/README.md -->
'''
        blocks = parse_blocks_recursive(
            main_md,
            base_dir=tmp_path,
            source_file="README.md",
        )
        assert len(blocks) == 2
        assert blocks[0].get_path() == "main.py"
        assert blocks[0].source_file == "README.md"
        assert blocks[1].get_path() == "deploy/traefik.yml"
        assert blocks[1].source_file == "deploy/README.md"

    def test_nested_includes(self, tmp_path):
        # Level 2
        l2 = tmp_path / "a" / "b" / "README.md"
        l2.parent.mkdir(parents=True)
        l2.write_text('''```yaml markpact:file path=deep.yml
key: value
```
''')

        # Level 1
        l1 = tmp_path / "a" / "README.md"
        l1.write_text('''```yaml markpact:file path=mid.yml
mid: true
```

<!-- markpact:include path=b/README.md -->
''')

        # Root
        root_md = '''```yaml markpact:file path=root.yml
root: true
```

<!-- markpact:include path=a/README.md -->
'''
        blocks = parse_blocks_recursive(
            root_md,
            base_dir=tmp_path,
            source_file="README.md",
        )
        paths = [b.get_path() for b in blocks]
        assert "root.yml" in paths
        assert "mid.yml" in paths
        assert "deep.yml" in paths
        assert len(blocks) == 3

    def test_circular_include_detected(self, tmp_path):
        # A includes B, B includes A
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text('''```yaml markpact:file path=from_a.yml
a: true
```

<!-- markpact:include path=b.md -->
''')
        b.write_text('''```yaml markpact:file path=from_b.yml
b: true
```

<!-- markpact:include path=a.md -->
''')

        blocks = parse_blocks_recursive(
            a.read_text(),
            base_dir=tmp_path,
            source_file="a.md",
        )
        # Should get blocks from both files, but not loop infinitely
        paths = [b.get_path() for b in blocks]
        assert "from_a.yml" in paths
        assert "from_b.yml" in paths
        assert len(blocks) == 2

    def test_missing_include_skipped(self, tmp_path):
        md = '''```yaml markpact:file path=main.yml
key: value
```

<!-- markpact:include path=nonexistent/README.md -->
'''
        blocks = parse_blocks_recursive(md, base_dir=tmp_path)
        assert len(blocks) == 1
        assert blocks[0].get_path() == "main.yml"

    def test_max_depth(self, tmp_path):
        # Create chain: 0 → 1 → 2 → 3 → 4 → 5
        for i in range(6):
            d = tmp_path / f"level{i}"
            d.mkdir()
            content = f'''```yaml markpact:file path=l{i}.yml
level: {i}
```
'''
            if i < 5:
                content += f"\n<!-- markpact:include path=level{i+1}/README.md -->\n"
            (d / "README.md").write_text(content)

        root_md = "<!-- markpact:include path=level0/README.md -->\n"
        blocks = parse_blocks_recursive(root_md, base_dir=tmp_path, max_depth=3)
        # Should stop at depth 3, not reaching all 6 levels
        assert len(blocks) < 6

    def test_source_file_tracking(self, tmp_path):
        sub = tmp_path / "sub.md"
        sub.write_text('''```yaml markpact:file path=sub.yml
key: val
```
''')
        md = '''```yaml markpact:file path=root.yml
root: true
```

<!-- markpact:include path=sub.md -->
'''
        blocks = parse_blocks_recursive(
            md, base_dir=tmp_path, source_file="main.md"
        )
        assert blocks[0].source_file == "main.md"
        assert blocks[1].source_file == "sub.md"


class TestBlockSourceFile:
    """Test that source_file is set on blocks."""

    def test_default_none(self):
        blocks = parse_blocks('```yaml markpact:file path=f.yml\nk: v\n```')
        assert blocks[0].source_file is None

    def test_explicit_source(self):
        blocks = parse_blocks(
            '```yaml markpact:file path=f.yml\nk: v\n```',
            source_file="README.md",
        )
        assert blocks[0].source_file == "README.md"
