# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/wronai/markpact
- **Analysis Mode**: static
- **Total Functions**: 265
- **Total Classes**: 13
- **Modules**: 35
- **Entry Points**: 27

## Architecture by Module

### examples.demo_live_markpact
- **Functions**: 29
- **Classes**: 2
- **File**: `demo_live_markpact.py`

### src.markpact.notebook_converter
- **Functions**: 25
- **Classes**: 2
- **File**: `notebook_converter.py`

### src.markpact.syncer
- **Functions**: 21
- **Classes**: 1
- **File**: `syncer.py`

### src.markpact.publish.pypi
- **Functions**: 21
- **File**: `pypi.py`

### src.markpact.docker_runner
- **Functions**: 16
- **File**: `docker_runner.py`

### src.markpact.auto_fix
- **Functions**: 15
- **File**: `auto_fix.py`

### src.markpact.publish.helpers
- **Functions**: 13
- **File**: `helpers.py`

### src.markpact.config
- **Functions**: 12
- **File**: `config.py`

### src.markpact.packer
- **Functions**: 12
- **Classes**: 1
- **File**: `packer.py`

### src.markpact.cli.sync_cmd
- **Functions**: 11
- **File**: `sync_cmd.py`

### src.markpact.generator
- **Functions**: 11
- **Classes**: 1
- **File**: `generator.py`

### src.markpact.converter
- **Functions**: 10
- **Classes**: 2
- **File**: `converter.py`

### scripts.sync_version
- **Functions**: 7
- **File**: `sync_version.py`

### src.markpact.cli.run_cmd
- **Functions**: 7
- **File**: `run_cmd.py`

### src.markpact.sandbox
- **Functions**: 6
- **Classes**: 1
- **File**: `sandbox.py`

### src.markpact.template
- **Functions**: 5
- **File**: `template.py`

### src.markpact.cli
- **Functions**: 5
- **File**: `__init__.py`

### src.markpact.cli.publish_cmd
- **Functions**: 5
- **File**: `publish_cmd.py`

### src.markpact.cli.convert_cmd
- **Functions**: 5
- **File**: `convert_cmd.py`

### src.markpact.publish.llm_config
- **Functions**: 5
- **File**: `llm_config.py`

## Key Entry Points

Main execution flows into the system:

### examples.demo_live_markpact.main
- **Calls**: argparse.ArgumentParser, parser.add_argument, parser.add_argument, parser.add_argument, parser.add_argument, parser.parse_args, examples.demo_live_markpact.run_live, examples.demo_live_markpact.list_prompts

### examples.demo_live_markpact._save_outputs
> Save README and PDF outputs.
- **Calls**: readme_path.write_text, examples.demo_live_markpact.ok, print, str, pdf.page_no, range, pdf.output, examples.demo_live_markpact.ok

### src.markpact.publish.helpers.ensure_publish_block_in_readme
> Insert a markpact:publish block into README if none exists.
- **Calls**: readme_path.read_text, re.search, lines.append, None.join, re.search, readme_path.write_text, lines.append, lines.append

### scripts.sync_version.sync_versions
> Sync both version files to the MAX version, ensuring next version tag doesn't exist.
- **Calls**: scripts.sync_version.get_pyproject_version, scripts.sync_version.get_bumpversion_version, max, scripts.sync_version.tag_exists, scripts.sync_version.get_next_version, scripts.sync_version.set_pyproject_version, print, scripts.sync_version.set_bumpversion_version

### src.markpact.docker_runner.stream_docker_logs
> Stream logs from Docker container.
- **Calls**: time.time, process.stdout.readline, print, subprocess.run, process.poll, print, sys.stdout.flush, time.time

### src.markpact.docker_runner.run_docker_with_tests
> Build, run Docker container, execute tests, and return results.
- **Calls**: src.markpact.docker_runner._build_docker_image, src.markpact.docker_runner._resolve_docker_port, src.markpact.docker_runner._start_docker_container, src.markpact.docker_runner._run_docker_tests, src.markpact.docker_runner._stop_docker_container, TestSuite, TestSuite, TestResult

### src.markpact.publish.version.extract_version_from_readme
> Extract version from README markpact:publish block.
- **Calls**: readme_path.read_text, re.search, re.search, match.group, re.search, version_match.group, None.strip, version_match.group

