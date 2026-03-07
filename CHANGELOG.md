## [0.1.19] - 2026-02-18

### Summary

fix(docs): multi-language support with 3 supporting modules

### Core

- update src/markpact/__init__.py
- update src/markpact/auto_fix.py
- update src/markpact/docker_runner.py
- update src/markpact/sandbox.py


## [0.1.18] - 2026-02-18

### Summary

feat(goal): multi-language support with 5 supporting modules

### Core

- update src/markpact/__init__.py
- update src/markpact/parser.py

### Build

- update pyproject.toml

### Config

- config: update goal.yaml


## [0.1.17] - 2026-02-18

### Summary

refactor(goal): deep code analysis engine with 7 supporting modules

### Build

- update pyproject.toml

### Config

- config: update goal.yaml

### Other

- update project.functions.toon
- update project.toon


# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Examples Test Script** (`scripts/test_examples.sh`):
  - Automated testing of all 18 examples
  - Supports dry-run and full-run modes
  - Categorized tests: Python, Node.js, Other, Publish, Converter
  - Summary with pass/fail/skip counts
- **Notebook Converter** (`notebook_converter.py`):
  - Convert Jupyter (.ipynb), R Markdown (.Rmd), Quarto (.qmd), Databricks (.dib), Zeppelin (.zpln) to markpact
  - `--from-notebook FILE` flag for conversion
  - `--list-notebook-formats` to list supported formats
  - Automatic dependency extraction from imports
  - Intelligent file grouping (app.py, models.py)
  - Framework-aware run command suggestions
- **Dynamic License Mapping** (`publisher.py`):
  - `get_license_classifier()` maps license names to PyPI classifiers
  - Supports: MIT, Apache-2.0, GPL-3.0, BSD-3-Clause, ISC, LGPL-3.0, MPL-2.0, Unlicense
- **Enhanced Auto-Fix** (`auto_fix.py`):
  - `run_with_auto_fix_llm()` with LLM integration for complex error fixes
  - Auto-detection of: port_in_use, missing_module, syntax_error, import_error
  - Automatic dependency addition for ModuleNotFoundError
  - `--auto-fix-llm` flag for LLM-powered error fixes
- **CLI Entry Point for PyPI packages**:
  - `[project.scripts]` section in generated `pyproject.toml`
  - Full README as project description on PyPI
- **New Examples**:
  - `php-cli/` – CLI application in PHP
  - `react-typescript-spa/` – React + TypeScript SPA with Vite
  - `typescript-node-api/` – REST API in TypeScript (Node)
- **LLM Contract Generation** (`generator.py`):
  - Generate markpact READMEs from text prompts: `markpact -p "REST API for tasks"`
  - Support for 16 example prompts: `markpact --list-examples`
  - Use examples directly: `markpact -e todo-api -o project/README.md`
  - One-liner run: `markpact -p "..." -o project/README.md --run`
- **LLM Configuration** (`config.py`):
  - Persistent config in `~/.markpact/.env`
  - Provider presets: `markpact config --provider openrouter`
  - Support for: Ollama, OpenRouter, OpenAI, Anthropic, Groq
  - Easy setup: `markpact config --api-key sk-xxx`
- **Docker Sandbox** (`docker_runner.py`):
  - Run in isolated Docker container: `markpact README.md --docker`
  - Auto-generate Dockerfile from deps and run command
- **Auto-fix Runtime Errors** (`auto_fix.py`):
  - Automatic port switching when "address in use"
  - Updates README with new port on fix
  - Enabled by default, disable with `--no-auto-fix`
- **HTTP Testing** (`tester.py`):
  - Define tests in `markpact:test http` blocks
  - Format: `GET /path EXPECT 200`, `POST /path BODY {...} EXPECT 201`
  - Run with `--test` or `--test-only` flags
  - Auto-starts service, runs tests, shows results summary
- **Multi-Registry Publishing** (`publisher.py`):
  - Publish to PyPI, npm, Docker Hub, GitHub Packages, GHCR
  - Define config in `markpact:publish` blocks
  - Auto-bump versioning: `--bump patch|minor|major`
  - Override registry: `--registry docker`
  - Generates pyproject.toml, package.json, Dockerfile as needed
