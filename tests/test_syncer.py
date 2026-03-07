"""Tests for markpact syncer"""

import textwrap
from pathlib import Path

from markpact.syncer import (
    list_tracked_paths,
    find_untracked_files,
    sync_readme,
    sync_readme_recursive,
    diff_block,
    create_backup,
    list_backups,
    restore_backup,
    add_untracked_blocks,
    _detect_lang,
    BACKUP_DIR_NAME,
    BACKUP_PREFIX,
    MAX_BACKUPS,
)


# ─── list_tracked_paths ──────────────────────────────────────────────────────

def test_list_tracked_old_format():
    md = textwrap.dedent("""\
        # Project

        ```markpact:file path=main.py
        print("hello")
        ```

        ```markpact:file path=lib/utils.py
        def foo(): pass
        ```
    """)
    paths = list_tracked_paths(md)
    assert paths == ["main.py", "lib/utils.py"]


def test_list_tracked_new_format():
    md = textwrap.dedent("""\
        # Project

        ```python markpact:file path=main.py
        print("hello")
        ```

        ```bash markpact:file path=run.sh
        echo hi
        ```
    """)
    paths = list_tracked_paths(md)
    assert paths == ["main.py", "run.sh"]


def test_list_tracked_mixed_formats():
    md = textwrap.dedent("""\
        ```markpact:file path=old.py
        x = 1
        ```

        ```python markpact:file path=new.py
        y = 2
        ```
    """)
    paths = list_tracked_paths(md)
    assert set(paths) == {"old.py", "new.py"}


def test_list_tracked_empty():
    md = "# No blocks here\n\nJust text.\n"
    assert list_tracked_paths(md) == []


# ─── find_untracked_files ────────────────────────────────────────────────────

def test_find_untracked(tmp_path):
    md = textwrap.dedent("""\
        ```markpact:file path=main.py
        print("hello")
        ```
    """)
    # Create source files
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "extra.py").write_text("print('extra')")
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "util.py").write_text("pass")

    untracked = find_untracked_files(md, tmp_path)
    assert set(untracked) == {"extra.py", "lib/util.py"}


def test_find_untracked_excludes_dirs(tmp_path):
    md = "```markpact:file path=main.py\npass\n```"
    (tmp_path / "main.py").write_text("pass")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "main.cpython-312.pyc").write_bytes(b"")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.js").write_text("x")

    untracked = find_untracked_files(md, tmp_path)
    assert untracked == []


def test_find_untracked_nonexistent_dir():
    md = "```markpact:file path=main.py\npass\n```"
    untracked = find_untracked_files(md, Path("/nonexistent/dir"))
    assert untracked == []


# ─── sync_readme ──────────────────────────────────────────────────────────────

def test_sync_updates_old_format(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        # Project

        ```markpact:file path=main.py
        print("old")
        ```
    """))
    (src / "main.py").write_text('print("new")\n')

    result = sync_readme(readme, src)
    assert result.success
    assert result.updated == 1
    assert result.unchanged == 0

    updated = readme.read_text()
    assert 'print("new")' in updated
    assert 'print("old")' not in updated


def test_sync_updates_new_format(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        # Project

        ```python markpact:file path=main.py
        print("old")
        ```
    """))
    (src / "main.py").write_text('print("new")\n')

    result = sync_readme(readme, src)
    assert result.success
    assert result.updated == 1

    updated = readme.read_text()
    assert 'print("new")' in updated


def test_sync_unchanged(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        ```markpact:file path=main.py
        print("same")
        ```
    """))
    (src / "main.py").write_text('print("same")\n')

    result = sync_readme(readme, src)
    assert result.success
    assert result.updated == 0
    assert result.unchanged == 1


def test_sync_missing_source_file(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        ```markpact:file path=missing.py
        old content
        ```
    """))

    result = sync_readme(readme, src)
    assert result.success
    assert result.missing == 1
    assert result.updated == 0


