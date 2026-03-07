"""Tests for markpact syncer"""

import textwrap
from pathlib import Path

from markpact.syncer import (
    list_tracked_paths,
    find_untracked_files,
    sync_readme,
    diff_block,
    create_backup,
    list_backups,
    restore_backup,
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