### src.markpact.generator.GeneratorConfig.from_env
> Load config from environment variables
- **Calls**: cls, os.environ.get, os.environ.get, os.environ.get, float, int, os.environ.get, os.environ.get

### src.markpact.docker_runner.run_docker_with_logs
> Start Docker container and return process for log monitoring.

Returns:
    Tuple of (Popen process, actual port used)
- **Calls**: src.markpact.docker_runner.stop_existing_container, subprocess.Popen, src.markpact.sandbox.find_free_port, print, print, src.markpact.docker_runner.is_port_free, print

### src.markpact.cli.main
> Main entry point for markpact CLI. CC≤5.
- **Calls**: src.markpact.cli._parse_main_args, src.markpact.cli._handle_generation_phase, isinstance, src.markpact.cli._process_readme, src.markpact.cli._dispatch_subcommand, src.markpact.cli.convert_cmd._handle_list_examples, src.markpact.cli.convert_cmd._handle_list_notebook_formats

### src.markpact.auto_fix.run_with_auto_fix
> Run command with automatic error detection and fixing.

Args:
    cmd: Command to run
    sandbox: Sandbox instance
    readme_path: Path to README.md
- **Calls**: src.markpact.auto_fix._setup_env_with_venv_simple, range, src.markpact.auto_fix.detect_error_type, src.markpact.auto_fix._run_and_print, src.markpact.auto_fix._handle_port_error_simple

### src.markpact.generator.GeneratorConfig.from_file
> Load config from JSON file
- **Calls**: json.loads, cls, path.exists, cls.from_env, path.read_text

### src.markpact.sandbox.Sandbox.__init__
- **Calls**: None.resolve, self.path.mkdir, Path, os.environ.get

### src.markpact.generator.save_contract
> Save generated contract to file.

Args:
    content: Generated README content
    output_path: Where to save the file
    verbose: Print save location
- **Calls**: output_path.parent.mkdir, output_path.write_text, print

### src.markpact.sandbox.Sandbox.write_file
> Write file to sandbox, creating directories as needed
- **Calls**: full.parent.mkdir, full.write_text

### src.markpact.sandbox.Sandbox.write_requirements
> Write requirements.txt
- **Calls**: req.write_text, None.join

### src.markpact.sandbox.Sandbox.clean
> Remove sandbox directory
- **Calls**: self.path.exists, shutil.rmtree

### src.markpact.parser.Block.get_meta_value
> Extract a key=value pair from the meta string.
- **Calls**: re.search, re.escape

### src.markpact.packer.PackResult.summary
> Return human-readable summary.
- **Calls**: None.join, lines.append

### src.markpact.syncer.SyncResult.summary
> Return human-readable summary.
- **Calls**: None.join, lines.append

### examples.demo_live_markpact.LiveSession.add_step
- **Calls**: self.steps.append, StepRecord

### src.markpact.sandbox.Sandbox.has_venv
- **Calls**: self.venv_python.exists

### src.markpact.parser.Block.get_path
> Extract path= from meta
- **Calls**: re.search

### examples.demo_live_markpact._ascii
> Transliterate Polish chars to ASCII for PDF rendering.
- **Calls**: text.translate

### examples.demo_live_markpact.LiveSession.elapsed
- **Calls**: time.time

### examples.sync-workflow.src.app.root
- **Calls**: app.get

### src.markpact.publish.models.PublishConfig.__post_init__

## Process Flows

Key execution flows identified:

### Flow 1: main
```
main [examples.demo_live_markpact]
```

### Flow 2: _save_outputs
```
_save_outputs [examples.demo_live_markpact]
  └─> ok
```

### Flow 3: ensure_publish_block_in_readme
```
ensure_publish_block_in_readme [src.markpact.publish.helpers]
```

### Flow 4: sync_versions
```
sync_versions [scripts.sync_version]
  └─> get_pyproject_version
  └─> get_bumpversion_version
```

### Flow 5: stream_docker_logs
```
stream_docker_logs [src.markpact.docker_runner]
```

### Flow 6: run_docker_with_tests
```
run_docker_with_tests [src.markpact.docker_runner]
  └─> _build_docker_image
  └─> _resolve_docker_port
      └─> is_port_free
      └─ →> find_free_port
```

### Flow 7: extract_version_from_readme
```
extract_version_from_readme [src.markpact.publish.version]
```

