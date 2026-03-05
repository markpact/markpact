# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/wronai/markpact
- **Analysis Mode**: static
- **Total Functions**: 114
- **Total Classes**: 12
- **Modules**: 13
- **Entry Points**: 34

## Architecture by Module

### demos.demo_live_markpact
- **Functions**: 28
- **Classes**: 3
- **File**: `demo_live_markpact.py`

### src.markpact.publisher
- **Functions**: 22
- **Classes**: 2
- **File**: `publisher.py`

### src.markpact.config
- **Functions**: 12
- **File**: `config.py`

### src.markpact.notebook_converter
- **Functions**: 12
- **Classes**: 2
- **File**: `notebook_converter.py`

### src.markpact.docker_runner
- **Functions**: 8
- **File**: `docker_runner.py`

### src.markpact.auto_fix
- **Functions**: 7
- **File**: `auto_fix.py`

### src.markpact.generator
- **Functions**: 7
- **Classes**: 1
- **File**: `generator.py`

### src.markpact.sandbox
- **Functions**: 6
- **Classes**: 1
- **File**: `sandbox.py`

### src.markpact.converter
- **Functions**: 4
- **Classes**: 2
- **File**: `converter.py`

### src.markpact.runner
- **Functions**: 3
- **File**: `runner.py`

### src.markpact.parser
- **Functions**: 3
- **Classes**: 1
- **File**: `parser.py`

### src.markpact.cli
- **Functions**: 2
- **File**: `cli.py`

## Key Entry Points

Main execution flows into the system:

### src.markpact.cli.main
- **Calls**: argparse.ArgumentParser, parser.add_argument, parser.add_argument, parser.add_argument, parser.add_argument, parser.add_argument, parser.add_argument, parser.add_argument

### demos.demo_live_markpact.LivePDF.add_summary_page
- **Calls**: self.add_page, self._bg, self.set_font, self.set_text_color, self.get_string_width, self.set_xy, self.cell, sum

### demos.demo_live_markpact.LivePDF._render_mono
- **Calls**: line.startswith, self.set_xy, self.cell, self.set_text_color, self.set_font, self.set_xy, self.cell, self.set_text_color

### src.markpact.docker_runner.run_docker_with_tests
> Build, run Docker container, execute tests, and return results.
- **Calls**: subprocess.run, src.markpact.docker_runner.stop_existing_container, subprocess.Popen, print, print, print, run_tests_from_block, suite.print_summary

### demos.demo_live_markpact.LivePDF.add_title_page
- **Calls**: self.add_page, self._bg, self.set_font, self.set_text_color, self.get_string_width, self.set_xy, self.cell, self.set_font

### src.markpact.auto_fix.run_with_auto_fix
> Run command with automatic error detection and fixing.

Args:
    cmd: Command to run
    sandbox: Sandbox instance
    readme_path: Path to README.md
- **Calls**: os.environ.copy, sandbox.venv_bin.exists, range, str, src.markpact.auto_fix.detect_error_type, print, subprocess.run, print

### demos.demo_live_markpact.LivePDF._render_checks
- **Calls**: self.set_draw_color, self.line, self.set_font, self.set_text_color, self.set_xy, self.cell, self.set_font, self.set_text_color

### demos.demo_live_markpact.main
- **Calls**: argparse.ArgumentParser, parser.add_argument, parser.add_argument, parser.add_argument, parser.add_argument, parser.parse_args, demos.demo_live_markpact.run_live, demos.demo_live_markpact.list_prompts

### demos.demo_live_markpact.LivePDF.add_step_page
> Add a split-screen step page.
- **Calls**: self.add_page, self._bg, self.set_font, self.set_text_color, self.set_xy, self.cell, self.set_font, self.set_text_color

### demos.demo_live_markpact.LivePDF._render_right
- **Calls**: self.set_xy, self.cell, self.set_font, line.startswith, self.set_text_color, self.set_font, line.startswith, self.set_text_color

