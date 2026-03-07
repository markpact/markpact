"""Tests for CLI subcommand modules — dispatch, sync, pack, config, publish, run."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from markpact.cli import main, _dispatch_subcommand, _parse_main_args


# ── Dispatch ─────────────────────────────────────────────────────────────────

class TestDispatch:
    def test_config_subcommand(self, capsys):
        """config subcommand dispatches correctly."""
        with pytest.raises(SystemExit) as exc_info:
            main(["config", "--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "config" in captured.out

    def test_unknown_subcommand_falls_through(self):
        """Unknown first arg is not treated as subcommand."""
        # 'nonexistent' is not in _SUBCOMMANDS, so it's treated as a readme path
        result = main(["nonexistent.md"])
        assert result == 1  # file not found

    def test_dispatch_returns_1_for_unknown(self):
        assert _dispatch_subcommand("nope", []) == 1


# ── Argument parsing ─────────────────────────────────────────────────────────

class TestParseMainArgs:
    def test_defaults(self):
        args = _parse_main_args([])
        assert args.readme == "README.md"
        assert args.dry_run is False
        assert args.quiet is False
        assert args.publish is False

    def test_dry_run(self):
        args = _parse_main_args(["--dry-run"])
        assert args.dry_run is True

    def test_quiet(self):
        args = _parse_main_args(["-q"])
        assert args.quiet is True

    def test_publish_with_bump(self):
        args = _parse_main_args(["--publish", "--bump", "minor"])
        assert args.publish is True
        assert args.bump == "minor"

    def test_custom_readme(self):
        args = _parse_main_args(["my_file.md"])
        assert args.readme == "my_file.md"

    def test_recursive_flag(self):
        args = _parse_main_args(["-R"])
        assert args.recursive is True

    def test_docker_flag(self):
        args = _parse_main_args(["--docker"])
        assert args.docker is True

    def test_test_flag(self):
        args = _parse_main_args(["--test"])
        assert args.test is True


# ── Sync subcommand ──────────────────────────────────────────────────────────

class TestSyncSubcommand:
    def test_sync_basic(self, tmp_path):
        src = tmp_path / "sandbox"
        src.mkdir()
        (src / "app.py").write_text("print('hello')\n")
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Project\n\n"
            "```python markpact:file path=app.py\n"
            "print('hello')\n"
            "```\n"
        )
        result = main(["sync", str(readme), "--source", str(src)])
        assert result == 0

    def test_sync_dry_run(self, tmp_path, capsys):
        src = tmp_path / "sandbox"
        src.mkdir()
        (src / "app.py").write_text("print('updated')\n")
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Project\n\n"
            "```python markpact:file path=app.py\n"
            "print('hello')\n"
            "```\n"
        )
        result = main(["sync", str(readme), "--source", str(src), "--dry-run"])
        assert result == 0

    def test_sync_nonexistent_file(self):
        result = main(["sync", "/nonexistent/readme.md"])
        assert result == 1

    def test_sync_list_tracked(self, tmp_path, capsys):
        src = tmp_path / "sandbox"
        src.mkdir()
        readme = tmp_path / "README.md"
        readme.write_text(
            "```python markpact:file path=app.py\n"
            "print('hello')\n"
            "```\n"
        )
        result = main(["sync", str(readme), "--source", str(src), "--list"])
        assert result == 0
        captured = capsys.readouterr()
        assert "app.py" in captured.out


# ── Pack subcommand ──────────────────────────────────────────────────────────

class TestPackSubcommand:
    def test_pack_basic(self, tmp_path):
        src = tmp_path / "myproject"
        src.mkdir()
        (src / "app.py").write_text("print('hello')\n")
        output = tmp_path / "output.md"
        result = main(["pack", str(src), "--output", str(output)])
        assert result == 0
        assert output.exists()
        content = output.read_text()
        assert "markpact:file" in content

    def test_pack_dry_run(self, tmp_path, capsys):
        src = tmp_path / "myproject"
        src.mkdir()
        (src / "main.py").write_text("print('dry')\n")
        result = main(["pack", str(src), "--dry-run"])
        assert result == 0

    def test_pack_nonexistent(self):
        result = main(["pack", "/nonexistent/dir"])
        assert result == 1


# ── Main entry point integration ─────────────────────────────────────────────

class TestMainIntegration:
    def test_dry_run_with_markpact_blocks(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Test\n\n"
            "```text markpact:deps python\nflask\n```\n\n"
            "```python markpact:file path=app.py\nprint('hi')\n```\n\n"
            "```bash markpact:run\npython app.py\n```\n"
        )
        result = main([str(readme), "--dry-run", "-s", str(tmp_path / "sandbox")])
        assert result == 0

    def test_recursive_dry_run(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        sub_readme = sub / "README.md"
        sub_readme.write_text(
            "```python markpact:file path=lib.py\ndef helper(): pass\n```\n"
        )
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Main\n\n"
            "```markpact:include path=sub/README.md\n```\n\n"
            "```bash markpact:run\npython -c 'print(1)'\n```\n"
        )
        result = main([str(readme), "--dry-run", "-R", "-s", str(tmp_path / "sandbox")])
        assert result == 0

    def test_quiet_mode_suppresses_parsing(self, tmp_path, capsys):
        readme = tmp_path / "README.md"
        readme.write_text(
            "```text markpact:deps python\nflask\n```\n"
            "```python markpact:file path=app.py\nprint('hi')\n```\n"
        )
        result = main([str(readme), "--dry-run", "-q", "-s", str(tmp_path / "sandbox")])
        assert result == 0
        captured = capsys.readouterr()
        # Quiet mode suppresses the "Parsing" message
        assert "Parsing" not in captured.out