### Flow 8: from_env
```
from_env [src.markpact.generator.GeneratorConfig]
```

### Flow 9: run_docker_with_logs
```
run_docker_with_logs [src.markpact.docker_runner]
  └─> stop_existing_container
  └─ →> find_free_port
```

### Flow 10: run_with_auto_fix
```
run_with_auto_fix [src.markpact.auto_fix]
  └─> _setup_env_with_venv_simple
  └─> detect_error_type
```

## Key Classes

### src.markpact.sandbox.Sandbox
> Manages sandbox directory for markpact execution
- **Methods**: 8
- **Key Methods**: src.markpact.sandbox.Sandbox.__init__, src.markpact.sandbox.Sandbox.venv_bin, src.markpact.sandbox.Sandbox.venv_pip, src.markpact.sandbox.Sandbox.venv_python, src.markpact.sandbox.Sandbox.has_venv, src.markpact.sandbox.Sandbox.write_file, src.markpact.sandbox.Sandbox.write_requirements, src.markpact.sandbox.Sandbox.clean

### src.markpact.parser.Block
- **Methods**: 2
- **Key Methods**: src.markpact.parser.Block.get_path, src.markpact.parser.Block.get_meta_value

### examples.demo_live_markpact.LiveSession
- **Methods**: 2
- **Key Methods**: examples.demo_live_markpact.LiveSession.add_step, examples.demo_live_markpact.LiveSession.elapsed

### src.markpact.generator.GeneratorConfig
> Configuration for LLM generator
- **Methods**: 2
- **Key Methods**: src.markpact.generator.GeneratorConfig.from_env, src.markpact.generator.GeneratorConfig.from_file

### src.markpact.packer.PackResult
> Result of packing a directory.
- **Methods**: 1
- **Key Methods**: src.markpact.packer.PackResult.summary

### src.markpact.syncer.SyncResult
> Result of a sync operation.
- **Methods**: 1
- **Key Methods**: src.markpact.syncer.SyncResult.summary

### src.markpact.publish.models.PublishConfig
> Configuration for publishing
- **Methods**: 1
- **Key Methods**: src.markpact.publish.models.PublishConfig.__post_init__

### src.markpact.notebook_converter.NotebookCell
> Represents a cell in a notebook.
- **Methods**: 0

### src.markpact.notebook_converter.Notebook
> Represents a parsed notebook.
- **Methods**: 0

### src.markpact.converter.ConvertedBlock
> A converted markpact block.
- **Methods**: 0

### src.markpact.converter.ConversionResult
> Result of converting a Markdown file.
- **Methods**: 0

### examples.demo_live_markpact.StepRecord
- **Methods**: 0

### src.markpact.publish.models.PublishResult
> Result of a publish operation
- **Methods**: 0

## Data Transformation Functions

Key functions that process and transform data:

### src.markpact.notebook_converter.detect_format
> Detect notebook format from file extension.
- **Output to**: path.suffix.lower, format_map.get

### src.markpact.notebook_converter.parse_jupyter
> Parse Jupyter .ipynb notebook.
- **Output to**: json.loads, content.get, metadata.get, kernel_info.get, content.get

### src.markpact.notebook_converter._parse_rmd_yaml_front_matter
> Parse YAML front matter from R Markdown. Returns (metadata, title, remaining_content).
- **Output to**: re.match, yaml_match.group, yaml_content.split, line.startswith, None.strip

### src.markpact.notebook_converter._parse_rmd_code_chunks
> Parse R Markdown code chunks. Returns list of cells.
- **Output to**: re.finditer, None.strip, None.strip, match.group, None.strip

### src.markpact.notebook_converter.parse_rmarkdown
> Parse R Markdown .Rmd file.
- **Output to**: path.read_text, src.markpact.notebook_converter._parse_rmd_yaml_front_matter, src.markpact.notebook_converter._parse_rmd_code_chunks, src.markpact.notebook_converter._extract_description_from_cells, Notebook

### src.markpact.notebook_converter._parse_quarto_yaml_front_matter
> Parse YAML front matter from Quarto. Returns (metadata, title, remaining_content, default_language).
- **Output to**: re.match, yaml_match.group, yaml_content.split, line.startswith, None.strip