### src.markpact.publisher.ensure_publish_block_in_readme
> Insert a markpact:publish block into README if none exists.
- **Calls**: readme_path.read_text, re.search, lines.append, None.join, re.search, readme_path.write_text, lines.append, lines.append

### demos.demo_live_markpact.LivePDF._draw_panel
- **Calls**: self.set_draw_color, self.set_fill_color, self.rect, self.set_fill_color, self.rect, self.set_draw_color, self.line, self.set_font

### src.markpact.docker_runner.stream_docker_logs
> Stream logs from Docker container.
- **Calls**: time.time, process.stdout.readline, print, subprocess.run, process.poll, print, sys.stdout.flush, time.time

### src.markpact.publisher.extract_version_from_readme
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

### src.markpact.generator.GeneratorConfig.from_file
> Load config from JSON file
- **Calls**: json.loads, cls, path.exists, cls.from_env, path.read_text

### demos.demo_live_markpact.LivePDF._page_num
- **Calls**: self.set_font, self.set_text_color, self.set_xy, self.cell, self.page_no

### src.markpact.sandbox.Sandbox.__init__
- **Calls**: None.resolve, self.path.mkdir, Path, os.environ.get

### demos.demo_live_markpact.LivePDF.cell
- **Calls**: None.cell, demos.demo_live_markpact._ascii, super, str

### demos.demo_live_markpact.LivePDF.multi_cell
- **Calls**: None.multi_cell, demos.demo_live_markpact._ascii, super, str

### demos.demo_live_markpact.LivePDF.get_string_width
- **Calls**: None.get_string_width, demos.demo_live_markpact._ascii, super, str

### src.markpact.generator.save_contract
> Save generated contract to file.

Args:
    content: Generated README content
    output_path: Where to save the file
    verbose: Print save location
- **Calls**: output_path.parent.mkdir, output_path.write_text, print

### demos.demo_live_markpact.LivePDF.__init__
- **Calls**: None.__init__, self.set_auto_page_break, super

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

### demos.demo_live_markpact.LiveSession.add_step
- **Calls**: self.steps.append, StepRecord

### demos.demo_live_markpact.LivePDF._bg
- **Calls**: self.set_fill_color, self.rect

## Process Flows

Key execution flows identified:

### Flow 1: main
```
main [src.markpact.cli]
```

### Flow 2: add_summary_page
```
add_summary_page [demos.demo_live_markpact.LivePDF]
```

### Flow 3: _render_mono
```
_render_mono [demos.demo_live_markpact.LivePDF]
```

### Flow 4: run_docker_with_tests
```
run_docker_with_tests [src.markpact.docker_runner]
  └─> stop_existing_container
```

### Flow 5: add_title_page
```
add_title_page [demos.demo_live_markpact.LivePDF]
```

### Flow 6: run_with_auto_fix
```
run_with_auto_fix [src.markpact.auto_fix]
  └─> detect_error_type
```

### Flow 7: _render_checks
```
_render_checks [demos.demo_live_markpact.LivePDF]
```

### Flow 8: add_step_page
```
add_step_page [demos.demo_live_markpact.LivePDF]
```

### Flow 9: _render_right
```
_render_right [demos.demo_live_markpact.LivePDF]
```

### Flow 10: ensure_publish_block_in_readme
```
ensure_publish_block_in_readme [src.markpact.publisher]
```

## Key Classes

### demos.demo_live_markpact.LivePDF
> Landscape A4 PDF with dark theme for live demo output.
- **Methods**: 13
- **Key Methods**: demos.demo_live_markpact.LivePDF.__init__, demos.demo_live_markpact.LivePDF.cell, demos.demo_live_markpact.LivePDF.multi_cell, demos.demo_live_markpact.LivePDF.get_string_width, demos.demo_live_markpact.LivePDF._bg, demos.demo_live_markpact.LivePDF._page_num, demos.demo_live_markpact.LivePDF.add_title_page, demos.demo_live_markpact.LivePDF.add_step_page, demos.demo_live_markpact.LivePDF._draw_panel, demos.demo_live_markpact.LivePDF._render_mono
- **Inherits**: FPDF

