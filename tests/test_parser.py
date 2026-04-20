"""Tests for markpact parser"""

from markpact.parser import parse_blocks, Block


def test_parse_file_block():
    md = '''```python markpact:file path=app/main.py
print("hello")
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "file"
    assert blocks[0].get_path() == "app/main.py"
    assert blocks[0].body == 'print("hello")'


def test_parse_file_block_new_header():
    md = '''```python markpact:file path=app/main.py
print("hello")
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "file"
    assert blocks[0].lang == "python"
    assert blocks[0].get_path() == "app/main.py"
    assert blocks[0].body == 'print("hello")'


def test_parse_deps_block():
    md = '''```text markpact:deps python
fastapi
uvicorn
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "deps"
    assert "python" in blocks[0].meta
    assert "fastapi" in blocks[0].body


def test_parse_deps_block_new_header():
    md = '''```text markpact:deps python
fastapi
uvicorn
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "deps"
    assert blocks[0].lang == "text"
    assert blocks[0].meta == "python"
    assert "fastapi" in blocks[0].body


def test_parse_run_block():
    md = '''```bash markpact:run
python main.py
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "run"
    assert blocks[0].body == "python main.py"


def test_parse_run_block_new_header():
    md = '''```bash markpact:run
python main.py
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "run"
    assert blocks[0].lang == "bash"
    assert blocks[0].meta == ""
    assert blocks[0].body == "python main.py"


def test_parse_multiple_blocks():
    md = '''# Test

```text markpact:deps python
requests
```

```python markpact:file path=main.py
import requests
```

```bash markpact:run
python main.py
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 3
    assert [b.kind for b in blocks] == ["deps", "file", "run"]


def test_empty_meta():
    md = '''```bash markpact:run
echo hello
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].meta == ""