### src.markpact.notebook_converter._parse_quarto_code_chunks
> Parse Quarto code chunks. Returns list of cells.
- **Output to**: re.finditer, None.strip, None.strip, match.group, None.strip

### src.markpact.notebook_converter.parse_quarto
> Parse Quarto .qmd file (similar to R Markdown but multi-language).
- **Output to**: path.read_text, src.markpact.notebook_converter._parse_quarto_yaml_front_matter, src.markpact.notebook_converter._parse_quarto_code_chunks, Notebook

### src.markpact.notebook_converter.parse_zeppelin
> Parse Zeppelin .zpln notebook.
- **Output to**: json.loads, content.get, content.get, Notebook, path.read_text

### src.markpact.notebook_converter.parse_databricks
> Parse Databricks .dib notebook.
- **Output to**: json.loads, content.get, content.get, Notebook, path.read_text

### src.markpact.notebook_converter.parse_notebook
> Parse notebook file based on format.
- **Output to**: src.markpact.notebook_converter.detect_format, src.markpact.notebook_converter.parse_jupyter, src.markpact.notebook_converter.parse_rmarkdown, src.markpact.notebook_converter.parse_quarto, src.markpact.notebook_converter.parse_zeppelin

### src.markpact.notebook_converter._extract_and_format_deps
> Extract dependencies and format as markpact block.
- **Output to**: src.markpact.notebook_converter.extract_dependencies, lines.append, lines.append, lines.append, lines.append

### src.markpact.notebook_converter._process_notebook_cells
> Process notebook cells and return (code_cells, markdown_sections).
- **Output to**: code_cells.append, src.markpact.notebook_converter._should_skip_first_markdown_cell, src.markpact.notebook_converter._extract_markdown_section, code_cells.append, markdown_sections.append

### src.markpact.notebook_converter.convert_notebook
> Convert a notebook file to markpact format.