### src.markpact.sandbox.Sandbox
> Manages sandbox directory for markpact execution
- **Methods**: 8
- **Key Methods**: src.markpact.sandbox.Sandbox.__init__, src.markpact.sandbox.Sandbox.venv_bin, src.markpact.sandbox.Sandbox.venv_pip, src.markpact.sandbox.Sandbox.venv_python, src.markpact.sandbox.Sandbox.has_venv, src.markpact.sandbox.Sandbox.write_file, src.markpact.sandbox.Sandbox.write_requirements, src.markpact.sandbox.Sandbox.clean

### src.markpact.parser.Block
- **Methods**: 2
- **Key Methods**: src.markpact.parser.Block.get_path, src.markpact.parser.Block.get_meta_value

### src.markpact.generator.GeneratorConfig
> Configuration for LLM generator
- **Methods**: 2
- **Key Methods**: src.markpact.generator.GeneratorConfig.from_env, src.markpact.generator.GeneratorConfig.from_file

### demos.demo_live_markpact.LiveSession
- **Methods**: 2
- **Key Methods**: demos.demo_live_markpact.LiveSession.add_step, demos.demo_live_markpact.LiveSession.elapsed

### src.markpact.publisher.PublishConfig
> Configuration for publishing
- **Methods**: 1
- **Key Methods**: src.markpact.publisher.PublishConfig.__post_init__

### src.markpact.notebook_converter.NotebookCell
> Represents a cell in a notebook.
- **Methods**: 0

### src.markpact.notebook_converter.Notebook
> Represents a parsed notebook.
- **Methods**: 0

### src.markpact.publisher.PublishResult
> Result of a publish operation
- **Methods**: 0

### src.markpact.converter.ConvertedBlock
> A converted markpact block.
- **Methods**: 0

### src.markpact.converter.ConversionResult
> Result of converting a Markdown file.
- **Methods**: 0

### demos.demo_live_markpact.StepRecord
- **Methods**: 0

## Data Transformation Functions

Key functions that process and transform data:

### src.markpact.notebook_converter.detect_format
> Detect notebook format from file extension.
- **Output to**: path.suffix.lower, format_map.get

### src.markpact.notebook_converter.parse_jupyter
> Parse Jupyter .ipynb notebook.
- **Output to**: json.loads, content.get, metadata.get, kernel_info.get, content.get

### src.markpact.notebook_converter.parse_rmarkdown
> Parse R Markdown .Rmd file.
- **Output to**: path.read_text, re.match, re.finditer, None.strip, Notebook

### src.markpact.notebook_converter.parse_quarto
> Parse Quarto .qmd file (similar to R Markdown but multi-language).
- **Output to**: path.read_text, re.match, re.finditer, None.strip, Notebook

### src.markpact.notebook_converter.parse_zeppelin
> Parse Zeppelin .zpln notebook.
- **Output to**: json.loads, content.get, content.get, Notebook, path.read_text

### src.markpact.notebook_converter.parse_databricks
> Parse Databricks .dib notebook.
- **Output to**: json.loads, content.get, content.get, Notebook, path.read_text

### src.markpact.notebook_converter.parse_notebook
> Parse notebook file based on format.
- **Output to**: src.markpact.notebook_converter.detect_format, src.markpact.notebook_converter.parse_jupyter, src.markpact.notebook_converter.parse_rmarkdown, src.markpact.notebook_converter.parse_quarto, src.markpact.notebook_converter.parse_zeppelin

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

### src.markpact.publisher._format_subprocess_failure
- **Output to**: None.strip, None.strip

### src.markpact.publisher.parse_publish_block
> Parse publish block content into config.

Args:
    block_body: The body of the publish block
    me
- **Output to**: all_lines.extend, PublishConfig, all_lines.append, None.splitlines, line.strip

### src.markpact.converter.convert_markdown_to_markpact
> Convert regular Markdown to markpact format.

