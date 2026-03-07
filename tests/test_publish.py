"""Tests for markpact.publish package — models, helpers, version, main dispatch."""

import tempfile
from pathlib import Path

import pytest

from markpact.publish.models import PublishConfig, PublishResult
from markpact.publish.version import bump_version, extract_version_from_readme, update_version_in_readme
from markpact.publish.main import parse_publish_block, publish
from markpact.publish.helpers import (
    _slugify,
    _first_heading,
    _first_paragraph,
    _format_subprocess_failure,
    _check_file_type,
    _analyze_blocks_for_types,
    _is_web_service,
    _detect_registry,
    _build_package_name,
    infer_publish_config,
    ensure_publish_block_in_readme,
)


# ── PublishConfig dataclass ──────────────────────────────────────────────────

class TestPublishConfig:
    def test_defaults(self):
        c = PublishConfig(registry="pypi", name="pkg", version="1.0.0")
        assert c.description == ""
        assert c.author == ""
        assert c.license == "MIT"
        assert c.keywords == []

    def test_keywords_none_defaults_to_list(self):
        c = PublishConfig(registry="pypi", name="pkg", version="1.0.0", keywords=None)
        assert c.keywords == []

    def test_keywords_preserved(self):
        c = PublishConfig(registry="npm", name="pkg", version="0.1.0", keywords=["web", "api"])
        assert c.keywords == ["web", "api"]


# ── PublishResult dataclass ──────────────────────────────────────────────────

class TestPublishResult:
    def test_success_result(self):
        r = PublishResult(success=True, registry="pypi", message="ok", version="1.0.0", url="https://pypi.org/p/x")
        assert r.success
        assert r.url == "https://pypi.org/p/x"

    def test_failure_result(self):
        r = PublishResult(success=False, registry="npm", message="auth failed", version="0.1.0")
        assert not r.success
        assert r.url == ""


# ── Version management ───────────────────────────────────────────────────────

class TestBumpVersion:
    def test_patch(self):
        assert bump_version("1.2.3", "patch") == "1.2.4"

    def test_minor(self):
        assert bump_version("1.2.3", "minor") == "1.3.0"

    def test_major(self):
        assert bump_version("1.2.3", "major") == "2.0.0"

    def test_v_prefix(self):
        assert bump_version("v1.2.3", "patch") == "1.2.4"

    def test_default_is_patch(self):
        assert bump_version("0.0.1") == "0.0.2"

    def test_invalid_version_resets(self):
        assert bump_version("bad", "patch") == "0.0.1"

    def test_prerelease_stripped(self):
        # "1.2.3-beta.1" splits to ["1", "2", "3-beta", "1"] → 4 parts → reset
        # but int("3-beta") would fail, so parts[2].split("-")[0] = "3"
        # Actually splits to 4 parts (due to ".1" suffix), len!=3, resets to 0.0.0
        assert bump_version("1.2.3-beta.1", "patch") == "0.0.1"

    def test_zero_version(self):
        assert bump_version("0.0.0", "patch") == "0.0.1"
        assert bump_version("0.0.0", "minor") == "0.1.0"
        assert bump_version("0.0.0", "major") == "1.0.0"