Args:
    input_path: Path to notebook file (.ipynb, .R
- **Output to**: src.markpact.notebook_converter.detect_format, src.markpact.notebook_converter.parse_notebook, src.markpact.notebook_converter.notebook_to_markpact, input_path.exists, FileNotFoundError

### src.markpact.notebook_converter.get_supported_formats
> Get dictionary of supported notebook formats.

### src.markpact.parser.parse_blocks
> Parse all markpact:* codeblocks from markdown text.

Supports both formats:
- New: ```python markpac
- **Output to**: CODEBLOCK_NEW_RE.finditer, CODEBLOCK_OLD_RE.finditer, blocks.append, blocks.append, Block

### src.markpact.parser.parse_blocks_recursive
> Parse blocks with recursive include resolution.

Resolves ``<!-- markpact:include path=sub/README.md
- **Output to**: src.markpact.parser.parse_blocks, _INCLUDE_COMMENT_RE.finditer, set, Path.cwd, None.resolve

### src.markpact.auto_fix._run_subprocess
> Run subprocess with proper error handling.
- **Output to**: subprocess.run

### src.markpact.converter.convert_markdown_to_markpact
> Convert regular Markdown to markpact format.

Analyzes code blocks and converts them to markpact:* f
- **Output to**: ConversionResult, re.search, re.compile, pattern.sub, result.changes.append

### src.markpact.cli.helpers._parse_blocks_to_state
> Parse blocks and extract state. Returns state dict with error key if failed.
- **Output to**: block.get_path, src.markpact.cli.helpers._resolve_file_body, print, print, sandbox.write_file

### src.markpact.syncer._process_block
> Process a single markpact:file block match. CC≤8.
- **Output to**: src.markpact.syncer._read_source_file, src.markpact.syncer._build_header_suffix, result.details.append, m.group, m.group

### src.markpact.cli._parse_main_args
> Build and parse the main argument parser.
- **Output to**: argparse.ArgumentParser, parser.add_argument, parser.add_argument, parser.add_argument, parser.add_argument

### src.markpact.cli._process_readme
> Parse blocks, extract state, dispatch to mode handler.
- **Output to**: Sandbox, readme.read_text, src.markpact.cli.convert_cmd._handle_markdown_conversion, getattr, src.markpact.cli.helpers._parse_blocks_to_state

### src.markpact.cli.sync_cmd._build_sync_parser
> Build the sync subcommand argument parser.
- **Output to**: argparse.ArgumentParser, parser.add_argument, parser.add_argument, parser.add_argument, parser.add_argument

### src.markpact.cli.convert_cmd._handle_list_notebook_formats
> Handle --list-notebook-formats flag.
- **Output to**: print, None.items, print, print, src.markpact.notebook_converter.get_supported_formats

## Behavioral Patterns

### recursion_parse_blocks_recursive
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: src.markpact.parser.parse_blocks_recursive

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `src.markpact.cli.config_cmd.handle_config_cli` - 35 calls
- `src.markpact.notebook_converter.parse_zeppelin` - 30 calls
- `src.markpact.notebook_converter.parse_databricks` - 30 calls
- `src.markpact.notebook_converter.parse_jupyter` - 24 calls
- `examples.demo_live_markpact.run_live` - 22 calls
- `src.markpact.template.resolve_template` - 20 calls
- `src.markpact.packer.pack_directory` - 20 calls
- `src.markpact.converter.convert_markdown_to_markpact` - 19 calls
- `src.markpact.parser.parse_blocks` - 18 calls
- `src.markpact.parser.parse_blocks_recursive` - 18 calls
- `src.markpact.syncer.sync_readme_recursive` - 18 calls
- `src.markpact.syncer.print_sync_report` - 18 calls
- `examples.demo_live_markpact.show_menu` - 18 calls
- `examples.demo_live_markpact.main` - 18 calls
- `src.markpact.notebook_converter.notebook_to_markpact` - 16 calls
- `src.markpact.publish.helpers.prompt_publish_config` - 16 calls
- `src.markpact.syncer.sync_readme` - 15 calls
- `src.markpact.cli.pack_cmd.handle_pack_cli` - 15 calls
- `src.markpact.publish.main.parse_publish_block` - 15 calls
- `src.markpact.auto_fix.run_with_auto_fix_llm` - 14 calls
- `src.markpact.cli.sync_cmd.handle_sync_cli` - 14 calls
- `src.markpact.publish.pypi.publish_pypi` - 14 calls
- `src.markpact.config.load_env` - 12 calls
- `src.markpact.packer.print_pack_report` - 12 calls
- `src.markpact.syncer.find_untracked_files` - 12 calls
- `src.markpact.syncer.add_untracked_blocks` - 12 calls
- `src.markpact.publish.helpers.ensure_publish_block_in_readme` - 12 calls
- `src.markpact.publish.docker_pub.publish_docker` - 12 calls
- `scripts.sync_version.sync_versions` - 11 calls
- `src.markpact.docker_runner.generate_dockerfile` - 11 calls
- `src.markpact.publish.helpers.infer_publish_config` - 11 calls
- `src.markpact.template.load_secrets` - 10 calls
- `src.markpact.notebook_converter.extract_dependencies` - 10 calls
- `src.markpact.syncer.create_backup` - 10 calls
- `src.markpact.publish.npm.publish_npm` - 10 calls
- `src.markpact.config.save_env` - 9 calls
- `src.markpact.config.list_providers` - 9 calls
- `src.markpact.docker_runner.stream_docker_logs` - 9 calls
- `src.markpact.docker_runner.run_docker_with_tests` - 9 calls
- `src.markpact.notebook_converter.convert_notebook` - 9 calls

## System Interactions

How components interact:

```mermaid
graph TD
    main --> ArgumentParser
    main --> add_argument
    _save_outputs --> write_text
    _save_outputs --> ok
    _save_outputs --> print
    _save_outputs --> str
    _save_outputs --> page_no
    ensure_publish_block --> read_text
    ensure_publish_block --> search
    ensure_publish_block --> append
    ensure_publish_block --> join
    sync_versions --> get_pyproject_versio
    sync_versions --> get_bumpversion_vers
    sync_versions --> max
    sync_versions --> tag_exists
    sync_versions --> get_next_version
    stream_docker_logs --> time
    stream_docker_logs --> readline
    stream_docker_logs --> print
    stream_docker_logs --> run
    stream_docker_logs --> poll
    run_docker_with_test --> _build_docker_image
    run_docker_with_test --> _resolve_docker_port
    run_docker_with_test --> _start_docker_contai
    run_docker_with_test --> _run_docker_tests
    run_docker_with_test --> _stop_docker_contain
    extract_version_from --> read_text
    extract_version_from --> search
    extract_version_from --> group
    from_env --> cls
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.