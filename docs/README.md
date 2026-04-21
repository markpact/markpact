<!-- code2docs:start --># markpact

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-417-green)
> **417** functions | **59** classes | **52** files | CC̄ = 4.5

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/wronai/markpact](https://github.com/wronai/markpact)

## Installation

### From PyPI

```bash
pip install markpact
```

### From Source

```bash
git clone https://github.com/wronai/markpact
cd markpact
pip install -e .
```

### Optional Extras

```bash
pip install markpact[llm]    # LLM integration (litellm)
pip install markpact[ops]    # ops features
pip install markpact[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
markpact ./my-project

# Only regenerate README
markpact ./my-project --readme-only

# Preview what would be generated (no file writes)
markpact ./my-project --dry-run

# Check documentation health
markpact check ./my-project

# Sync — regenerate only changed modules
markpact sync ./my-project
```

### Python API

```python
from markpact import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```




## Architecture

```
markpact/
├── project
            ├── run
        ├── sandbox
        ├── tester
            ├── helpers
        ├── converter
            ├── app
        ├── template
        ├── config
            ├── run_cmd
        ├── cli/
            ├── pack_cmd
            ├── sync_cmd
            ├── config_cmd
            ├── convert_cmd
            ├── exceptions
        ├── notebook_converter
            ├── cli
        ├── runtime/
    ├── markpact/
            ├── plugins
        ├── packer
            ├── executors
            ├── ssh_manager
        ├── publisher
            ├── version
        ├── docker_runner
            ├── parser
        ├── publish/
            ├── helpers
            ├── npm
        ├── runner
            ├── pypi
            ├── main
            ├── github
    ├── test_examples
            ├── models
    ├── sync_version
            ├── docker_pub
        ├── auto_fix
        ├── parser
            ├── core
        ├── syncer
            ├── core_v3
            ├── steps
            ├── core_v2
            ├── state
            ├── models
            ├── llm_config
        ├── generator
            ├── publish_cmd
    ├── demo_live_markpact
```

## API Overview

### Classes

- **`Sandbox`** — Manages sandbox directory for markpact execution
- **`TestResult`** — Result of a single test
- **`TestSuite`** — Collection of test results
- **`ConvertedBlock`** — A converted markpact block.
- **`ConversionResult`** — Result of converting a Markdown file.
- **`MarkpactError`** — Base exception for all markpact errors.
- **`ParseError`** — Error parsing markpact file.
- **`ExecutionError`** — Error executing a step.
- **`PluginError`** — Error with plugin loading or execution.
- **`ValidationError`** — Error validating configuration or steps.
- **`TimeoutError`** — Step execution timed out.
- **`ConnectionError`** — Error connecting to remote host.
- **`RollbackError`** — Error during rollback.
- **`NotebookCell`** — Represents a cell in a notebook.
- **`Notebook`** — Represents a parsed notebook.
- **`Plugin`** — Base class for plugins.
- **`PluginLoader`** — Loads plugins from various sources.
- **`BrowserReloadPlugin`** — Plugin to reload browser via CDP (Chrome DevTools Protocol).
- **`PackResult`** — Result of packing a directory.
- **`Executor`** — Base class for action executors.
- **`ShellExecutor`** — Execute shell commands locally or via SSH with persistent sessions.
- **`SSHCmdExecutor`** — Alias for shell executor with explicit SSH.
- **`RsyncExecutor`** — Execute rsync operations.
- **`ScpExecutor`** — Execute SCP copy operations.
- **`DockerExecutor`** — Execute Docker Compose operations.
- **`HttpExecutor`** — Execute HTTP health checks.
- **`PluginExecutor`** — Execute custom plugin actions.
- **`PythonExecutor`** — Execute Python code blocks.
- **`BashExecutor`** — Execute Bash/shell scripts.
- **`ExecutorRegistry`** — Registry of available executors.
- **`SSHSessionManager`** — Manages persistent SSH sessions for performance.
- **`BlockType`** — Types of markpact blocks.
- **`Block`** — A parsed markpact block.
- **`MarkpactParser`** — Parser for markpact markdown files.
- **`PublishConfig`** — Configuration for publishing
- **`PublishResult`** — Result of a publish operation
- **`Block`** — —
- **`RuntimeConfig`** — Configuration for the runtime.
- **`Runtime`** — Main runtime for executing markpact markdown files.
- **`SyncResult`** — Result of a sync operation.
- **`RuntimeConfigV3`** — Configuration for RuntimeV3.
- **`StepExecutionRecord`** — Record of executed step for rollback stack.
- **`FactsGatherer`** — Gathers current state facts from target host.
- **`RuntimeV3`** — Markpact Runtime v3: State Reconciliation Engine
- **`StepStatus`** — Status of step execution.
- **`Step`** — A deployment step.
- **`StepResult`** — Result of step execution.
- **`RuntimeConfig`** — Configuration for the runtime.
- **`RuntimeV2`** — Production-grade runtime for executing markpact deployments.
- **`StateManager`** — Manages deployment state for idempotency.
- **`ConditionChecker`** — Check step conditions (when/skip_if).
- **`Step`** — Pydantic-validated deployment step.
- **`DeploymentConfig`** — Deployment configuration with validation.
- **`DeployState`** — Deployment state for idempotency tracking.
- **`StepResult`** — Result of step execution with structured logging.
- **`ExecutionSummary`** — Summary of full deployment execution.
- **`GeneratorConfig`** — Configuration for LLM generator
- **`StepRecord`** — —
- **`LiveSession`** — —

### Functions

- `find_free_port(start_port, max_attempts)` — Find a free port starting from start_port.
- `wait_for_service(url, timeout, interval)` — Wait for a service to become available.
- `http_request(method, url, data, headers)` — Make an HTTP request and return (status_code, response_body).
- `run_http_test(test_spec, base_url)` — Run a single HTTP test from spec.
- `run_tests_from_block(test_body, base_url)` — Run all tests defined in a test block.
- `run_service_with_tests(run_command, test_body, sandbox, port)` — Start a service, run tests, and return results.
- `run_shell_tests(test_body, sandbox, verbose)` — Run shell command tests.
- `detect_block_type(lang, body)` — Detect the markpact block type based on language and content.
- `suggest_filename(lang, body, index)` — Suggest a filename for a file block.
- `convert_markdown_to_markpact(text, verbose)` — Convert regular Markdown to markpact format.
- `print_conversion_report(result)` — Print a report of the conversion.
- `root()` — —
- `load_secrets(project_dir)` — Load secrets from the secrets file.
- `resolve_template(body)` — Resolve template placeholders in a block body.
- `has_template_placeholders(body)` — Check if body contains any template placeholders.
- `get_env_path()` — Get the .env file path (can be overridden by MARKPACT_ENV_PATH)
- `ensure_config_dir()` — Ensure config directory exists
- `load_env()` — Load configuration from .env file
- `save_env(config)` — Save configuration to .env file
- `init_env(force)` — Initialize .env file with defaults if it doesn't exist.
- `set_config(key, value)` — Set a single configuration value
- `set_model(model)` — Set the LLM model
- `set_api_key(api_key)` — Set the API key
- `set_api_base(api_base)` — Set the API base URL
- `apply_preset(provider, api_key)` — Apply a provider preset configuration
- `show_config()` — Show current configuration as formatted string
- `list_providers()` — List available provider presets
- `main(argv)` — Main entry point for markpact CLI. CC≤5.
- `handle_pack_cli(argv)` — Handle pack subcommand - pack directory into markpact README.
- `handle_sync_cli(argv)` — Handle sync subcommand — thin orchestrator dispatching to steps.
- `handle_config_cli(argv)` — Handle config subcommand with its own parser
- `detect_format(path)` — Detect notebook format from file extension.
- `parse_jupyter(path)` — Parse Jupyter .ipynb notebook.
- `parse_rmarkdown(path)` — Parse R Markdown .Rmd file.
- `parse_quarto(path)` — Parse Quarto .qmd file (similar to R Markdown but multi-language).
- `parse_zeppelin(path)` — Parse Zeppelin .zpln notebook.
- `parse_databricks(path)` — Parse Databricks .dib notebook.
- `parse_notebook(path)` — Parse notebook file based on format.
- `extract_dependencies(notebook)` — Extract dependencies from notebook code cells.
- `suggest_run_command(notebook)` — Suggest a run command based on notebook content.
- `notebook_to_markpact(notebook, output_path, verbose)` — Convert notebook to markpact README.md format.
- `convert_notebook(input_path, output_path, verbose)` — Convert a notebook file to markpact format.
- `get_supported_formats()` — Get dictionary of supported notebook formats.
- `main()` — —
- `pack_directory(source_dir, output)` — Pack a directory into markpact README.md format.
- `print_pack_report(result)` — Print a report of the packing operation.
- `get_ssh_manager(host, user, key_file)` — Factory for SSH session manager.
- `bump_version(version, bump_type)` — Bump semantic version.
- `extract_version_from_readme(readme_path)` — Extract version from README markpact:publish block.
- `update_version_in_readme(readme_path, new_version)` — Update version in README file.
- `stop_existing_container(container_name, verbose)` — Stop and remove existing container if it exists.
- `generate_dockerfile(sandbox_path, deps, run_command)` — Generate a Dockerfile for the markpact project.
- `is_port_free(port)` — Check if a port is free.
- `build_and_run_docker(sandbox_path, image_name, port, verbose)` — Build and run Docker container from sandbox.
- `check_docker_available()` — Check if Docker is available.
- `run_docker_with_logs(sandbox_path, image_name, port, follow_logs)` — Start Docker container and return process for log monitoring.
- `stream_docker_logs(process, timeout)` — Stream logs from Docker container.
- `run_docker_with_tests(sandbox_path, test_body, image_name, port)` — Build, run Docker container, execute tests, and return results.
- `infer_publish_config(readme_path, markdown, blocks, run_command)` — Infer a reasonable PublishConfig for READMEs without markpact:publish.
- `prompt_publish_config(config)` — Interactively ask user for missing or important publish fields.
- `ensure_publish_block_in_readme(readme_path, config)` — Insert a markpact:publish block into README if none exists.
- `generate_package_json(config, sandbox)` — Generate package.json for npm publishing.
- `publish_npm(config, sandbox, registry, verbose)` — Publish package to npm registry.
- `run_cmd(cmd, sandbox, verbose)` — Run command in sandbox with venv-aware PATH
- `ensure_venv(sandbox, verbose)` — Create venv in sandbox if not exists and not disabled
- `install_deps(deps, sandbox, verbose)` — Install Python dependencies in sandbox
- `get_license_classifier(license_name)` — Map license name to PyPI classifier.
- `generate_pyproject_toml(config, sandbox, base_path, verbose)` — Generate pyproject.toml for PyPI publishing.
- `publish_pypi(config, sandbox, test, verbose)` — Publish package to PyPI.
- `parse_publish_block(block_body, meta)` — Parse publish block content into config.
- `publish(config, sandbox, bump, verbose)` — Publish to specified registry.
- `publish_github_packages(config, sandbox, package_type, verbose)` — Publish to GitHub Packages.
- `log()` — —
- `log_verbose()` — —
- `test_example()` — —
- `test_publish_example()` — —
- `test_converter_example()` — —
- `test_notebook_example()` — —
- `get_pyproject_version()` — Extract version from pyproject.toml.
- `get_bumpversion_version()` — Extract version from .bumpversion.toml.
- `set_pyproject_version(new_ver)` — Set version in pyproject.toml.
- `set_bumpversion_version(new_ver)` — Set version in .bumpversion.toml.
- `tag_exists(tag)` — Check if git tag exists.
- `get_next_version(current)` — Get next patch version.
- `sync_versions()` — Sync both version files to the MAX version, ensuring next version tag doesn't exist.
- `generate_dockerfile(config, sandbox, base_image)` — Generate Dockerfile for Docker publishing.
- `publish_docker(config, sandbox, registry, tag)` — Build and push Docker image to registry.
- `detect_error_type(error_output, exit_code, cmd)` — Detect the type of error from output.
- `fix_port_in_readme(readme_path, new_port)` — Update the port in a README file.
- `run_with_auto_fix(cmd, sandbox, readme_path, verbose)` — Run command with automatic error detection and fixing.
- `add_missing_dependency(readme_path, module_name)` — Add a missing dependency to the README deps block.
- `extract_module_name(error_output)` — Extract missing module name from ModuleNotFoundError.
- `fix_with_llm(readme_path, error_output, error_type, verbose)` — Use LLM to fix errors in the README.
- `run_with_auto_fix_llm(cmd, sandbox, readme_path, verbose)` — Run command with automatic error detection and fixing (with optional LLM).
- `parse_blocks(text)` — Parse all markpact:* codeblocks from markdown text.
- `parse_blocks_recursive(text)` — Parse blocks with recursive include resolution.
- `create_backup(readme_path)` — Create a timestamped backup of README before sync.
- `list_backups(readme_path)` — List all backup files, newest first.
- `restore_backup(readme_path, backup_path)` — Restore README from a backup (rollback).
- `list_tracked_paths(text)` — List all file paths tracked in markpact:file blocks.
- `find_untracked_files(text, source_dir)` — Find files in source directory not tracked in README markpact blocks.
- `diff_block(rel_path, old_body, new_body)` — Generate unified diff between old and new block content.
- `sync_readme(readme_path, source_dir)` — Sync source directory files into README.md markpact:file blocks.
- `sync_readme_recursive(readme_path, source_dir)` — Sync README and all included sub-READMEs recursively.
- `add_untracked_blocks(readme_path, source_dir, paths)` — Append new markpact:file blocks for untracked files to README.
- `print_sync_report(result)` — Print a formatted report of the sync operation.
- `generate_publish_config_with_llm(markdown, verbose)` — Try to generate a publish config using LLM.
- `generate_contract(prompt, config, verbose)` — Generate a markpact contract from a text prompt.
- `save_contract(content, output_path, verbose)` — Save generated contract to file.
- `get_example_prompt(name)` — Get example prompt by name.
- `list_example_prompts()` — List all available example prompts.
- `hdr(text)` — —
- `step(icon, text)` — —
- `ok(text, detail)` — —
- `fail(text, detail)` — —
- `wait(text)` — —
- `wait_done(ok_flag)` — —
- `info(text)` — —
- `show_menu()` — —
- `list_prompts()` — —
- `run_live(prompt_key, prompt, model)` — Main pipeline: prompt -> generate -> parse -> validate -> PDF.
- `main()` — —


## Project Structure

📄 `examples.demo_live_markpact` (29 functions, 2 classes)
📄 `examples.sync-workflow.src.app` (1 functions)
📄 `examples.sync-workflow.src.run`
📄 `project`
📄 `scripts.sync_version` (7 functions)
📄 `scripts.test_examples` (6 functions)
📦 `src.markpact`
📄 `src.markpact.auto_fix` (15 functions)
📦 `src.markpact.cli` (5 functions)
📄 `src.markpact.cli.config_cmd` (1 functions)
📄 `src.markpact.cli.convert_cmd` (5 functions)
📄 `src.markpact.cli.helpers` (2 functions)
📄 `src.markpact.cli.pack_cmd` (1 functions)
📄 `src.markpact.cli.publish_cmd` (5 functions)
📄 `src.markpact.cli.run_cmd` (7 functions)
📄 `src.markpact.cli.sync_cmd` (11 functions)
📄 `src.markpact.config` (12 functions)
📄 `src.markpact.converter` (10 functions, 2 classes)
📄 `src.markpact.docker_runner` (16 functions)
📄 `src.markpact.generator` (11 functions, 1 classes)
📄 `src.markpact.notebook_converter` (25 functions, 2 classes)
📄 `src.markpact.packer` (12 functions, 1 classes)
📄 `src.markpact.parser` (4 functions, 1 classes)
📦 `src.markpact.publish`
📄 `src.markpact.publish.docker_pub` (2 functions)
📄 `src.markpact.publish.github` (1 functions)
📄 `src.markpact.publish.helpers` (13 functions)
📄 `src.markpact.publish.llm_config` (5 functions)
📄 `src.markpact.publish.main` (2 functions)
📄 `src.markpact.publish.models` (1 functions, 2 classes)
📄 `src.markpact.publish.npm` (3 functions)
📄 `src.markpact.publish.pypi` (21 functions)
📄 `src.markpact.publish.version` (3 functions)
📄 `src.markpact.publisher`
📄 `src.markpact.runner` (3 functions)
📦 `src.markpact.runtime`
📄 `src.markpact.runtime.cli` (1 functions)
📄 `src.markpact.runtime.core` (12 functions, 2 classes)
📄 `src.markpact.runtime.core_v2` (19 functions, 2 classes)
📄 `src.markpact.runtime.core_v3` (29 functions, 4 classes)
📄 `src.markpact.runtime.exceptions` (5 functions, 8 classes)
📄 `src.markpact.runtime.executors` (23 functions, 11 classes)
📄 `src.markpact.runtime.models` (4 functions, 5 classes)
📄 `src.markpact.runtime.parser` (5 functions, 3 classes)
📄 `src.markpact.runtime.plugins` (14 functions, 3 classes)
📄 `src.markpact.runtime.ssh_manager` (7 functions, 1 classes)
📄 `src.markpact.runtime.state` (17 functions, 2 classes)
📄 `src.markpact.runtime.steps` (3 functions, 3 classes)
📄 `src.markpact.sandbox` (6 functions, 1 classes)
📄 `src.markpact.syncer` (21 functions, 1 classes)
📄 `src.markpact.template` (5 functions)
📄 `src.markpact.tester` (7 functions, 2 classes)

## Requirements

- Python >= >=3.10
- goal >=2.1.0- costs >=0.1.20- pfix >=0.1.60

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Open an issue or pull request to get started.
### Development Setup

```bash
# Clone the repository
git clone https://github.com/wronai/markpact
cd markpact

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `examples` | Usage examples and code samples | [View](./examples) |

<!-- code2docs:end -->