class TestExtractVersionFromReadme:
    def test_from_publish_block(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "# My Project\n\n"
            "```toml markpact:publish\n"
            "version = 2.3.4\n"
            "```\n"
        )
        assert extract_version_from_readme(readme) == "2.3.4"

    def test_from_pyproject_style(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text('# X\nversion = "5.6.7"\n')
        assert extract_version_from_readme(readme) == "5.6.7"

    def test_fallback_default(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# No version here\n")
        assert extract_version_from_readme(readme) == "0.1.0"

    def test_colon_syntax(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "```toml markpact:publish\n"
            "version: 9.8.7\n"
            "```\n"
        )
        assert extract_version_from_readme(readme) == "9.8.7"


class TestUpdateVersionInReadme:
    def test_updates_version(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            '# Project\nversion = "1.0.0"\n'
        )
        assert update_version_in_readme(readme, "1.0.1") is True
        assert "1.0.1" in readme.read_text()
        assert "1.0.0" not in readme.read_text()

    def test_no_version_returns_false(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# No version\n")
        assert update_version_in_readme(readme, "1.0.0") is False


# ── parse_publish_block ──────────────────────────────────────────────────────

class TestParsePublishBlock:
    def test_basic_equals_syntax(self):
        body = "registry = npm\nname = my-pkg\nversion = 2.0.0\nauthor = Tom"
        cfg = parse_publish_block(body)
        assert cfg.registry == "npm"
        assert cfg.name == "my-pkg"
        assert cfg.version == "2.0.0"
        assert cfg.author == "Tom"

    def test_colon_syntax(self):
        body = "registry: docker\nname: my-img\nversion: 1.0.0"
        cfg = parse_publish_block(body)
        assert cfg.registry == "docker"
        assert cfg.name == "my-img"

    def test_ignores_comments(self):
        body = "# comment\nregistry = pypi\n# another comment\nname = pkg"
        cfg = parse_publish_block(body)
        assert cfg.registry == "pypi"
        assert cfg.name == "pkg"

    def test_keywords_split(self):
        body = "keywords = web, api, python"
        cfg = parse_publish_block(body)
        assert cfg.keywords == ["web", "api", "python"]

    def test_meta_line(self):
        body = "version = 3.0.0"
        cfg = parse_publish_block(body, meta="registry=npm")
        assert cfg.registry == "npm"
        assert cfg.version == "3.0.0"

    def test_defaults(self):
        cfg = parse_publish_block("")
        assert cfg.registry == "pypi"
        assert cfg.name == "my-package"
        assert cfg.version == "0.1.0"
        assert cfg.license == "MIT"

    def test_quoted_values_stripped(self):
        body = 'name = "my-quoted-pkg"\nversion = \'1.2.3\''
        cfg = parse_publish_block(body)
        assert cfg.name == "my-quoted-pkg"
        assert cfg.version == "1.2.3"

    def test_unknown_keys_ignored(self):
        body = "registry = pypi\nfoo = bar\nname = x"
        cfg = parse_publish_block(body)
        assert cfg.registry == "pypi"
        assert cfg.name == "x"


# ── publish dispatch ─────────────────────────────────────────────────────────

class TestPublishDispatch:
    def test_unknown_registry(self, tmp_path):
        from markpact.sandbox import Sandbox
        sandbox = Sandbox(tmp_path)
        cfg = PublishConfig(registry="foobar", name="x", version="1.0.0")
        result = publish(cfg, sandbox, verbose=False)
        assert not result.success
        assert "Unknown registry" in result.message

    def test_bump_before_publish(self, tmp_path):
        from markpact.sandbox import Sandbox
        sandbox = Sandbox(tmp_path)
        cfg = PublishConfig(registry="unknown_test", name="x", version="1.0.0")
        result = publish(cfg, sandbox, bump="minor", verbose=False)
        assert cfg.version == "1.1.0"
        assert result.version == "1.1.0"


# ── Helpers ──────────────────────────────────────────────────────────────────

class TestSlugify:
    def test_basic(self):
        assert _slugify("My Cool Project") == "my-cool-project"

    def test_special_chars(self):
        assert _slugify("Project: v2.0!") == "project-v2-0"

    def test_empty(self):
        assert _slugify("") == "my-project"

    def test_leading_trailing(self):
        assert _slugify("  --hello-- ") == "hello"


class TestFirstHeading:
    def test_found(self):
        assert _first_heading("# Hello World\nstuff") == "Hello World"

    def test_not_found(self):
        assert _first_heading("no heading here") == "My Project"

    def test_second_heading_ignored(self):
        assert _first_heading("## Sub\n# Main") == "Main"


class TestFirstParagraph:
    def test_found(self):
        md = "# Title\n\nThis is the first paragraph.\n\n## Next"
        assert _first_paragraph(md) == "This is the first paragraph."

    def test_multiline(self):
        md = "# Title\n\nLine one\nLine two\n\n## Next"
        assert _first_paragraph(md) == "Line one Line two"

    def test_no_paragraph(self):
        md = "# Title\n## Sub"
        assert _first_paragraph(md) == ""


class TestFormatSubprocessFailure:
    def test_stderr(self):
        class R:
            stderr = "some error"
            stdout = ""
            returncode = 1
        assert _format_subprocess_failure(R()) == "some error"

    def test_empty(self):
        class R:
            stderr = ""
            stdout = ""
            returncode = 1
        assert "exit code 1" in _format_subprocess_failure(R())

    def test_truncation(self):
        class R:
            stderr = "x" * 500
            stdout = ""
            returncode = 1
        assert len(_format_subprocess_failure(R())) == 400


class TestCheckFileType:
    def test_python(self):
        f = _check_file_type("app/__init__.py")
        assert f["python_pkg"] is True

    def test_js(self):
        f = _check_file_type("index.ts")
        assert f["js"] is True

    def test_dockerfile(self):
        f = _check_file_type("Dockerfile")
        assert f["dockerfile"] is True


class TestIsWebService:
    def test_uvicorn(self):
        assert _is_web_service("uvicorn app:app") is True

    def test_flask(self):
        assert _is_web_service("flask run --port 8000") is True

    def test_not_web(self):
        assert _is_web_service("python script.py") is False

    def test_none(self):
        assert _is_web_service(None) is False


class TestDetectRegistry:
    def test_npm_from_js(self):
        assert _detect_registry({"has_js": True, "has_package_json": False,
                                  "has_dockerfile": False, "has_pyproject": False,
                                  "has_python_pkg": False}, None) == "npm"

    def test_docker_from_web(self):
        assert _detect_registry({"has_js": False, "has_package_json": False,
                                  "has_dockerfile": False, "has_pyproject": False,
                                  "has_python_pkg": False}, "uvicorn app:app") == "docker"

    def test_pypi_from_pyproject(self):
        assert _detect_registry({"has_js": False, "has_package_json": False,
                                  "has_dockerfile": False, "has_pyproject": True,
                                  "has_python_pkg": False}, None) == "pypi"


class TestBuildPackageName:
    def test_pypi_prefix(self):
        assert _build_package_name("myapp", "pypi") == "markpact-myapp"

    def test_already_prefixed(self):
        assert _build_package_name("markpact-myapp", "pypi") == "markpact-myapp"


class TestInferPublishConfig:
    def test_basic_inference(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Todo API\n\nA simple todo API.\n")
        cfg = infer_publish_config(readme, readme.read_text(), [], None)
        assert cfg.name == "markpact-todo-api"
        assert cfg.description == "A simple todo API."
        assert cfg.version == "0.1.0"


class TestEnsurePublishBlock:
    def test_inserts_block(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Project\n\nHello world.\n")
        cfg = PublishConfig(registry="pypi", name="pkg", version="1.0.0")
        ensure_publish_block_in_readme(readme, cfg)
        text = readme.read_text()
        assert "markpact:publish" in text
        assert "registry = pypi" in text

    def test_no_duplicate(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Project\n\n```toml markpact:publish\nregistry = npm\n```\n")
        cfg = PublishConfig(registry="pypi", name="pkg", version="1.0.0")
        ensure_publish_block_in_readme(readme, cfg)
        text = readme.read_text()
        assert text.count("markpact:publish") == 1

    def test_inserts_before_deps(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Project\n\n```text markpact:deps python\nflask\n```\n")
        cfg = PublishConfig(registry="pypi", name="pkg", version="1.0.0")
        ensure_publish_block_in_readme(readme, cfg)
        text = readme.read_text()
        pub_pos = text.index("markpact:publish")
        deps_pos = text.index("markpact:deps")
        assert pub_pos < deps_pos