def test_sync_excluded_file(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        ```markpact:file path=.env
        SECRET=old
        ```
    """))
    (src / ".env").write_text("SECRET=new_actual_secret\n")

    result = sync_readme(readme, src, exclude_sync={".env"})
    assert result.success
    assert result.excluded == 1
    assert result.updated == 0

    # .env should NOT have been updated
    assert "old" in readme.read_text()


def test_sync_dry_run(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    original = textwrap.dedent("""\
        ```markpact:file path=main.py
        print("old")
        ```
    """)
    readme.write_text(original)
    (src / "main.py").write_text('print("new")\n')

    result = sync_readme(readme, src, dry_run=True)
    assert result.success
    assert result.updated == 1
    assert result.dry_run

    # File should NOT have changed
    assert readme.read_text() == original


def test_sync_multiple_files(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()
    (src / "scripts").mkdir()

    readme.write_text(textwrap.dedent("""\
        # Project

        ```markpact:file path=main.py
        old_main
        ```

        Some docs here.

        ```markpact:file path=scripts/run.sh
        old_script
        ```
    """))
    (src / "main.py").write_text("new_main\n")
    (src / "scripts" / "run.sh").write_text("new_script\n")

    result = sync_readme(readme, src)
    assert result.success
    assert result.updated == 2

    updated = readme.read_text()
    assert "new_main" in updated
    assert "new_script" in updated
    assert "Some docs here." in updated  # prose preserved


def test_sync_preserves_surrounding_text(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        # My Project

        This is a great project.

        ## Files

        ```markpact:file path=app.py
        old_code
        ```

        ## Usage

        Run it with `python app.py`.
    """))
    (src / "app.py").write_text("new_code\n")

    result = sync_readme(readme, src)
    updated = readme.read_text()

    assert "# My Project" in updated
    assert "This is a great project." in updated
    assert "## Usage" in updated
    assert "Run it with `python app.py`." in updated
    assert "new_code" in updated


def test_sync_nonexistent_readme(tmp_path):
    result = sync_readme(tmp_path / "nope.md", tmp_path)
    assert not result.success
    assert "not found" in result.message