- Python package structure (`src/markpact/`)
- CLI entry point `markpact` with full options
- Markdown → Markpact converter (`--convert`, `--convert-only`, `--auto`)
- Auto-detection of non-markpact files with conversion suggestion
- `--save-converted` flag to save converted output
- Comprehensive test suite (parser, sandbox, runner, CLI, converter)
- Documentation:
  - `docs/README.md` – Quick start and CLI reference
  - `docs/generator.md` – LLM generation guide
  - `docs/contract.md` – markpact:* specification
  - `docs/ci-cd.md` – GitHub Actions, GitLab CI, Docker
  - `docs/llm.md` – LLM integration guide
  - `docs/publishing.md` – PyPI publishing guide
- Examples:
  - `examples/fastapi-todo/` – REST API with SQLite
  - `examples/flask-blog/` – Web app with templates
  - `examples/cli-tool/` – CLI application
  - `examples/streamlit-dashboard/` – Data dashboard
  - `examples/kivy-mobile/` – Mobile app
  - `examples/electron-desktop/` – Desktop app
  - `examples/markdown-converter/` – Conversion demo
- Makefile targets: `test-cov`, `run-cli`, `convert`, `publish-prod`

### Changed
- Makefile `publish` now uses `~/.pypirc` for credentials (no prompt)
- Makefile `extract` outputs to `markpact.py` instead of `markpact_bootstrap.py`
- Improved `clean` target removes all build artifacts
- Default LLM model: `ollama/qwen2.5-coder:14b`

## [0.1.28] - 2026-03-07

### Test
- Update tests/test_include.py
- Update tests/test_syncer.py
- Update tests/test_template.py

## [0.1.27] - 2026-03-06

### Docs
- Update project/README.md
- Update project/context.md

### Other
- Update project/analysis.toon
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/dashboard.html
- Update project/evolution.toon
- Update project/flow.mmd
- Update project/flow.png
- Update project/flow.toon
- ... and 3 more files

## [0.1.26] - 2026-03-05

## [0.1.25] - 2026-03-05

## [0.1.24] - 2026-03-05

### Docs
- Update project/README.md
- Update project/context.md

### Other
- Update demos/demo_live_markpact.py
- Update project/analysis.toon
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/dashboard.html
- Update project/evolution.toon
- Update project/flow.mmd
- Update project/flow.png
- ... and 4 more files

## [0.1.23] - 2026-03-05

## [0.1.22] - 2026-03-05

### Docs
- Update project/README.md
- Update project/context.md

### Other
- Update project/analysis.toon
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/dashboard.html
- Update project/evolution.toon
- Update project/flow.mmd
- Update project/flow.png
- Update project/flow.toon
- ... and 3 more files

## [0.1.21] - 2026-03-05

### Docs
- Update project/context.md

### Other
- Update project/analysis.toon
- Update project/calls.mmd
- Update project/calls.png
- Update project/dashboard.html
- Update project/flow.mmd
- Update project/flow.png
- Update project/flow.toon
- Update project/map.toon
- Update project/project.toon
- Update project/project.yaml

## [0.1.20] - 2026-03-05

### Docs
- Update project/README.md
- Update project/context.md

### Other
- Update project.functions.toon
- Update project.sh
- Update project/analysis.toon
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/dashboard.html
- Update project/evolution.toon
- Update project/flow.mmd
- ... and 6 more files

## [0.1.0] - 2026-01-14

### Added
- Initial release
- `markpact:bootstrap` – embedded Python runtime in README
- `markpact:file` – file creation in sandbox
- `markpact:deps python` – Python dependency management with venv
- `markpact:run` – command execution in sandbox
- Environment variables:
  - `MARKPACT_SANDBOX` – custom sandbox directory
  - `MARKPACT_NO_VENV` – disable venv creation
  - `MARKPACT_PORT` – configurable port for examples
- Safe `sed` extraction command (handles ``` in regex)
- FastAPI example application

### Fixed
- Bootstrap extraction with `sed` no longer breaks on ``` inside code

[Unreleased]: https://github.com/wronai/markpact/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/wronai/markpact/releases/tag/v0.1.0