Analyzes code blocks and converts them to markpact:* f
- **Output to**: ConversionResult, re.search, re.compile, pattern.sub, result.changes.append

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `demos.demo_live_markpact.run_live` - 193 calls
- `src.markpact.cli.main` - 160 calls
- `src.markpact.publisher.publish_pypi` - 108 calls
- `src.markpact.notebook_converter.notebook_to_markpact` - 58 calls
- `demos.demo_live_markpact.LivePDF.add_summary_page` - 58 calls
- `src.markpact.cli.handle_config_cli` - 35 calls
- `src.markpact.notebook_converter.parse_rmarkdown` - 33 calls
- `src.markpact.auto_fix.run_with_auto_fix_llm` - 32 calls
- `src.markpact.notebook_converter.parse_zeppelin` - 30 calls
- `src.markpact.notebook_converter.parse_databricks` - 30 calls
- `src.markpact.notebook_converter.parse_quarto` - 29 calls
- `src.markpact.docker_runner.run_docker_with_tests` - 26 calls
- `demos.demo_live_markpact.LivePDF.add_title_page` - 26 calls
- `src.markpact.publisher.infer_publish_config` - 25 calls
- `src.markpact.notebook_converter.parse_jupyter` - 24 calls
- `src.markpact.auto_fix.run_with_auto_fix` - 20 calls
- `src.markpact.converter.convert_markdown_to_markpact` - 19 calls
- `src.markpact.converter.print_conversion_report` - 19 calls
- `src.markpact.parser.parse_blocks` - 18 calls
- `src.markpact.generator.generate_contract` - 18 calls
- `demos.demo_live_markpact.show_menu` - 18 calls
- `demos.demo_live_markpact.main` - 18 calls
- `src.markpact.docker_runner.build_and_run_docker` - 17 calls
- `demos.demo_live_markpact.LivePDF.add_step_page` - 17 calls
- `src.markpact.publisher.prompt_publish_config` - 16 calls
- `src.markpact.publisher.generate_pyproject_toml` - 15 calls
- `src.markpact.publisher.parse_publish_block` - 15 calls
- `src.markpact.publisher.generate_publish_config_with_llm` - 14 calls
- `src.markpact.publisher.generate_package_json` - 13 calls
- `src.markpact.config.load_env` - 12 calls
- `src.markpact.publisher.ensure_publish_block_in_readme` - 12 calls
- `src.markpact.publisher.generate_dockerfile` - 12 calls
- `src.markpact.publisher.publish_docker` - 12 calls
- `src.markpact.docker_runner.generate_dockerfile` - 11 calls
- `src.markpact.notebook_converter.extract_dependencies` - 10 calls
- `src.markpact.publisher.publish_npm` - 10 calls
- `src.markpact.converter.detect_block_type` - 10 calls
- `src.markpact.config.save_env` - 9 calls
- `src.markpact.config.list_providers` - 9 calls
- `src.markpact.docker_runner.stream_docker_logs` - 9 calls

## System Interactions

How components interact:

```mermaid
graph TD
    main --> ArgumentParser
    main --> add_argument
    add_summary_page --> add_page
    add_summary_page --> _bg
    add_summary_page --> set_font
    add_summary_page --> set_text_color
    add_summary_page --> get_string_width
    _render_mono --> startswith
    _render_mono --> set_xy
    _render_mono --> cell
    _render_mono --> set_text_color
    _render_mono --> set_font
    run_docker_with_test --> run
    run_docker_with_test --> stop_existing_contai
    run_docker_with_test --> Popen
    run_docker_with_test --> print
    add_title_page --> add_page
    add_title_page --> _bg
    add_title_page --> set_font
    add_title_page --> set_text_color
    add_title_page --> get_string_width
    run_with_auto_fix --> copy
    run_with_auto_fix --> exists
    run_with_auto_fix --> range
    run_with_auto_fix --> str
    run_with_auto_fix --> detect_error_type
    _render_checks --> set_draw_color
    _render_checks --> line
    _render_checks --> set_font
    _render_checks --> set_text_color
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.