def test_sync_nonexistent_source_dir(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# test")
    result = sync_readme(readme, tmp_path / "nope")
    assert not result.success
    assert "not found" in result.message


# ─── diff_block ───────────────────────────────────────────────────────────────

def test_diff_block_shows_changes():
    d = diff_block("main.py", 'print("old")', 'print("new")')
    assert "old" in d
    assert "new" in d
    assert "README:main.py" in d
    assert "source/main.py" in d


def test_diff_block_identical():
    d = diff_block("main.py", "same", "same")
    assert d == ""


# ─── create_backup ─────────────────────────────────────────────────────────────────

def test_create_backup(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# Original")

    bak = create_backup(readme)
    assert bak is not None
    assert bak.exists()
    assert bak.read_text() == "# Original"
    assert BACKUP_DIR_NAME in str(bak.parent)
    assert BACKUP_PREFIX in bak.name


def test_create_backup_nonexistent(tmp_path):
    bak = create_backup(tmp_path / "nope.md")
    assert bak is None


def test_create_backup_prunes_old(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("content")

    # Create MAX_BACKUPS + 5 backups manually
    bak_dir = tmp_path / BACKUP_DIR_NAME
    bak_dir.mkdir()
    for i in range(MAX_BACKUPS + 5):
        (bak_dir / f"{BACKUP_PREFIX}20240101_{i:06d}").write_text(f"v{i}")

    create_backup(readme)

    remaining = list(bak_dir.glob(f"{BACKUP_PREFIX}*"))
    assert len(remaining) <= MAX_BACKUPS


# ─── list_backups ──────────────────────────────────────────────────────────────────

def test_list_backups_empty(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("x")
    assert list_backups(readme) == []


def test_list_backups_ordered(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("x")
    bak_dir = tmp_path / BACKUP_DIR_NAME
    bak_dir.mkdir()
    (bak_dir / f"{BACKUP_PREFIX}20240101_100000").write_text("old")
    (bak_dir / f"{BACKUP_PREFIX}20240102_100000").write_text("new")

    backups = list_backups(readme)
    assert len(backups) == 2
    assert "20240102" in backups[0].name  # newest first


# ─── restore_backup ───────────────────────────────────────────────────────────────

def test_restore_latest(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# Original")

    # Create backup, then modify
    create_backup(readme)
    readme.write_text("# Modified")
    assert readme.read_text() == "# Modified"

    # Rollback
    ok = restore_backup(readme)
    assert ok
    assert readme.read_text() == "# Original"


def test_restore_specific(tmp_path):
    readme = tmp_path / "README.md"
    bak_dir = tmp_path / BACKUP_DIR_NAME
    bak_dir.mkdir()

    readme.write_text("# v1")
    bak1 = bak_dir / f"{BACKUP_PREFIX}20240101_100000"
    bak1.write_text("# v1")

    readme.write_text("# v2")
    bak2 = bak_dir / f"{BACKUP_PREFIX}20240102_100000"
    bak2.write_text("# v2")

    readme.write_text("# v3")

    # Restore to v1 specifically
    ok = restore_backup(readme, bak1)
    assert ok
    assert readme.read_text() == "# v1"


def test_restore_no_backups(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("x")
    ok = restore_backup(readme)
    assert not ok


def test_restore_nonexistent_backup(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("x")
    ok = restore_backup(readme, tmp_path / "nope")
    assert not ok


# ─── sync_readme creates backup ─────────────────────────────────────────────────

def test_sync_creates_backup_on_update(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        ```markpact:file path=main.py
        print("old")
        ```
    """))
    (src / "main.py").write_text('print("new")\n')

    result = sync_readme(readme, src)
    assert result.updated == 1

    backups = list_backups(readme)
    assert len(backups) == 1
    assert 'print("old")' in backups[0].read_text()


def test_sync_no_backup_when_unchanged(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        ```markpact:file path=main.py
        print("same")
        ```
    """))
    (src / "main.py").write_text('print("same")\n')

    sync_readme(readme, src)

    backups = list_backups(readme)
    assert len(backups) == 0  # no backup needed


def test_sync_then_rollback(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    original = textwrap.dedent("""\
        ```markpact:file path=main.py
        print("old")
        ```
    """)
    readme.write_text(original)
    (src / "main.py").write_text('print("new")\n')

    # Sync
    sync_readme(readme, src)
    assert 'print("new")' in readme.read_text()

    # Rollback
    ok = restore_backup(readme)
    assert ok
    assert readme.read_text() == original


# ─── hash_blocks ─────────────────────────────────────────────────────────────

def test_sync_hash_blocks_adds_sha256(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        ```python markpact:file path=main.py
        print("old")
        ```
    """))
    (src / "main.py").write_text('print("new")\n')

    result = sync_readme(readme, src, hash_blocks=True)
    assert result.success
    assert result.updated == 1

    updated = readme.read_text()
    assert "sha256=" in updated
    assert 'print("new")' in updated


def test_sync_hash_blocks_updates_existing_sha(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        ```python markpact:file path=main.py sha256=oldhash12345
        print("old")
        ```
    """))
    (src / "main.py").write_text('print("new")\n')

    result = sync_readme(readme, src, hash_blocks=True)
    assert result.success
    assert result.updated == 1

    updated = readme.read_text()
    assert "oldhash12345" not in updated
    assert "sha256=" in updated


def test_sync_hash_blocks_preserves_other_meta(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        ```yaml markpact:file path=.env template=true
        KEY=old
        ```
    """))
    (src / ".env").write_text("KEY=new\n")

    result = sync_readme(readme, src, hash_blocks=True)
    assert result.success

    updated = readme.read_text()
    assert "template=true" in updated
    assert "sha256=" in updated
    assert "KEY=new" in updated


def test_sync_no_hash_by_default(tmp_path):
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        ```python markpact:file path=main.py
        print("old")
        ```
    """))
    (src / "main.py").write_text('print("new")\n')

    result = sync_readme(readme, src)
    assert result.success

    updated = readme.read_text()
    assert "sha256=" not in updated


# ─── sync_readme_recursive ───────────────────────────────────────────────────

def test_sync_recursive_single_readme(tmp_path):
    """Without includes, recursive sync behaves like normal sync."""
    readme = tmp_path / "README.md"
    src = tmp_path / "sandbox"
    src.mkdir()

    readme.write_text(textwrap.dedent("""\
        ```python markpact:file path=main.py
        print("old")
        ```
    """))
    (src / "main.py").write_text('print("new")\n')

    results = sync_readme_recursive(readme, src)
    assert len(results) == 1
    assert results[0].success
    assert results[0].updated == 1
    assert 'print("new")' in readme.read_text()


def test_sync_recursive_with_sub_readme(tmp_path):
    """Recursive sync processes both root and included sub-README."""
    src = tmp_path / "sandbox"
    src.mkdir()
    (src / "deploy").mkdir()

    # Sub-README
    sub_readme = tmp_path / "deploy" / "README.md"
    sub_readme.parent.mkdir()
    sub_readme.write_text(textwrap.dedent("""\
        ```yaml markpact:file path=deploy/config.yml
        old_config: true
        ```
    """))
    (src / "deploy" / "config.yml").write_text("new_config: true\n")

    # Root README with include
    readme = tmp_path / "README.md"
    readme.write_text(textwrap.dedent("""\
        ```python markpact:file path=main.py
        print("old")
        ```

        <!-- markpact:include path=deploy/README.md -->
    """))
    (src / "main.py").write_text('print("new")\n')

    results = sync_readme_recursive(readme, src)
    assert len(results) == 2

    total_updated = sum(r.updated for r in results)
    assert total_updated == 2

    assert 'print("new")' in readme.read_text()
    assert "new_config: true" in sub_readme.read_text()


def test_sync_recursive_dry_run(tmp_path):
    """Recursive sync with dry_run doesn't modify any files."""
    src = tmp_path / "sandbox"
    src.mkdir()

    sub = tmp_path / "sub.md"
    sub.write_text('```yaml markpact:file path=s.yml\nold\n```\n')
    (src / "s.yml").write_text("new\n")

    readme = tmp_path / "README.md"
    original = '```yaml markpact:file path=r.yml\nold\n```\n\n<!-- markpact:include path=sub.md -->\n'
    readme.write_text(original)
    (src / "r.yml").write_text("new\n")

    results = sync_readme_recursive(readme, src, dry_run=True)
    assert len(results) == 2
    total_updated = sum(r.updated for r in results)
    assert total_updated == 2

    # Files should NOT have changed
    assert readme.read_text() == original
    assert "old" in sub.read_text()


def test_sync_recursive_circular(tmp_path):
    """Circular includes don't cause infinite loops in recursive sync."""
    src = tmp_path / "sandbox"
    src.mkdir()

    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text('```yaml markpact:file path=a.yml\nold_a\n```\n\n<!-- markpact:include path=b.md -->\n')
    b.write_text('```yaml markpact:file path=b.yml\nold_b\n```\n\n<!-- markpact:include path=a.md -->\n')
    (src / "a.yml").write_text("new_a\n")
    (src / "b.yml").write_text("new_b\n")

    results = sync_readme_recursive(a, src)
    assert len(results) == 2  # each file synced once, no infinite loop


def test_sync_recursive_with_hash(tmp_path):
    """Recursive sync + hash_blocks combined."""
    src = tmp_path / "sandbox"
    src.mkdir()

    sub = tmp_path / "sub.md"
    sub.write_text('```yaml markpact:file path=cfg.yml\nold_cfg\n```\n')
    (src / "cfg.yml").write_text("new_cfg\n")

    readme = tmp_path / "README.md"
    readme.write_text(
        '```python markpact:file path=main.py\nprint("old")\n```\n\n'
        '<!-- markpact:include path=sub.md -->\n'
    )
    (src / "main.py").write_text('print("new")\n')

    results = sync_readme_recursive(readme, src, hash_blocks=True)
    assert len(results) == 2
    assert sum(r.updated for r in results) == 2

    # Both files should have sha256= embedded
    assert "sha256=" in readme.read_text()
    assert "sha256=" in sub.read_text()


# ─── CLI integration smoke test ──────────────────────────────────────────────

def test_sync_cli_recursive_hash(tmp_path):
    """End-to-end CLI test: markpact sync --recursive --hash."""
    from markpact.cli import handle_sync_cli

    src = tmp_path / "sandbox"
    src.mkdir()

    sub_dir = tmp_path / "deploy"
    sub_dir.mkdir()
    sub_readme = sub_dir / "README.md"
    sub_readme.write_text('```yaml markpact:file path=deploy/conf.yml\nold\n```\n')
    (src / "deploy").mkdir()
    (src / "deploy" / "conf.yml").write_text("new\n")

    readme = tmp_path / "README.md"
    readme.write_text(
        '```python markpact:file path=app.py\nold\n```\n\n'
        '<!-- markpact:include path=deploy/README.md -->\n'
    )
    (src / "app.py").write_text("new\n")

    rc = handle_sync_cli([
        str(readme), "--source", str(src),
        "--recursive", "--hash", "-q",
    ])
    assert rc == 0
    assert "sha256=" in readme.read_text()
    assert "new" in readme.read_text()
    assert "sha256=" in sub_readme.read_text()
    assert "new" in sub_readme.read_text()


def test_sync_cli_check_recursive_detects_drift(tmp_path):
    """markpact sync --check --recursive returns 1 when sub-README is out of sync."""
    from markpact.cli import handle_sync_cli

    src = tmp_path / "sandbox"
    src.mkdir()

    sub = tmp_path / "sub.md"
    sub.write_text('```yaml markpact:file path=s.yml\nold\n```\n')
    (src / "s.yml").write_text("new\n")

    readme = tmp_path / "README.md"
    readme.write_text(
        '```yaml markpact:file path=r.yml\nsame\n```\n\n'
        '<!-- markpact:include path=sub.md -->\n'
    )
    (src / "r.yml").write_text("same\n")

    rc = handle_sync_cli([
        str(readme), "--source", str(src),
        "--recursive", "--check", "-q",
    ])
    assert rc == 1  # sub.md has drift


# ─── _detect_lang ────────────────────────────────────────────────────────────

def test_detect_lang_python():
    assert _detect_lang("app.py") == "python"


def test_detect_lang_yaml():
    assert _detect_lang("config.yml") == "yaml"
    assert _detect_lang("deploy.yaml") == "yaml"


def test_detect_lang_bash():
    assert _detect_lang("run.sh") == "bash"


def test_detect_lang_env():
    assert _detect_lang(".env") == "bash"
    assert _detect_lang(".env.prod") == "bash"
    assert _detect_lang(".env.staging") == "bash"


def test_detect_lang_dockerfile():
    assert _detect_lang("Dockerfile") == "dockerfile"


def test_detect_lang_makefile():
    assert _detect_lang("Makefile") == "makefile"


def test_detect_lang_container():
    assert _detect_lang("traefik.container") == "ini"
    assert _detect_lang("web.service") == "ini"


def test_detect_lang_unknown():
    assert _detect_lang("data.xyz") == ""


def test_detect_lang_nested_path():
    assert _detect_lang("deploy/quadlet/traefik.container") == "ini"
    assert _detect_lang("src/main.py") == "python"


# ─── add_untracked_blocks ────────────────────────────────────────────────────

def test_add_untracked_blocks_basic(tmp_path):
    """add_untracked_blocks appends new markpact:file blocks."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("print('hello')\n")
    (src / "config.yaml").write_text("key: value\n")

    readme = tmp_path / "README.md"
    readme.write_text("# Project\n\nSome text.\n")

    added = add_untracked_blocks(readme, src, ["app.py", "config.yaml"])
    assert added == 2

    content = readme.read_text()
    assert "markpact:file path=app.py" in content
    assert "markpact:file path=config.yaml" in content
    assert "print('hello')" in content
    assert "key: value" in content


def test_add_untracked_blocks_detects_lang(tmp_path):
    """add_untracked_blocks uses correct language identifier."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "run.sh").write_text("echo hi\n")

    readme = tmp_path / "README.md"
    readme.write_text("# Project\n")

    add_untracked_blocks(readme, src, ["run.sh"])
    content = readme.read_text()
    assert "```bash markpact:file path=run.sh" in content


def test_add_untracked_blocks_skips_already_tracked(tmp_path):
    """add_untracked_blocks skips files that already have blocks."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("new content\n")

    readme = tmp_path / "README.md"
    readme.write_text(
        "# Project\n\n"
        "```python markpact:file path=app.py\nold content\n```\n"
    )

    added = add_untracked_blocks(readme, src, ["app.py"])
    assert added == 0
    # Original content should be unchanged
    assert "old content" in readme.read_text()


def test_add_untracked_blocks_skips_missing_files(tmp_path):
    """add_untracked_blocks skips files that don't exist in source."""
    src = tmp_path / "src"
    src.mkdir()

    readme = tmp_path / "README.md"
    readme.write_text("# Project\n")

    added = add_untracked_blocks(readme, src, ["nonexistent.py"])
    assert added == 0


def test_add_untracked_blocks_dry_run(tmp_path):
    """add_untracked_blocks dry_run doesn't modify the file."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("print('hello')\n")

    readme = tmp_path / "README.md"
    original = "# Project\n"
    readme.write_text(original)

    added = add_untracked_blocks(readme, src, ["app.py"], dry_run=True)
    assert added == 1
    assert readme.read_text() == original  # File unchanged


def test_add_untracked_blocks_creates_backup(tmp_path):
    """add_untracked_blocks creates a backup before writing."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("print('hello')\n")

    readme = tmp_path / "README.md"
    readme.write_text("# Project\n")

    add_untracked_blocks(readme, src, ["app.py"])

    bak_dir = tmp_path / BACKUP_DIR_NAME
    assert bak_dir.exists()
    backups = list(bak_dir.glob(f"{BACKUP_PREFIX}*"))
    assert len(backups) >= 1


def test_add_untracked_blocks_empty_paths(tmp_path):
    """add_untracked_blocks returns 0 for empty paths list."""
    src = tmp_path / "src"
    src.mkdir()

    readme = tmp_path / "README.md"
    readme.write_text("# Project\n")

    added = add_untracked_blocks(readme, src, [])
    assert added == 0


# ─── CLI --add flag ──────────────────────────────────────────────────────────

def test_sync_cli_add_all_untracked(tmp_path):
    """markpact sync --add adds all untracked files."""
    from markpact.cli import handle_sync_cli

    src = tmp_path / "sandbox"
    src.mkdir()
    (src / "app.py").write_text("print('hello')\n")
    (src / "config.yaml").write_text("key: value\n")

    readme = tmp_path / "README.md"
    readme.write_text("# Project\n")

    rc = handle_sync_cli([str(readme), "--source", str(src), "--add", "-q"])
    assert rc == 0

    content = readme.read_text()
    assert "markpact:file path=app.py" in content
    assert "markpact:file path=config.yaml" in content


def test_sync_cli_add_specific_files(tmp_path):
    """markpact sync --add file1 file2 adds only specified files."""
    from markpact.cli import handle_sync_cli

    src = tmp_path / "sandbox"
    src.mkdir()
    (src / "app.py").write_text("print('hello')\n")
    (src / "config.yaml").write_text("key: value\n")
    (src / "secret.env").write_text("KEY=val\n")

    readme = tmp_path / "README.md"
    readme.write_text("# Project\n")

    rc = handle_sync_cli([
        str(readme), "--source", str(src),
        "--add", "app.py", "config.yaml", "-q",
    ])
    assert rc == 0

    content = readme.read_text()
    assert "markpact:file path=app.py" in content
    assert "markpact:file path=config.yaml" in content
    assert "secret.env" not in content


def test_sync_cli_add_dry_run(tmp_path):
    """markpact sync --add --dry-run doesn't modify README."""
    from markpact.cli import handle_sync_cli

    src = tmp_path / "sandbox"
    src.mkdir()
    (src / "app.py").write_text("print('hello')\n")

    readme = tmp_path / "README.md"
    original = "# Project\n"
    readme.write_text(original)

    rc = handle_sync_cli([
        str(readme), "--source", str(src),
        "--add", "--dry-run", "-q",
    ])
    assert rc == 0
    assert readme.read_text() == original


def test_sync_cli_add_then_sync(tmp_path):
    """After --add, subsequent sync should see the new blocks."""
    from markpact.cli import handle_sync_cli

    src = tmp_path / "sandbox"
    src.mkdir()
    (src / "app.py").write_text("version 1\n")

    readme = tmp_path / "README.md"
    readme.write_text("# Project\n")

    # Add the file
    rc = handle_sync_cli([str(readme), "--source", str(src), "--add", "-q"])
    assert rc == 0
    assert "version 1" in readme.read_text()

    # Modify source
    (src / "app.py").write_text("version 2\n")

    # Sync should update the block
    rc = handle_sync_cli([str(readme), "--source", str(src), "-q"])
    assert rc == 0
    assert "version 2" in readme.read_text()
