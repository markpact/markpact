# markpact - + GitOps meets AI Agents — all in one README.

Executable Markdown Runtime – run and manage entire projects directly from a single README.md file using specialized markpact code blocks and isolated Docker sandboxes.

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Intent](#intent)

## Metadata

- **name**: `markpact`
- **version**: `0.1.41`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, app.doql.less, pyqual.yaml, goal.yaml, .env.example, project/(2 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: markpact;
  version: 0.1.41;
}

dependencies {
  runtime: "goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
  dev: "pytest>=7.0, pytest-cov>=4.0, ruff>=0.1, build, twine, bump2version>=1.0, litellm>=1.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

entity[name="Step"] {
  id: string!;
  action: string!;
  description: string!;
  command: string!;
  params: Dict[str, Any]!;
  risk: string!;
  timeout: int!;
  retry: int!;
  when: string;
  skip_if: string;
  check_cmd: string;
  rollback_cmd: string;
}

entity[name="DeploymentConfig"] {
  name: string!;
  version: string!;
  description: string!;
  target: Dict[str, Any]!;
  plugins: List[Dict[str, Any]]!;
}

entity[name="DeployState"] {
  steps_done: List[str]!;
  step_hashes: Dict[str, str]!;
  failed_step: string;
  start_time: string;
  end_time: string;
  variables: Dict[str, Any]!;
}

entity[name="ExecutionSummary"] {
  total_steps: int!;
  succeeded: int!;
  failed: int!;
  skipped: int!;
  total_duration: float!;
  start_time: string;
  end_time: string;
  status: string!;
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="markpact"] {

}

workflow[name="extract"] {
  trigger: manual;
  step-1: run cmd=sed -n '/^```markpact:bootstrap/,/^```[[:space:]]*$$/p' $(README) | sed '1d;$$d' > markpact.py;
  step-2: run cmd=echo "Extracted markpact.py";
}

workflow[name="run"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) markpact.py $(README);
}

workflow[name="run-port"] {
  trigger: manual;
  step-1: run cmd=MARKPACT_PORT=$(PORT) $(PYTHON) markpact.py $(README);
}

workflow[name="run-cli"] {
  trigger: manual;
  step-1: run cmd=markpact $(README);
}

workflow[name="convert"] {
  trigger: manual;
  step-1: run cmd=markpact $(README) --convert-only;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=rm -rf $(SANDBOX) markpact.py dist/ build/ *.egg-info src/*.egg-info;
  step-2: run cmd=find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true;
  step-3: run cmd=find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true;
  step-4: run cmd=echo "Cleaned all generated files";
}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pip install -e .;
}

workflow[name="dev"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pip install -e ".[dev]";
  step-2: run cmd=$(MAKE) fix-editable;
}

workflow[name="fix-editable"] {
  trigger: manual;
  step-1: run cmd=echo "$(PWD)/src" > .venv/lib/python3.13/site-packages/markpact.pth;
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pytest tests/ -v;
}

workflow[name="test-cov"] {
  trigger: manual;
  step-1: run cmd=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src $(PYTHON) -m pytest tests/ -v --cov=src/markpact --cov-report=term-missing;
}

workflow[name="lint"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m ruff check src/ tests/;
}

workflow[name="format"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m ruff format src/ tests/;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m build;
}

workflow[name="publish-test"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m twine upload --repository testpypi --config-file ~/.pypirc dist/*;
}

workflow[name="publish"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m twine upload dist/*;
}

workflow[name="version"] {
  trigger: manual;
  step-1: run cmd=grep -m1 'version = ' pyproject.toml | cut -d'"' -f2;
}

workflow[name="bump-patch"] {
  trigger: manual;
  step-1: run cmd=bump2version patch --config-file .bumpversion.toml --allow-dirty;
  step-2: run cmd=echo "Bumped to $$(python3 scripts/sync_version.py --get)";
}

workflow[name="bump-minor"] {
  trigger: manual;
  step-1: run cmd=bump2version minor --config-file .bumpversion.toml --allow-dirty;
  step-2: run cmd=echo "Bumped to $$(python3 scripts/sync_version.py --get)";
}

workflow[name="bump-major"] {
  trigger: manual;
  step-1: run cmd=bump2version major --config-file .bumpversion.toml --allow-dirty;
  step-2: run cmd=echo "Bumped to $$(python3 scripts/sync_version.py --get)";
}

workflow[name="sync-version"] {
  trigger: manual;
  step-1: run cmd=python3 scripts/sync_version.py;
}

workflow[name="release"] {
  trigger: manual;
  step-1: depend target=bump-patch;
  step-2: depend target=publish;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  python_version: >=3.10;
}
```

## Interfaces

### CLI Entry Points

- `markpact`

## Workflows

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
pipeline:
  name: markpact-quality

  metrics:
    cc_max: 15
    critical_max: 0

  custom_tools:
    - name: code2llm_markpact
      binary: code2llm
      command: >-
        code2llm {workdir} -f toon -o ./project --no-chunk
        --exclude .git .venv .venv_test build dist __pycache__ .pytest_cache .code2llm_cache .benchmarks .mypy_cache .ruff_cache node_modules
      output: ""
      allow_failure: false

    - name: vallm_markpact
      binary: vallm
      command: >-
        vallm batch {workdir} --recursive --format toon --output ./project
        --exclude .git,.venv,.venv_test,build,dist,__pycache__,.pytest_cache,.code2llm_cache,.benchmarks,.mypy_cache,.ruff_cache,node_modules
      output: ""
      allow_failure: false

  stages:
    - name: analyze
      tool: code2llm_markpact
      optional: true
      timeout: 0

    - name: validate
      tool: vallm_markpact
      optional: true
      timeout: 0

    - name: lint
      tool: ruff
      optional: true

    - name: fix
      tool: prefact
      optional: true
      when: metrics_fail
      timeout: 900

    - name: test
      run: python3 -m pytest -q
      when: always

  loop:
    max_iterations: 3
    on_fail: report

  env:
    LLM_MODEL: openrouter/qwen/qwen3-coder-next
```

## Configuration

```yaml
project:
  name: markpact
  version: 0.1.41
  env: local
```

## Dependencies

### Runtime

```text markpact:deps python
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

### Development

```text markpact:deps python scope=dev
pytest>=7.0
pytest-cov>=4.0
ruff>=0.1
build
twine
bump2version>=1.0
litellm>=1.0
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Deployment

```bash markpact:run
pip install markpact

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Required: OpenRouter API key (https://openrouter.ai/keys) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Model (default: openrouter/qwen/qwen3-coder-next) |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`markpact`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `venv/lib/python3.13/site-packages/matplotlib/__init__.py:__version__`

## Makefile Targets

- `help`
- `extract`
- `run`
- `run-port`
- `run-cli`
- `convert`
- `clean`
- `install`
- `dev`
- `fix-editable`
- `test`
- `test-cov`
- `lint`
- `format`
- `build`
- `publish-test`
- `publish`
- `version` — Version management
- `bump-patch`
- `bump-minor`
- `bump-major`
- `sync-version`
- `release`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# markpact | 69f 14651L | python:65,shell:3,less:1 | 2026-04-23
# stats: 389 func | 91 cls | 69 mod | CC̄=4.5 | critical:30 | cycles:0
# alerts[5]: CC main=24; CC _step_analyze_blocks=20; CC _pdf_analyze=20; CC run_with_auto_fix_llm=18; CC run_service_with_tests=16
# hotspots[5]: main fan=22; run_service_with_tests fan=22; run_live fan=19; _step_analyze_blocks fan=16; _process_readme fan=16
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[69]:
  app.doql.less,196
  examples/demo_live_markpact.py,970
  examples/sandbox/app/main.py,29
  examples/sync-workflow/src/app.py,8
  examples/sync-workflow/src/run.sh,3
  project.sh,40
  scripts/sync_version.py,107
  scripts/test_examples.sh,315
  src/markpact/__init__.py,57
  src/markpact/auto_fix.py,428
  src/markpact/cli/__init__.py,206
  src/markpact/cli/config_cmd.py,75
  src/markpact/cli/convert_cmd.py,113
  src/markpact/cli/helpers.py,67
  src/markpact/cli/pack_cmd.py,63
  src/markpact/cli/publish_cmd.py,96
  src/markpact/cli/run_cmd.py,106
  src/markpact/cli/sync_cmd.py,292
  src/markpact/config.py,205
  src/markpact/converter.py,321
  src/markpact/docker_runner.py,418
  src/markpact/generator.py,363
  src/markpact/notebook_converter.py,711
  src/markpact/packer.py,432
  src/markpact/parser.py,155
  src/markpact/publish/__init__.py,55
  src/markpact/publish/docker_pub.py,109
  src/markpact/publish/github.py,38
  src/markpact/publish/helpers.py,227
  src/markpact/publish/llm_config.py,108
  src/markpact/publish/main.py,111
  src/markpact/publish/models.py,33
  src/markpact/publish/npm.py,101
  src/markpact/publish/pypi.py,446
  src/markpact/publish/version.py,73
  src/markpact/publisher.py,28
  src/markpact/runner.py,43
  src/markpact/runtime/__init__.py,90
  src/markpact/runtime/cli.py,268
  src/markpact/runtime/core.py,297
  src/markpact/runtime/core_v2.py,508
  src/markpact/runtime/core_v3.py,652
  src/markpact/runtime/exceptions.py,54
  src/markpact/runtime/executors.py,506
  src/markpact/runtime/models.py,144
  src/markpact/runtime/parser.py,154
  src/markpact/runtime/plugins.py,284
  src/markpact/runtime/ssh_manager.py,115
  src/markpact/runtime/state.py,177
  src/markpact/runtime/steps.py,104
  src/markpact/sandbox.py,60
  src/markpact/syncer.py,613
  src/markpact/template.py,185
  src/markpact/tester.py,313
  tests/__init__.py,1
  tests/test_auto_fix.py,109
  tests/test_cli.py,152
  tests/test_cli_subcommands.py,190
  tests/test_converter.py,120
  tests/test_examples.py,28
  tests/test_generator.py,131
  tests/test_include.py,182
  tests/test_notebook_converter.py,246
  tests/test_parser.py,102
  tests/test_publish.py,367
  tests/test_runner.py,113
  tests/test_sandbox.py,47
  tests/test_syncer.py,1012
  tests/test_template.py,179
D:
  examples/demo_live_markpact.py:
    e: _ascii,hdr,step,ok,fail,wait,wait_done,info,show_menu,list_prompts,_step_generate_contract,_step_parse_blocks,_step_validate_blocks,_step_analyze_blocks,_step_sha_integrity,_save_outputs,_print_summary,_pdf_generate,_pdf_parse,_pdf_validate,_pdf_analyze,_pdf_sha,_setup_session,_finalize,run_live,_fallback_readme,main,StepRecord,LiveSession
    StepRecord:
    LiveSession: add_step(5),elapsed(0)
    _ascii(text)
    hdr(text)
    step(icon;text)
    ok(text;detail)
    fail(text;detail)
    wait(text)
    wait_done(ok_flag)
    info(text)
    show_menu()
    list_prompts()
    _step_generate_contract(session;config;pdf;prompt)
    _step_parse_blocks(session;readme)
    _step_validate_blocks(session;blocks)
    _step_analyze_blocks(session;blocks)
    _step_sha_integrity(session;readme;blocks)
    _save_outputs(session;pdf;readme;prompt_key)
    _print_summary(session;blocks;readme_path)
    _pdf_generate(pdf;session;config;readme;prompt_key;prompt;dur;readme_path)
    _pdf_parse(pdf;readme;blocks)
    _pdf_validate(pdf;readme;blocks;all_required_ok)
    _pdf_analyze(pdf;readme;blocks;analysis_checks)
    _pdf_sha(pdf;readme;blocks;sha_checks)
    _setup_session(prompt_key;prompt;model)
    _finalize(session;pdf;blocks;readme_path;prompt_key)
    run_live(prompt_key;prompt;model)
    _fallback_readme(prompt)
    main()
  examples/sandbox/app/main.py:
    e: root,health,info
    root()
    health()
    info()
  examples/sync-workflow/src/app.py:
    e: root
    root()
  scripts/sync_version.py:
    e: get_pyproject_version,get_bumpversion_version,set_pyproject_version,set_bumpversion_version,tag_exists,get_next_version,sync_versions
    get_pyproject_version()
    get_bumpversion_version()
    set_pyproject_version(new_ver)
    set_bumpversion_version(new_ver)
    tag_exists(tag)
    get_next_version(current)
    sync_versions()
  src/markpact/__init__.py:
  src/markpact/auto_fix.py:
    e: detect_error_type,fix_port_in_readme,_setup_env_with_venv_simple,_run_and_print,_handle_port_error_simple,run_with_auto_fix,add_missing_dependency,extract_module_name,fix_with_llm,_setup_env_with_venv,_run_subprocess,_handle_port_error,_handle_missing_module_error,_try_llm_fix,run_with_auto_fix_llm
    detect_error_type(error_output;exit_code;cmd)
    fix_port_in_readme(readme_path;new_port)
    _setup_env_with_venv_simple(sandbox)
    _run_and_print(cmd;sandbox;env;verbose)
    _handle_port_error_simple(cmd;env;readme_path)
    run_with_auto_fix(cmd;sandbox;readme_path;verbose;max_retries)
    add_missing_dependency(readme_path;module_name)
    extract_module_name(error_output)
    fix_with_llm(readme_path;error_output;error_type;verbose)
    _setup_env_with_venv(sandbox)
    _run_subprocess(cmd;sandbox;env)
    _handle_port_error(cmd;env;readme_path;verbose)
    _handle_missing_module_error(error_output;sandbox;readme_path;verbose)
    _try_llm_fix(error_type;error_output;readme_path;verbose)
    run_with_auto_fix_llm(cmd;sandbox;readme_path;verbose;max_retries;use_llm)
  src/markpact/cli/__init__.py:
    e: main,_dispatch_subcommand,_parse_main_args,_handle_generation_phase,_process_readme
    main(argv)
    _dispatch_subcommand(cmd;argv)
    _parse_main_args(args_list)
    _handle_generation_phase(args;verbose)
    _process_readme(args;readme;verbose)
  src/markpact/cli/config_cmd.py:
    e: handle_config_cli
    handle_config_cli(argv)
  src/markpact/cli/convert_cmd.py:
    e: _handle_list_examples,_handle_list_notebook_formats,_handle_from_notebook,_handle_llm_generation,_handle_markdown_conversion
    _handle_list_examples(verbose)
    _handle_list_notebook_formats(verbose)
    _handle_from_notebook(args;verbose)
    _handle_llm_generation(args;verbose)
    _handle_markdown_conversion(args;original_text;verbose)
  src/markpact/cli/helpers.py:
    e: _resolve_file_body,_parse_blocks_to_state
    _resolve_file_body(block;verbose)
    _parse_blocks_to_state(blocks;sandbox;args;verbose)
  src/markpact/cli/pack_cmd.py:
    e: handle_pack_cli
    handle_pack_cli(argv)
  src/markpact/cli/publish_cmd.py:
    e: _resolve_publish_config,_determine_bump_type,_print_publish_dry_run,_execute_publish_result,_handle_publish_mode
    _resolve_publish_config(args;text_to_parse;readme;blocks;run_command;verbose)
    _determine_bump_type(args)
    _print_publish_dry_run(config;bump_type)
    _execute_publish_result(result;readme;bump_type;verbose)
    _handle_publish_mode(args;config;sandbox;readme;text_to_parse;blocks;run_command;verbose)
  src/markpact/cli/run_cmd.py:
    e: _handle_docker_mode,_print_dry_run_tests,_split_test_blocks,_run_http_tests,_run_shell_tests,_handle_test_mode,_handle_normal_run
    _handle_docker_mode(args;sandbox;deps;run_command;verbose)
    _print_dry_run_tests(test_blocks)
    _split_test_blocks(test_blocks)
    _run_http_tests(run_command;http_tests;sandbox;port;verbose;test_only)
    _run_shell_tests(shell_tests;sandbox;verbose)
    _handle_test_mode(args;sandbox;run_command;test_blocks;deps;verbose)
    _handle_normal_run(args;sandbox;run_command;deps;readme;verbose)
  src/markpact/cli/sync_cmd.py:
    e: _build_sync_parser,_resolve_paths,_handle_backups_mode,_handle_rollback_mode,_handle_list_mode,_handle_missing_mode,_handle_add_mode,_execute_recursive_sync,_show_diffs,_execute_single_sync,handle_sync_cli
    _build_sync_parser()
    _resolve_paths(args)
    _handle_backups_mode(readme_path)
    _handle_rollback_mode(args;readme_path;verbose)
    _handle_list_mode(text;source_dir)
    _handle_missing_mode(text;source_dir)
    _handle_add_mode(args;readme_path;source_dir;verbose)
    _execute_recursive_sync(args;readme_path;source_dir;exclude_sync;dry_run;verbose)
    _show_diffs(result;text;readme_path;source_dir;dry_run)
    _execute_single_sync(args;readme_path;source_dir;text;exclude_sync;dry_run;verbose)
    handle_sync_cli(argv)
  src/markpact/config.py:
    e: get_env_path,ensure_config_dir,load_env,save_env,init_env,set_config,set_model,set_api_key,set_api_base,apply_preset,show_config,list_providers
    get_env_path()
    ensure_config_dir()
    load_env()
    save_env(config)
    init_env(force)
    set_config(key;value)
    set_model(model)
    set_api_key(api_key)
    set_api_base(api_base)
    apply_preset(provider;api_key)
    show_config()
    list_providers()
  src/markpact/converter.py:
    e: _detect_deps,_detect_run,_detect_file,detect_block_type,suggest_filename,convert_markdown_to_markpact,_print_conversion_header,_print_block_changes,_print_conversion_summary,print_conversion_report,ConvertedBlock,ConversionResult
    ConvertedBlock:  # A converted markpact block.
    ConversionResult:  # Result of converting a Markdown file.
    _detect_deps(lang;body;body_lower)
    _detect_run(lang;first_lines)
    _detect_file(first_lines;lang)
    detect_block_type(lang;body)
    suggest_filename(lang;body;index)
    convert_markdown_to_markpact(text;verbose)
    _print_conversion_header()
    _print_block_changes(changes)
    _print_conversion_summary(blocks)
    print_conversion_report(result)
  src/markpact/docker_runner.py:
    e: stop_existing_container,generate_dockerfile,is_port_free,_build_docker_image_simple,_find_docker_port,_run_docker_container_interactive,build_and_run_docker,check_docker_available,run_docker_with_logs,stream_docker_logs,_build_docker_image,_resolve_docker_port,_start_docker_container,_run_docker_tests,_stop_docker_container,run_docker_with_tests
    stop_existing_container(container_name;verbose)
    generate_dockerfile(sandbox_path;deps;run_command)
    is_port_free(port)
    _build_docker_image_simple(sandbox_path;image_name;verbose)
    _find_docker_port(port;auto_find_port;verbose)
    _run_docker_container_interactive(sandbox_path;image_name;container_name;current_port;verbose)
    build_and_run_docker(sandbox_path;image_name;port;verbose;auto_find_port)
    check_docker_available()
    run_docker_with_logs(sandbox_path;image_name;port;follow_logs;verbose;auto_find_port)
    stream_docker_logs(process;timeout)
    _build_docker_image(sandbox_path;image_name;verbose)
    _resolve_docker_port(port;auto_find_port;verbose)
    _start_docker_container(sandbox_path;image_name;current_port;verbose)
    _run_docker_tests(test_body;current_port;verbose)
    _stop_docker_container(container_name;process;verbose)
    run_docker_with_tests(sandbox_path;test_body;image_name;port;verbose;auto_find_port)
  src/markpact/generator.py:
    e: _fix_unclosed_blocks,_configure_litellm,_set_provider_api_key,_call_llm_with_config,_clean_llm_response,generate_contract,save_contract,get_example_prompt,list_example_prompts,GeneratorConfig
    GeneratorConfig: from_env(1),from_file(2)  # Configuration for LLM generator
    _fix_unclosed_blocks(content)
    _configure_litellm(config;verbose)
    _set_provider_api_key(model;api_key)
    _call_llm_with_config(config;messages)
    _clean_llm_response(content)
    generate_contract(prompt;config;verbose)
    save_contract(content;output_path;verbose)
    get_example_prompt(name)
    list_example_prompts()
  src/markpact/notebook_converter.py:
    e: detect_format,parse_jupyter,_parse_rmd_yaml_front_matter,_parse_rmd_code_chunks,_extract_description_from_cells,parse_rmarkdown,_parse_quarto_yaml_front_matter,_parse_quarto_code_chunks,parse_quarto,parse_zeppelin,parse_databricks,parse_notebook,extract_dependencies,suggest_run_command,_generate_header,_extract_and_format_deps,_should_skip_first_markdown_cell,_extract_markdown_section,_extract_file_hint,_process_notebook_cells,_merge_code_files,_generate_file_blocks,notebook_to_markpact,convert_notebook,get_supported_formats,NotebookCell,Notebook
    NotebookCell:  # Represents a cell in a notebook.
    Notebook:  # Represents a parsed notebook.
    detect_format(path)
    parse_jupyter(path)
    _parse_rmd_yaml_front_matter(content;default_title)
    _parse_rmd_code_chunks(content)
    _extract_description_from_cells(cells)
    parse_rmarkdown(path)
    _parse_quarto_yaml_front_matter(content;default_title)
    _parse_quarto_code_chunks(content)
    parse_quarto(path)
    parse_zeppelin(path)
    parse_databricks(path)
    parse_notebook(path)
    extract_dependencies(notebook)
    suggest_run_command(notebook)
    _generate_header(notebook;output_path)
    _extract_and_format_deps(notebook)
    _should_skip_first_markdown_cell(cell;notebook;skip_first_title)
    _extract_markdown_section(cell)
    _extract_file_hint(source)
    _process_notebook_cells(notebook)
    _merge_code_files(code_cells)
    _generate_file_blocks(merged_files;notebook)
    notebook_to_markpact(notebook;output_path;verbose)
    convert_notebook(input_path;output_path;verbose)
    get_supported_formats()
  src/markpact/packer.py:
    e: _should_include,_get_language,_detect_file_indicators,_detect_framework_from_content,_build_run_command,_detect_run_command,_collect_files,_generate_readme_content,_write_output,pack_directory,print_pack_report,PackResult
    PackResult: summary(0)  # Result of packing a directory.
    _should_include(path;exclude_patterns)
    _get_language(path)
    _detect_file_indicators(files)
    _detect_framework_from_content(files)
    _build_run_command(indicators;has_fastapi;has_flask)
    _detect_run_command(files)
    _collect_files(src;output_path;exclude_patterns;include_patterns;verbose)
    _generate_readme_content(files_to_pack;src;project_title;desc;run_command;dry_run)
    _write_output(output_path;lines;files_to_pack;dry_run;verbose)
    pack_directory(source_dir;output)
    print_pack_report(result)
  src/markpact/parser.py:
    e: parse_blocks,parse_blocks_recursive,Block
    Block: get_path(0),get_meta_value(1)
    parse_blocks(text)
    parse_blocks_recursive(text)
  src/markpact/publish/__init__.py:
  src/markpact/publish/docker_pub.py:
    e: generate_dockerfile,publish_docker
    generate_dockerfile(config;sandbox;base_image)
    publish_docker(config;sandbox;registry;tag;verbose)
  src/markpact/publish/github.py:
    e: publish_github_packages
    publish_github_packages(config;sandbox;package_type;verbose)
  src/markpact/publish/helpers.py:
    e: _slugify,_first_heading,_first_paragraph,_format_subprocess_failure,_check_file_type,_analyze_blocks_for_types,_is_web_service,_detect_registry,_build_package_name,_get_default_author,infer_publish_config,prompt_publish_config,ensure_publish_block_in_readme
    _slugify(name)
    _first_heading(markdown)
    _first_paragraph(markdown)
    _format_subprocess_failure(result)
    _check_file_type(path)
    _analyze_blocks_for_types(blocks)
    _is_web_service(run_command)
    _detect_registry(flags;run_command)
    _build_package_name(base_name;registry)
    _get_default_author()
    infer_publish_config(readme_path;markdown;blocks;run_command)
    prompt_publish_config(config)
    ensure_publish_block_in_readme(readme_path;config)
  src/markpact/publish/llm_config.py:
    e: _setup_llm_for_publish,_set_provider_api_key_for_publish,_call_llm_for_publish_config,_extract_publish_block_from_response,generate_publish_config_with_llm
    _setup_llm_for_publish()
    _set_provider_api_key_for_publish(cfg)
    _call_llm_for_publish_config(litellm;cfg;markdown)
    _extract_publish_block_from_response(content)
    generate_publish_config_with_llm(markdown;verbose)
  src/markpact/publish/main.py:
    e: parse_publish_block,publish
    parse_publish_block(block_body;meta)
    publish(config;sandbox;bump;verbose;source_readme_path)
  src/markpact/publish/models.py:
    e: PublishConfig,PublishResult
    PublishConfig: __post_init__(0)  # Configuration for publishing
    PublishResult:  # Result of a publish operation
  src/markpact/publish/npm.py:
    e: _build_npm_description,generate_package_json,publish_npm
    _build_npm_description(config;sandbox)
    generate_package_json(config;sandbox)
    publish_npm(config;sandbox;registry;verbose)
  src/markpact/publish/pypi.py:
    e: get_license_classifier,_extract_readme_description,_build_description,generate_pyproject_toml,_normalize_package_name,_determine_base_path,_detect_build_backend,_ensure_build_backend,_copy_readme,_run_build_command,_print_build_output,_get_build_error_hint,_build_package,_setup_env_creds,_parse_pypirc_section,_check_pypi_credentials,_setup_upload_env,_build_upload_cmd,_get_upload_error_hint,_upload_to_pypi,publish_pypi
    get_license_classifier(license_name)
    _extract_readme_description(base_path)
    _build_description(config;base_path)
    generate_pyproject_toml(config;sandbox;base_path;verbose)
    _normalize_package_name(config;verbose)
    _determine_base_path(config;sandbox;verbose)
    _detect_build_backend(pyproject_path)
    _ensure_build_backend(build_backend;verbose)
    _copy_readme(source_readme_path;base_path;config;verbose)
    _run_build_command(base_path)
    _print_build_output(build_result)
    _get_build_error_hint(stdout;stderr)
    _build_package(base_path;verbose)
    _setup_env_creds(test)
    _parse_pypirc_section(pypirc_path;test;verbose)
    _check_pypi_credentials(test;verbose)
    _setup_upload_env(test)
    _build_upload_cmd(test;pypirc_path;verbose)
    _get_upload_error_hint(payload;stdout;test;config)
    _upload_to_pypi(base_path;test;config;pypirc_path;verbose)
    publish_pypi(config;sandbox;test;verbose;source_readme_path)
  src/markpact/publish/version.py:
    e: bump_version,extract_version_from_readme,update_version_in_readme
    bump_version(version;bump_type)
    extract_version_from_readme(readme_path)
    update_version_in_readme(readme_path;new_version)
  src/markpact/publisher.py:
  src/markpact/runner.py:
    e: run_cmd,ensure_venv,install_deps
    run_cmd(cmd;sandbox;verbose)
    ensure_venv(sandbox;verbose)
    install_deps(deps;sandbox;verbose)
  src/markpact/runtime/__init__.py:
  src/markpact/runtime/cli.py:
    e: main
    main()
  src/markpact/runtime/core.py:
    e: RuntimeConfig,Runtime
    RuntimeConfig:  # Configuration for the runtime.
    Runtime: __init__(2),_load_plugins(0),parse(0),execute(1),_process_blocks(1),_process_config(1),_process_steps(1),_process_run_block(1),_execute_step(1),_print_summary(0),set_variable(2),get_variable(2)  # Main runtime for executing markpact markdown files.
  src/markpact/runtime/core_v2.py:
    e: RuntimeConfig,RuntimeV2
    RuntimeConfig:  # Configuration for the runtime.
    RuntimeV2: __init__(2),_load_plugins(0),parse(0),execute(1),_should_run_step(1),_execute_step_with_retry(1),_execute_step_single(2),_rollback(1),_get_ssh_manager(2),_process_blocks(1),_process_python_block(1),_process_bash_block(1),_process_run_block(1),_process_config(1),_process_steps(1),_process_rollback(1),_print_summary(0),reset_state(0),close(0)  # Production-grade runtime for executing markpact deployments.
  src/markpact/runtime/core_v3.py:
    e: RuntimeConfigV3,StepExecutionRecord,FactsGatherer,RuntimeV3
    RuntimeConfigV3: __init__(10)  # Configuration for RuntimeV3.
    StepExecutionRecord:  # Record of executed step for rollback stack.
    FactsGatherer: __init__(1),clear_cache(0),check(1),_eval_condition(1),_check_docker_installed(0),_check_container_running(1),_check_file_exists(1),_check_dir_exists(1),_check_command_succeeds(1)  # Gathers current state facts from target host.
    RuntimeV3: __init__(2),parse(0),_process_blocks(1),_load_config(1),_load_steps(1),_load_rollback(1),plan(0),reconcile(1),_should_execute(1),_compute_step_hash(1),_execute_step_with_retry(1),_execute_step(1),_get_ssh_manager(2),_exec_remote(2),_rollback(1),_filter_steps(2),close(0),__enter__(0),__exit__(3)  # Markpact Runtime v3: State Reconciliation Engine
  src/markpact/runtime/exceptions.py:
    e: MarkpactError,ParseError,ExecutionError,PluginError,ValidationError,TimeoutError,ConnectionError,RollbackError
    MarkpactError:  # Base exception for all markpact errors.
    ParseError: __init__(2)  # Error parsing markpact file.
    ExecutionError: __init__(2)  # Error executing a step.
    PluginError: __init__(2)  # Error with plugin loading or execution.
    ValidationError:  # Error validating configuration or steps.
    TimeoutError: __init__(2)  # Step execution timed out.
    ConnectionError:  # Error connecting to remote host.
    RollbackError: __init__(2)  # Error during rollback.
  src/markpact/runtime/executors.py:
    e: Executor,ShellExecutor,SSHCmdExecutor,RsyncExecutor,ScpExecutor,DockerExecutor,HttpExecutor,PluginExecutor,PythonExecutor,BashExecutor,ExecutorRegistry
    Executor: name(0),execute(2),validate(1)  # Base class for action executors.
    ShellExecutor: name(0),execute(2),_run_local(2),_run_ssh_persistent(4),_run_ssh_subprocess(4)  # Execute shell commands locally or via SSH with persistent se
    SSHCmdExecutor: name(0)  # Alias for shell executor with explicit SSH.
    RsyncExecutor: name(0),execute(2)  # Execute rsync operations.
    ScpExecutor: name(0),execute(2)  # Execute SCP copy operations.
    DockerExecutor: name(0),execute(2),_compose_up(2),_compose_down(2),_wait_healthy(2),_run_local(3),_run_ssh(4)  # Execute Docker Compose operations.
    HttpExecutor: name(0),execute(2)  # Execute HTTP health checks.
    PluginExecutor: name(0),execute(2)  # Execute custom plugin actions.
    PythonExecutor: name(0),execute(2)  # Execute Python code blocks.
    BashExecutor: name(0),execute(2)  # Execute Bash/shell scripts.
    ExecutorRegistry: __init__(0),_register_defaults(0),register(1),get(1),list(0)  # Registry of available executors.
  src/markpact/runtime/models.py:
    e: Step,DeploymentConfig,DeployState,StepResult,ExecutionSummary
    Step: validate_risk(2),positive_int(2),from_dict(2),to_dict(0)  # Pydantic-validated deployment step.
    DeploymentConfig:  # Deployment configuration with validation.
    DeployState:  # Deployment state for idempotency tracking.
    StepResult: success(0),failed(0)  # Result of step execution with structured logging.
    ExecutionSummary:  # Summary of full deployment execution.
  src/markpact/runtime/parser.py:
    e: BlockType,Block,MarkpactParser
    BlockType:  # Types of markpact blocks.
    Block:  # A parsed markpact block.
    MarkpactParser: __init__(0),parse(1),_parse_block_type(1),get_blocks_by_type(1),get_first_block(1)  # Parser for markpact markdown files.
  src/markpact/runtime/plugins.py:
    e: Plugin,PluginLoader,BrowserReloadPlugin
    Plugin: name(0),version(0),execute(2),initialize(1),shutdown(0)  # Base class for plugins.
    PluginLoader: __init__(0),load_from_path(1),load_from_module(1),_load_from_directory(1),_load_from_file(1),_extract_plugin_from_module(2),get(1),list(0),get_all(0),clear(0)  # Loads plugins from various sources.
    BrowserReloadPlugin: name(0),version(0),execute(2)  # Plugin to reload browser via CDP (Chrome DevTools Protocol).
  src/markpact/runtime/ssh_manager.py:
    e: get_ssh_manager,SSHSessionManager
    SSHSessionManager: __init__(3),connect(0),exec_command(2),close(0),session(0),__del__(0)  # Manages persistent SSH sessions for performance.
    get_ssh_manager(host;user;key_file)
  src/markpact/runtime/state.py:
    e: StateManager,ConditionChecker
    StateManager: __init__(1),_load(0),_save(0),is_step_done(1),mark_step_done(1),mark_failed(1),clear_failed(0),start_deployment(0),end_deployment(1),reset(0),set_variable(2),get_variable(2)  # Manages deployment state for idempotency.
    ConditionChecker: __init__(1),check_when(1),check_skip_if(1),_is_docker_running(0),_is_container_running(1)  # Check step conditions (when/skip_if).
  src/markpact/runtime/steps.py:
    e: StepStatus,Step,StepResult
    StepStatus:  # Status of step execution.
    Step: from_dict(2),to_dict(0)  # A deployment step.
    StepResult: success(0),__str__(0)  # Result of step execution.
  src/markpact/sandbox.py:
    e: find_free_port,Sandbox
    Sandbox: __init__(1),venv_bin(0),venv_pip(0),venv_python(0),has_venv(0),write_file(2),write_requirements(1),clean(0)  # Manages sandbox directory for markpact execution
    find_free_port(start_port;max_attempts)
  src/markpact/syncer.py:
    e: _backup_dir,create_backup,list_backups,restore_backup,_prune_backups,list_tracked_paths,find_untracked_files,diff_block,_content_sha256,_build_header_suffix,_read_source_file,_process_block,sync_readme,sync_readme_recursive,_detect_lang,_build_block,_collect_untracked_blocks,_write_new_blocks,add_untracked_blocks,print_sync_report,SyncResult
    SyncResult: summary(0)  # Result of a sync operation.
    _backup_dir(readme_path)
    create_backup(readme_path)
    list_backups(readme_path)
    restore_backup(readme_path;backup_path)
    _prune_backups(bak_dir)
    list_tracked_paths(text)
    find_untracked_files(text;source_dir)
    diff_block(rel_path;old_body;new_body)
    _content_sha256(body)
    _build_header_suffix(rest_of_header;new_body;hash_blocks)
    _read_source_file(src;rel_path)
    _process_block(m)
    sync_readme(readme_path;source_dir)
    sync_readme_recursive(readme_path;source_dir)
    _detect_lang(rel_path)
    _build_block(rel_path;content)
    _collect_untracked_blocks(src;paths;tracked)
    _write_new_blocks(readme;text;new_blocks)
    add_untracked_blocks(readme_path;source_dir;paths)
    print_sync_report(result)
  src/markpact/template.py:
    e: _find_secrets_file,load_secrets,_prompt_value,resolve_template,has_template_placeholders
    _find_secrets_file(project_dir)
    load_secrets(project_dir)
    _prompt_value(label;default)
    resolve_template(body)
    has_template_placeholders(body)
  src/markpact/tester.py:
    e: wait_for_service,http_request,run_http_test,run_tests_from_block,run_service_with_tests,run_shell_tests,TestResult,TestSuite
    TestResult:  # Result of a single test
    TestSuite: passed(0),failed(0),total(0),print_summary(0)  # Collection of test results
    wait_for_service(url;timeout;interval)
    http_request(method;url;data;headers;timeout)
    run_http_test(test_spec;base_url)
    run_tests_from_block(test_body;base_url)
    run_service_with_tests(run_command;test_body;sandbox;port;verbose)
    run_shell_tests(test_body;sandbox;verbose)
  tests/__init__.py:
  tests/test_auto_fix.py:
    e: TestDetectErrorType,TestFixPortInReadme,TestExtractModuleName,TestAddMissingDependency
    TestDetectErrorType: test_port_in_use(0),test_missing_module(0),test_syntax_error(0),test_import_error(0),test_unknown_error(0),test_case_insensitive(0),test_empty_output(0)
    TestFixPortInReadme: test_replaces_env_var_port(1),test_replaces_direct_port(1),test_no_port_returns_false(1)
    TestExtractModuleName: test_single_module(0),test_dotted_module(0),test_double_quotes(0),test_no_match(0)
    TestAddMissingDependency: test_adds_to_deps_block(1),test_already_present(1),test_no_deps_block(1)
  tests/test_cli.py:
    e: test_cli_help,test_cli_version,test_cli_file_not_found,test_cli_dry_run,test_cli_dry_run_new_header,test_cli_convert_only,test_cli_auto_no_markpact,test_cli_save_converted,test_cli_quiet_mode
    test_cli_help(capsys)
    test_cli_version(capsys)
    test_cli_file_not_found(capsys)
    test_cli_dry_run()
    test_cli_dry_run_new_header()
    test_cli_convert_only(capsys)
    test_cli_auto_no_markpact(capsys)
    test_cli_save_converted()
    test_cli_quiet_mode()
  tests/test_cli_subcommands.py:
    e: TestDispatch,TestParseMainArgs,TestSyncSubcommand,TestPackSubcommand,TestMainIntegration
    TestDispatch: test_config_subcommand(1),test_unknown_subcommand_falls_through(0),test_dispatch_returns_1_for_unknown(0)
    TestParseMainArgs: test_defaults(0),test_dry_run(0),test_quiet(0),test_publish_with_bump(0),test_custom_readme(0),test_recursive_flag(0),test_docker_flag(0),test_test_flag(0)
    TestSyncSubcommand: test_sync_basic(1),test_sync_dry_run(2),test_sync_nonexistent_file(0),test_sync_list_tracked(2)
    TestPackSubcommand: test_pack_basic(1),test_pack_dry_run(2),test_pack_nonexistent(0)
    TestMainIntegration: test_dry_run_with_markpact_blocks(1),test_recursive_dry_run(1),test_quiet_mode_suppresses_parsing(2)
  tests/test_converter.py:
    e: test_detect_deps_python,test_detect_deps_with_versions,test_detect_file_python,test_detect_file_javascript,test_detect_run_command,test_detect_run_python,test_suggest_filename_fastapi,test_suggest_filename_class,test_suggest_filename_html,test_convert_simple_markdown,test_convert_already_markpact,test_convert_preserves_non_code
    test_detect_deps_python()
    test_detect_deps_with_versions()
    test_detect_file_python()
    test_detect_file_javascript()
    test_detect_run_command()
    test_detect_run_python()
    test_suggest_filename_fastapi()
    test_suggest_filename_class()
    test_suggest_filename_html()
    test_convert_simple_markdown()
    test_convert_already_markpact()
    test_convert_preserves_non_code()
  tests/test_examples.py:
    e: test_examples_dry_run
    test_examples_dry_run(tmp_path)
  tests/test_generator.py:
    e: test_generator_config_defaults,test_generator_config_from_env,test_get_example_prompt,test_get_example_prompt_unknown,test_list_example_prompts,test_system_prompt_contains_format,test_example_prompts_dict,test_generate_contract_integration,test_generate_contract_mock
    test_generator_config_defaults()
    test_generator_config_from_env()
    test_get_example_prompt()
    test_get_example_prompt_unknown()
    test_list_example_prompts()
    test_system_prompt_contains_format()
    test_example_prompts_dict()
    test_generate_contract_integration()
    test_generate_contract_mock()
  tests/test_include.py:
    e: TestParseBlocksRecursive,TestBlockSourceFile
    TestParseBlocksRecursive: test_no_includes(0),test_single_include(1),test_nested_includes(1),test_circular_include_detected(1),test_missing_include_skipped(1),test_max_depth(1),test_source_file_tracking(1)  # Test recursive include resolution.
    TestBlockSourceFile: test_default_none(0),test_explicit_source(0)  # Test that source_file is set on blocks.
  tests/test_notebook_converter.py:
    e: test_detect_format_jupyter,test_detect_format_rmarkdown,test_detect_format_quarto,test_detect_format_unknown,test_get_supported_formats,test_parse_jupyter,test_extract_dependencies,test_suggest_run_command_fastapi,test_suggest_run_command_streamlit,test_suggest_run_command_flask,test_notebook_to_markpact,test_convert_notebook_jupyter,test_convert_notebook_file_not_found,test_convert_notebook_unsupported_format
    test_detect_format_jupyter()
    test_detect_format_rmarkdown()
    test_detect_format_quarto()
    test_detect_format_unknown()
    test_get_supported_formats()
    test_parse_jupyter(tmp_path)
    test_extract_dependencies()
    test_suggest_run_command_fastapi()
    test_suggest_run_command_streamlit()
    test_suggest_run_command_flask()
    test_notebook_to_markpact()
    test_convert_notebook_jupyter(tmp_path)
    test_convert_notebook_file_not_found()
    test_convert_notebook_unsupported_format(tmp_path)
  tests/test_parser.py:
    e: test_parse_file_block,test_parse_file_block_new_header,test_parse_deps_block,test_parse_deps_block_new_header,test_parse_run_block,test_parse_run_block_new_header,test_parse_multiple_blocks,test_empty_meta
    test_parse_file_block()
    test_parse_file_block_new_header()
    test_parse_deps_block()
    test_parse_deps_block_new_header()
    test_parse_run_block()
    test_parse_run_block_new_header()
    test_parse_multiple_blocks()
    test_empty_meta()
  tests/test_publish.py:
    e: TestPublishConfig,TestPublishResult,TestBumpVersion,TestExtractVersionFromReadme,TestUpdateVersionInReadme,TestParsePublishBlock,TestPublishDispatch,TestSlugify,TestFirstHeading,TestFirstParagraph,TestFormatSubprocessFailure,TestCheckFileType,TestIsWebService,TestDetectRegistry,TestBuildPackageName,TestInferPublishConfig,TestEnsurePublishBlock
    TestPublishConfig: test_defaults(0),test_keywords_none_defaults_to_list(0),test_keywords_preserved(0)
    TestPublishResult: test_success_result(0),test_failure_result(0)
    TestBumpVersion: test_patch(0),test_minor(0),test_major(0),test_v_prefix(0),test_default_is_patch(0),test_invalid_version_resets(0),test_prerelease_stripped(0),test_zero_version(0)
    TestExtractVersionFromReadme: test_from_publish_block(1),test_from_pyproject_style(1),test_fallback_default(1),test_colon_syntax(1)
    TestUpdateVersionInReadme: test_updates_version(1),test_no_version_returns_false(1)
    TestParsePublishBlock: test_basic_equals_syntax(0),test_colon_syntax(0),test_ignores_comments(0),test_keywords_split(0),test_meta_line(0),test_defaults(0),test_quoted_values_stripped(0),test_unknown_keys_ignored(0)
    TestPublishDispatch: test_unknown_registry(1),test_bump_before_publish(1)
    TestSlugify: test_basic(0),test_special_chars(0),test_empty(0),test_leading_trailing(0)
    TestFirstHeading: test_found(0),test_not_found(0),test_second_heading_ignored(0)
    TestFirstParagraph: test_found(0),test_multiline(0),test_no_paragraph(0)
    TestFormatSubprocessFailure: test_stderr(0),test_empty(0),test_truncation(0)
    TestCheckFileType: test_python(0),test_js(0),test_dockerfile(0)
    TestIsWebService: test_uvicorn(0),test_flask(0),test_not_web(0),test_none(0)
    TestDetectRegistry: test_npm_from_js(0),test_docker_from_web(0),test_pypi_from_pyproject(0)
    TestBuildPackageName: test_pypi_prefix(0),test_already_prefixed(0)
    TestInferPublishConfig: test_basic_inference(1)
    TestEnsurePublishBlock: test_inserts_block(1),test_no_duplicate(1),test_inserts_before_deps(1)
  tests/test_runner.py:
    e: test_run_cmd_simple,test_run_cmd_with_venv,test_ensure_venv_creates_venv,test_ensure_venv_skips_if_disabled,test_ensure_venv_skips_if_exists,test_install_deps_empty,test_install_deps_writes_requirements
    test_run_cmd_simple()
    test_run_cmd_with_venv()
    test_ensure_venv_creates_venv()
    test_ensure_venv_skips_if_disabled()
    test_ensure_venv_skips_if_exists()
    test_install_deps_empty()
    test_install_deps_writes_requirements()
  tests/test_sandbox.py:
    e: test_sandbox_creation,test_write_file,test_write_requirements,test_venv_paths,test_clean
    test_sandbox_creation()
    test_write_file()
    test_write_requirements()
    test_venv_paths()
    test_clean()
  tests/test_syncer.py:
    e: test_list_tracked_old_format,test_list_tracked_new_format,test_list_tracked_mixed_formats,test_list_tracked_empty,test_find_untracked,test_find_untracked_excludes_dirs,test_find_untracked_nonexistent_dir,test_sync_updates_old_format,test_sync_updates_new_format,test_sync_unchanged,test_sync_missing_source_file,test_sync_excluded_file,test_sync_dry_run,test_sync_multiple_files,test_sync_preserves_surrounding_text,test_sync_nonexistent_readme,test_sync_nonexistent_source_dir,test_diff_block_shows_changes,test_diff_block_identical,test_create_backup,test_create_backup_nonexistent,test_create_backup_prunes_old,test_list_backups_empty,test_list_backups_ordered,test_restore_latest,test_restore_specific,test_restore_no_backups,test_restore_nonexistent_backup,test_sync_creates_backup_on_update,test_sync_no_backup_when_unchanged,test_sync_then_rollback,test_sync_hash_blocks_adds_sha256,test_sync_hash_blocks_updates_existing_sha,test_sync_hash_blocks_preserves_other_meta,test_sync_no_hash_by_default,test_sync_recursive_single_readme,test_sync_recursive_with_sub_readme,test_sync_recursive_dry_run,test_sync_recursive_circular,test_sync_recursive_with_hash,test_sync_cli_recursive_hash,test_sync_cli_check_recursive_detects_drift,test_detect_lang_python,test_detect_lang_yaml,test_detect_lang_bash,test_detect_lang_env,test_detect_lang_dockerfile,test_detect_lang_makefile,test_detect_lang_container,test_detect_lang_unknown,test_detect_lang_nested_path,test_add_untracked_blocks_basic,test_add_untracked_blocks_detects_lang,test_add_untracked_blocks_skips_already_tracked,test_add_untracked_blocks_skips_missing_files,test_add_untracked_blocks_dry_run,test_add_untracked_blocks_creates_backup,test_add_untracked_blocks_empty_paths,test_sync_cli_add_all_untracked,test_sync_cli_add_specific_files,test_sync_cli_add_dry_run,test_sync_cli_add_then_sync
    test_list_tracked_old_format()
    test_list_tracked_new_format()
    test_list_tracked_mixed_formats()
    test_list_tracked_empty()
    test_find_untracked(tmp_path)
    test_find_untracked_excludes_dirs(tmp_path)
    test_find_untracked_nonexistent_dir()
    test_sync_updates_old_format(tmp_path)
    test_sync_updates_new_format(tmp_path)
    test_sync_unchanged(tmp_path)
    test_sync_missing_source_file(tmp_path)
    test_sync_excluded_file(tmp_path)
    test_sync_dry_run(tmp_path)
    test_sync_multiple_files(tmp_path)
    test_sync_preserves_surrounding_text(tmp_path)
    test_sync_nonexistent_readme(tmp_path)
    test_sync_nonexistent_source_dir(tmp_path)
    test_diff_block_shows_changes()
    test_diff_block_identical()
    test_create_backup(tmp_path)
    test_create_backup_nonexistent(tmp_path)
    test_create_backup_prunes_old(tmp_path)
    test_list_backups_empty(tmp_path)
    test_list_backups_ordered(tmp_path)
    test_restore_latest(tmp_path)
    test_restore_specific(tmp_path)
    test_restore_no_backups(tmp_path)
    test_restore_nonexistent_backup(tmp_path)
    test_sync_creates_backup_on_update(tmp_path)
    test_sync_no_backup_when_unchanged(tmp_path)
    test_sync_then_rollback(tmp_path)
    test_sync_hash_blocks_adds_sha256(tmp_path)
    test_sync_hash_blocks_updates_existing_sha(tmp_path)
    test_sync_hash_blocks_preserves_other_meta(tmp_path)
    test_sync_no_hash_by_default(tmp_path)
    test_sync_recursive_single_readme(tmp_path)
    test_sync_recursive_with_sub_readme(tmp_path)
    test_sync_recursive_dry_run(tmp_path)
    test_sync_recursive_circular(tmp_path)
    test_sync_recursive_with_hash(tmp_path)
    test_sync_cli_recursive_hash(tmp_path)
    test_sync_cli_check_recursive_detects_drift(tmp_path)
    test_detect_lang_python()
    test_detect_lang_yaml()
    test_detect_lang_bash()
    test_detect_lang_env()
    test_detect_lang_dockerfile()
    test_detect_lang_makefile()
    test_detect_lang_container()
    test_detect_lang_unknown()
    test_detect_lang_nested_path()
    test_add_untracked_blocks_basic(tmp_path)
    test_add_untracked_blocks_detects_lang(tmp_path)
    test_add_untracked_blocks_skips_already_tracked(tmp_path)
    test_add_untracked_blocks_skips_missing_files(tmp_path)
    test_add_untracked_blocks_dry_run(tmp_path)
    test_add_untracked_blocks_creates_backup(tmp_path)
    test_add_untracked_blocks_empty_paths(tmp_path)
    test_sync_cli_add_all_untracked(tmp_path)
    test_sync_cli_add_specific_files(tmp_path)
    test_sync_cli_add_dry_run(tmp_path)
    test_sync_cli_add_then_sync(tmp_path)
  tests/test_template.py:
    e: TestHasTemplatePlaceholders,TestResolveTemplate,TestLoadSecrets,TestFindSecretsFile
    TestHasTemplatePlaceholders: test_ask_placeholder(0),test_ask_with_default(0),test_env_placeholder(0),test_env_with_default(0),test_no_placeholders(0),test_generic_var_not_detected(0)
    TestResolveTemplate: test_ask_from_secrets(0),test_ask_from_env(0),test_ask_with_default_no_input(0),test_ask_unresolved_warning(0),test_env_resolved(0),test_env_with_default(0),test_env_unresolved_warning(0),test_generic_var_from_env(0),test_generic_var_from_secrets(0),test_generic_var_unresolved_no_warning(0),test_multiple_placeholders(0),test_interactive_prompt(0)
    TestLoadSecrets: test_load_from_project(1),test_skip_comments_and_empty(1),test_strip_quotes(1),test_no_secrets_file(1)
    TestFindSecretsFile: test_project_local(1),test_none_when_missing(1)
```

## Call Graph

*316 nodes · 396 edges · 38 modules · CC̄=1.8*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in README)* | 0 | 399 | 0 | **399** |
| `_step_analyze_blocks` *(in examples.demo_live_markpact)* | 20 ⚠ | 1 | 40 | **41** |
| `_parse_main_args` *(in src.markpact.cli)* | 1 | 1 | 35 | **36** |
| `run_service_with_tests` *(in src.markpact.tester)* | 16 ⚠ | 0 | 35 | **35** |
| `handle_config_cli` *(in src.markpact.cli.config_cmd)* | 12 ⚠ | 0 | 35 | **35** |
| `parse_zeppelin` *(in src.markpact.notebook_converter)* | 7 | 1 | 30 | **31** |
| `parse_databricks` *(in src.markpact.notebook_converter)* | 7 | 1 | 30 | **31** |
| `_handle_llm_generation` *(in src.markpact.cli.convert_cmd)* | 11 ⚠ | 0 | 26 | **26** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/markpact
# nodes: 316 | edges: 396 | modules: 38
# CC̄=1.8

HUBS[20]:
  README.print
    CC=0  in:399  out:0  total:399
  examples.demo_live_markpact._step_analyze_blocks
    CC=20  in:1  out:40  total:41
  src.markpact.cli._parse_main_args
    CC=1  in:1  out:35  total:36
  src.markpact.tester.run_service_with_tests
    CC=16  in:0  out:35  total:35
  src.markpact.cli.config_cmd.handle_config_cli
    CC=12  in:0  out:35  total:35
  src.markpact.notebook_converter.parse_zeppelin
    CC=7  in:1  out:30  total:31
  src.markpact.notebook_converter.parse_databricks
    CC=7  in:1  out:30  total:31
  src.markpact.cli.convert_cmd._handle_llm_generation
    CC=11  in:0  out:26  total:26
  src.markpact.notebook_converter.parse_jupyter
    CC=11  in:1  out:24  total:25
  src.markpact.runtime.core_v2.RuntimeV2.execute
    CC=16  in:0  out:25  total:25
  examples.demo_live_markpact.run_live
    CC=8  in:1  out:22  total:23
  examples.demo_live_markpact._step_generate_contract
    CC=2  in:1  out:21  total:22
  src.markpact.tester.run_http_test
    CC=8  in:1  out:21  total:22
  src.markpact.runtime.core_v3.RuntimeV3.reconcile
    CC=12  in:0  out:21  total:21
  examples.demo_live_markpact._print_summary
    CC=5  in:1  out:19  total:20
  src.markpact.packer.pack_directory
    CC=11  in:0  out:20  total:20
  examples.demo_live_markpact._finalize
    CC=3  in:1  out:19  total:20
  src.markpact.parser.parse_blocks
    CC=6  in:1  out:18  total:19
  src.markpact.converter.convert_markdown_to_markpact
    CC=3  in:0  out:19  total:19
  examples.demo_live_markpact.ok
    CC=2  in:18  out:1  total:19

MODULES:
  README  [1 funcs]
    print  CC=0  out:0
  SUMD  [60 funcs]
    _build_description  CC=0  out:0
    _extract_readme_description  CC=0  out:0
    _format_subprocess_failure  CC=0  out:0
    _handle_from_notebook  CC=0  out:0
    _handle_list_examples  CC=0  out:0
    _handle_list_notebook_formats  CC=0  out:0
    _handle_llm_generation  CC=0  out:0
    _handle_markdown_conversion  CC=0  out:0
    _handle_publish_mode  CC=0  out:0
    _parse_blocks_to_state  CC=0  out:0
  examples.demo_live_markpact  [20 funcs]
    _finalize  CC=3  out:19
    _print_summary  CC=5  out:19
    _save_outputs  CC=3  out:14
    _setup_session  CC=3  out:5
    _step_analyze_blocks  CC=20  out:40
    _step_generate_contract  CC=2  out:21
    _step_parse_blocks  CC=7  out:16
    _step_sha_integrity  CC=5  out:15
    _step_validate_blocks  CC=7  out:11
    fail  CC=2  out:1
  examples.fastapi-todo.README  [1 funcs]
    setattr  CC=0  out:0
  scripts.sync_version  [7 funcs]
    get_bumpversion_version  CC=2  out:6
    get_next_version  CC=1  out:4
    get_pyproject_version  CC=2  out:5
    set_bumpversion_version  CC=1  out:4
    set_pyproject_version  CC=1  out:4
    sync_versions  CC=5  out:11
    tag_exists  CC=2  out:1
  src.markpact.auto_fix  [15 funcs]
    _handle_missing_module_error  CC=5  out:6
    _handle_port_error  CC=4  out:9
    _handle_port_error_simple  CC=4  out:9
    _run_and_print  CC=6  out:5
    _run_subprocess  CC=1  out:1
    _setup_env_with_venv  CC=2  out:4
    _setup_env_with_venv_simple  CC=2  out:4
    _try_llm_fix  CC=3  out:3
    add_missing_dependency  CC=3  out:7
    detect_error_type  CC=7  out:8
  src.markpact.cli  [5 funcs]
    _dispatch_subcommand  CC=4  out:3
    _handle_generation_phase  CC=9  out:7
    _parse_main_args  CC=1  out:35
    _process_readme  CC=14  out:17
    main  CC=7  out:7
  src.markpact.cli.config_cmd  [1 funcs]
    handle_config_cli  CC=12  out:35
  src.markpact.cli.convert_cmd  [5 funcs]
    _handle_from_notebook  CC=6  out:8
    _handle_list_examples  CC=2  out:5
    _handle_list_notebook_formats  CC=2  out:5
    _handle_llm_generation  CC=11  out:26
    _handle_markdown_conversion  CC=12  out:11
  src.markpact.cli.helpers  [2 funcs]
    _parse_blocks_to_state  CC=15  out:12
    _resolve_file_body  CC=6  out:8
  src.markpact.cli.publish_cmd  [5 funcs]
    _determine_bump_type  CC=3  out:0
    _execute_publish_result  CC=4  out:5
    _handle_publish_mode  CC=5  out:5
    _print_publish_dry_run  CC=2  out:3
    _resolve_publish_config  CC=10  out:6
  src.markpact.cli.run_cmd  [7 funcs]
    _handle_docker_mode  CC=4  out:9
    _handle_normal_run  CC=5  out:4
    _handle_test_mode  CC=4  out:6
    _print_dry_run_tests  CC=2  out:4
    _run_http_tests  CC=4  out:2
    _run_shell_tests  CC=2  out:3
    _split_test_blocks  CC=7  out:3
  src.markpact.cli.sync_cmd  [11 funcs]
    _build_sync_parser  CC=1  out:16
    _execute_recursive_sync  CC=11  out:5
    _execute_single_sync  CC=12  out:8
    _handle_add_mode  CC=8  out:8
    _handle_backups_mode  CC=4  out:7
    _handle_list_mode  CC=3  out:5
    _handle_missing_mode  CC=3  out:5
    _handle_rollback_mode  CC=3  out:4
    _resolve_paths  CC=4  out:9
    _show_diffs  CC=6  out:9
  src.markpact.config  [11 funcs]
    apply_preset  CC=4  out:6
    ensure_config_dir  CC=1  out:2
    get_env_path  CC=1  out:2
    init_env  CC=3  out:3
    load_env  CC=8  out:12
    save_env  CC=1  out:9
    set_api_base  CC=1  out:1
    set_api_key  CC=1  out:1
    set_config  CC=1  out:2
    set_model  CC=1  out:1
  src.markpact.converter  [9 funcs]
    _detect_deps  CC=9  out:2
    _detect_file  CC=5  out:4
    _detect_run  CC=5  out:1
    _print_block_changes  CC=2  out:1
    _print_conversion_header  CC=1  out:3
    _print_conversion_summary  CC=11  out:9
    convert_markdown_to_markpact  CC=3  out:19
    detect_block_type  CC=6  out:6
    print_conversion_report  CC=3  out:9
  src.markpact.docker_runner  [14 funcs]
    _build_docker_image  CC=3  out:3
    _build_docker_image_simple  CC=4  out:5
    _find_docker_port  CC=6  out:5
    _resolve_docker_port  CC=6  out:4
    _run_docker_container_interactive  CC=3  out:6
    _run_docker_tests  CC=6  out:8
    _start_docker_container  CC=2  out:3
    _stop_docker_container  CC=2  out:3
    build_and_run_docker  CC=3  out:4
    is_port_free  CC=2  out:2
  src.markpact.generator  [7 funcs]
    _call_llm_with_config  CC=2  out:1
    _clean_llm_response  CC=4  out:4
    _configure_litellm  CC=3  out:2
    _fix_unclosed_blocks  CC=7  out:6
    _set_provider_api_key  CC=8  out:2
    generate_contract  CC=5  out:9
    save_contract  CC=2  out:3
  src.markpact.notebook_converter  [23 funcs]
    _extract_and_format_deps  CC=3  out:5
    _extract_description_from_cells  CC=7  out:5
    _extract_file_hint  CC=2  out:4
    _extract_markdown_section  CC=3  out:3
    _generate_header  CC=3  out:13
    _merge_code_files  CC=3  out:0
    _parse_quarto_code_chunks  CC=5  out:15
    _parse_quarto_yaml_front_matter  CC=7  out:12
    _parse_rmd_code_chunks  CC=5  out:15
    _parse_rmd_yaml_front_matter  CC=5  out:11
  src.markpact.packer  [11 funcs]
    _build_run_command  CC=8  out:0
    _collect_files  CC=10  out:13
    _detect_file_indicators  CC=5  out:8
    _detect_framework_from_content  CC=6  out:1
    _detect_run_command  CC=1  out:3
    _generate_readme_content  CC=7  out:12
    _get_language  CC=3  out:3
    _should_include  CC=6  out:2
    _write_output  CC=4  out:7
    pack_directory  CC=11  out:20
  src.markpact.parser  [2 funcs]
    parse_blocks  CC=6  out:18
    parse_blocks_recursive  CC=13  out:18
  src.markpact.publish.docker_pub  [2 funcs]
    generate_dockerfile  CC=1  out:2
    publish_docker  CC=9  out:12
  src.markpact.publish.github  [1 funcs]
    publish_github_packages  CC=3  out:3
  src.markpact.publish.helpers  [11 funcs]
    _analyze_blocks_for_types  CC=4  out:3
    _build_package_name  CC=9  out:5
    _check_file_type  CC=2  out:7
    _detect_registry  CC=7  out:1
    _first_heading  CC=3  out:3
    _first_paragraph  CC=7  out:8
    _get_default_author  CC=4  out:3
    _is_web_service  CC=3  out:1
    _slugify  CC=2  out:5
    infer_publish_config  CC=2  out:11
  src.markpact.publish.llm_config  [5 funcs]
    _call_llm_for_publish_config  CC=2  out:1
    _extract_publish_block_from_response  CC=4  out:5
    _set_provider_api_key_for_publish  CC=8  out:2
    _setup_llm_for_publish  CC=3  out:1
    generate_publish_config_with_llm  CC=8  out:5
  src.markpact.publish.main  [1 funcs]
    publish  CC=9  out:9
  src.markpact.publish.npm  [3 funcs]
    _build_npm_description  CC=3  out:5
    generate_package_json  CC=2  out:3
    publish_npm  CC=6  out:10
  src.markpact.publish.pypi  [20 funcs]
    _build_description  CC=3  out:5
    _build_package  CC=5  out:5
    _build_upload_cmd  CC=5  out:6
    _check_pypi_credentials  CC=9  out:7
    _copy_readme  CC=10  out:16
    _determine_base_path  CC=5  out:7
    _ensure_build_backend  CC=7  out:4
    _extract_readme_description  CC=8  out:8
    _get_build_error_hint  CC=6  out:0
    _get_upload_error_hint  CC=8  out:0
  src.markpact.runner  [3 funcs]
    ensure_venv  CC=3  out:3
    install_deps  CC=2  out:3
    run_cmd  CC=3  out:6
  src.markpact.runtime.core  [5 funcs]
    __init__  CC=3  out:8
    _execute_step  CC=6  out:17
    _print_summary  CC=11  out:9
    execute  CC=9  out:11
    parse  CC=3  out:6
  src.markpact.runtime.core_v2  [8 funcs]
    __init__  CC=4  out:10
    _execute_step_single  CC=9  out:15
    _execute_step_with_retry  CC=9  out:6
    _print_summary  CC=11  out:12
    _rollback  CC=8  out:10
    execute  CC=16  out:25
    parse  CC=3  out:6
    reset_state  CC=1  out:2
  src.markpact.runtime.core_v3  [4 funcs]
    _execute_step  CC=3  out:6
    _execute_step_with_retry  CC=8  out:12
    _rollback  CC=17  out:13
    reconcile  CC=12  out:21
  src.markpact.runtime.executors  [1 funcs]
    _run_ssh_persistent  CC=4  out:6
  src.markpact.runtime.plugins  [5 funcs]
    _extract_plugin_from_module  CC=6  out:9
    _load_from_directory  CC=5  out:7
    _load_from_file  CC=4  out:5
    load_from_module  CC=6  out:10
    load_from_path  CC=14  out:18
  src.markpact.runtime.ssh_manager  [2 funcs]
    close  CC=2  out:2
    connect  CC=5  out:7
  src.markpact.runtime.state  [2 funcs]
    _load  CC=3  out:6
    _save  CC=2  out:3
  src.markpact.syncer  [19 funcs]
    _backup_dir  CC=1  out:0
    _build_block  CC=1  out:1
    _build_header_suffix  CC=2  out:2
    _collect_untracked_blocks  CC=9  out:7
    _content_sha256  CC=1  out:3
    _detect_lang  CC=4  out:5
    _process_block  CC=15  out:18
    _prune_backups  CC=2  out:3
    _read_source_file  CC=3  out:4
    _write_new_blocks  CC=2  out:4
  src.markpact.template  [2 funcs]
    _find_secrets_file  CC=4  out:3
    load_secrets  CC=6  out:10
  src.markpact.tester  [5 funcs]
    print_summary  CC=3  out:5
    http_request  CC=7  out:12
    run_http_test  CC=8  out:21
    run_service_with_tests  CC=16  out:35
    run_tests_from_block  CC=4  out:7

EDGES:
  src.markpact.template.load_secrets → src.markpact.template._find_secrets_file
  src.markpact.cli.helpers._resolve_file_body → SUMD.load_secrets
  src.markpact.cli.helpers._resolve_file_body → SUMD.resolve_template
  src.markpact.cli.helpers._resolve_file_body → SUMD.has_template_placeholders
  src.markpact.cli.helpers._resolve_file_body → README.print
  src.markpact.cli.helpers._parse_blocks_to_state → src.markpact.cli.helpers._resolve_file_body
  src.markpact.cli.helpers._parse_blocks_to_state → README.print
  src.markpact.docker_runner.stop_existing_container → README.print
  src.markpact.docker_runner._build_docker_image_simple → README.print
  src.markpact.docker_runner._find_docker_port → src.markpact.docker_runner.is_port_free
  src.markpact.docker_runner._find_docker_port → README.print
  src.markpact.docker_runner._find_docker_port → SUMD.find_free_port
  src.markpact.docker_runner._run_docker_container_interactive → README.print
  src.markpact.docker_runner.build_and_run_docker → src.markpact.docker_runner._build_docker_image_simple
  src.markpact.docker_runner.build_and_run_docker → src.markpact.docker_runner.stop_existing_container
  src.markpact.docker_runner.build_and_run_docker → src.markpact.docker_runner._find_docker_port
  src.markpact.docker_runner.build_and_run_docker → src.markpact.docker_runner._run_docker_container_interactive
  src.markpact.docker_runner.run_docker_with_logs → src.markpact.docker_runner.stop_existing_container
  src.markpact.docker_runner.run_docker_with_logs → SUMD.find_free_port
  src.markpact.docker_runner.run_docker_with_logs → README.print
  src.markpact.docker_runner.run_docker_with_logs → src.markpact.docker_runner.is_port_free
  src.markpact.docker_runner.stream_docker_logs → README.print
  src.markpact.docker_runner._build_docker_image → README.print
  src.markpact.docker_runner._resolve_docker_port → src.markpact.docker_runner.is_port_free
  src.markpact.docker_runner._resolve_docker_port → README.print
  src.markpact.docker_runner._resolve_docker_port → SUMD.find_free_port
  src.markpact.docker_runner._start_docker_container → src.markpact.docker_runner.stop_existing_container
  src.markpact.docker_runner._start_docker_container → README.print
  src.markpact.docker_runner._run_docker_tests → SUMD.run_tests_from_block
  src.markpact.docker_runner._run_docker_tests → README.print
  src.markpact.docker_runner._run_docker_tests → SUMD.wait_for_service
  src.markpact.docker_runner._stop_docker_container → README.print
  src.markpact.docker_runner.run_docker_with_tests → src.markpact.docker_runner._build_docker_image
  src.markpact.docker_runner.run_docker_with_tests → src.markpact.docker_runner._resolve_docker_port
  src.markpact.docker_runner.run_docker_with_tests → src.markpact.docker_runner._start_docker_container
  src.markpact.docker_runner.run_docker_with_tests → src.markpact.docker_runner._run_docker_tests
  src.markpact.docker_runner.run_docker_with_tests → src.markpact.docker_runner._stop_docker_container
  src.markpact.cli.main → src.markpact.cli._parse_main_args
  src.markpact.cli.main → src.markpact.cli._handle_generation_phase
  src.markpact.cli.main → src.markpact.cli._process_readme
  src.markpact.cli.main → src.markpact.cli._dispatch_subcommand
  src.markpact.cli.main → SUMD._handle_list_examples
  src.markpact.cli.main → SUMD._handle_list_notebook_formats
  src.markpact.cli._dispatch_subcommand → SUMD.handle_config_cli
  src.markpact.cli._dispatch_subcommand → SUMD.handle_pack_cli
  src.markpact.cli._dispatch_subcommand → SUMD.handle_sync_cli
  src.markpact.cli._handle_generation_phase → SUMD._handle_from_notebook
  src.markpact.cli._handle_generation_phase → SUMD._handle_llm_generation
  src.markpact.cli._handle_generation_phase → README.print
  src.markpact.cli._process_readme → SUMD._handle_markdown_conversion
```

## Intent

Executable Markdown Runtime – run and manage entire projects directly from a single README.md file using specialized markpact code blocks and isolated Docker sandboxes.
