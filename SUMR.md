# markpact - + GitOps meets AI Agents — all in one README.

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Call Graph](#call-graph)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `markpact`
- **version**: `0.1.41`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, app.doql.less, pyqual.yaml, goal.yaml, .env.example, project/(5 analysis files)

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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

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

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 106f 24705L | python:49,md:38,yaml:10,shell:3,toml:2,json:2,txt:1 | 2026-04-23
# CC̄=1.8 | critical:10/998 | dups:0 | cycles:0

HEALTH[12]:
  🔴 GOD   src/markpact/runtime/executors.py = 505L, 11 classes, 23m, max CC=8
  🔴 GOD   src/markpact/runtime/core_v3.py = 651L, 4 classes, 29m, max CC=17
  🟡 CC    _parse_blocks_to_state CC=15 (limit:15)
  🟡 CC    run_with_auto_fix_llm CC=18 (limit:15)
  🟡 CC    main CC=24 (limit:15)
  🟡 CC    _parse_pypirc_section CC=15 (limit:15)
  🟡 CC    run_service_with_tests CC=16 (limit:15)
  🟡 CC    _process_block CC=15 (limit:15)
  🟡 CC    _step_analyze_blocks CC=20 (limit:15)
  🟡 CC    _pdf_analyze CC=20 (limit:15)
  🟡 CC    _rollback CC=17 (limit:15)
  🟡 CC    execute CC=16 (limit:15)

REFACTOR[3]:
  1. split src/markpact/runtime/executors.py  (god module)
  2. split src/markpact/runtime/core_v3.py  (god module)
  3. split 10 high-CC methods  (CC>15)

PIPELINES[205]:
  [1] Src [load_secrets]: load_secrets → _find_secrets_file
      PURITY: 100% pure
  [2] Src [resolve_template]: resolve_template → _prompt_value
      PURITY: 100% pure
  [3] Src [has_template_placeholders]: has_template_placeholders
      PURITY: 100% pure
  [4] Src [root]: root
      PURITY: 100% pure
  [5] Src [_parse_blocks_to_state]: _parse_blocks_to_state → _resolve_file_body → load_secrets
      PURITY: 100% pure

LAYERS:
  src/                            CC̄=4.5    ←in:0  →out:0
  │ !! notebook_converter         710L  2C   25m  CC=11     ←0
  │ !! core_v3                    651L  4C   29m  CC=17     ←0
  │ !! syncer                     612L  1C   21m  CC=15     ←0
  │ !! core_v2                    507L  2C   19m  CC=16     ←0
  │ !! executors                  505L  11C   23m  CC=8      ←0
  │ !! pypi                       445L  0C   21m  CC=15     ←0
  │ packer                     431L  1C   12m  CC=11     ←0
  │ !! auto_fix                   427L  0C   15m  CC=18     ←0
  │ docker_runner              417L  0C   16m  CC=8      ←0
  │ generator                  362L  1C   11m  CC=8      ←2
  │ converter                  320L  2C   10m  CC=11     ←0
  │ !! tester                     312L  2C    7m  CC=16     ←0
  │ core                       296L  2C   12m  CC=11     ←0
  │ sync_cmd                   291L  0C   11m  CC=14     ←0
  │ plugins                    283L  3C   14m  CC=14     ←0
  │ !! cli                        267L  0C    1m  CC=24     ←0
  │ helpers                    226L  0C   13m  CC=9      ←0
  │ __init__                   205L  0C    5m  CC=14     ←0
  │ config                     204L  0C   12m  CC=8      ←0
  │ template                   184L  0C    5m  CC=6      ←0
  │ state                      176L  2C   17m  CC=9      ←0
  │ parser                     154L  1C    4m  CC=13     ←0
  │ parser                     153L  3C    5m  CC=8      ←0
  │ models                     143L  5C    4m  CC=10     ←0
  │ ssh_manager                114L  1C    7m  CC=5      ←0
  │ convert_cmd                112L  0C    5m  CC=12     ←0
  │ main                       110L  0C    2m  CC=11     ←0
  │ docker_pub                 108L  0C    2m  CC=9      ←0
  │ llm_config                 107L  0C    5m  CC=8      ←0
  │ run_cmd                    105L  0C    7m  CC=7      ←0
  │ steps                      103L  3C    3m  CC=7      ←2
  │ npm                        100L  0C    3m  CC=6      ←0
  │ publish_cmd                 95L  0C    5m  CC=10     ←0
  │ __init__                    89L  0C    0m  CC=0.0    ←0
  │ config_cmd                  74L  0C    1m  CC=12     ←0
  │ version                     72L  0C    3m  CC=4      ←0
  │ !! helpers                     66L  0C    2m  CC=15     ←0
  │ pack_cmd                    62L  0C    1m  CC=6      ←0
  │ sandbox                     59L  1C    6m  CC=3      ←0
  │ __init__                    56L  0C    0m  CC=0.0    ←0
  │ __init__                    54L  0C    0m  CC=0.0    ←0
  │ exceptions                  53L  8C    5m  CC=2      ←0
  │ runner                      42L  0C    3m  CC=3      ←0
  │ github                      37L  0C    1m  CC=3      ←0
  │ models                      32L  2C    1m  CC=2      ←0
  │ publisher                   27L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=1.9    ←in:0  →out:52  !! split
  │ !! demo_live_markpact         969L  2C   29m  CC=20     ←0
  │ README.md                  302L  0C    2m  CC=0.0    ←0
  │ DEMOS.md                   296L  0C    0m  CC=0.0    ←0
  │ README.md                  195L  2C    3m  CC=0.0    ←0
  │ README.md                  164L  0C    6m  CC=0.0    ←0
  │ README.md                  160L  0C    1m  CC=0.0    ←0
  │ README.md                  157L  0C    1m  CC=0.0    ←0
  │ README.md                  153L  0C    4m  CC=0.0    ←0
  │ README.md                  136L  6C    7m  CC=0.0    ←2
  │ README.md                  135L  0C    2m  CC=0.0    ←0
  │ README.md                  126L  0C    3m  CC=0.0    ←0
  │ README.md                  119L  0C    3m  CC=0.0    ←0
  │ README.md                  107L  0C    0m  CC=0.0    ←0
  │ README.md                   92L  0C    0m  CC=0.0    ←0
  │ README.md                   90L  0C    1m  CC=0.0    ←0
  │ README.md                   85L  3C    1m  CC=0.0    ←0
  │ README.md                   73L  3C    1m  CC=0.0    ←0
  │ README.md                   63L  1C    0m  CC=0.0    ←0
  │ sample.md                   62L  1C    3m  CC=0.0    ←0
  │ README.md                   62L  0C    0m  CC=0.0    ←0
  │ README.md                   59L  0C    0m  CC=0.0    ←0
  │ README.md                   57L  0C    0m  CC=0.0    ←0
  │ README.md                   48L  1C    3m  CC=0.0    ←0
  │ README.md                   44L  0C    3m  CC=0.0    ←0
  │ app                          7L  0C    1m  CC=1      ←0
  │ config.yaml                  4L  0C    0m  CC=0.0    ←0
  │ run.sh                       2L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=1.1    ←in:0  →out:3
  │ test_examples.sh           314L  0C    6m  CC=0.0    ←0
  │ sync_version               106L  0C    7m  CC=5      ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! SUMD.md                   1041L  0C  262m  CC=0.0    ←18
  │ !! README.md                  627L  0C    4m  CC=0.0    ←33
  │ CHANGELOG.md               436L  0C    0m  CC=0.0    ←0
  │ goal.yaml                  432L  0C    0m  CC=0.0    ←0
  │ TODO.md                    109L  0C    1m  CC=0.0    ←0
  │ pyproject.toml              94L  0C    0m  CC=0.0    ←0
  │ project.toon-schema.json    66L  0C    0m  CC=0.0    ←0
  │ pyqual.yaml                 55L  0C    0m  CC=0.0    ←0
  │ project.sh                  40L  0C    0m  CC=0.0    ←0
  │ .bumpversion.toml           14L  0C    0m  CC=0.0    ←0
  │ markpact.config.json         6L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │
  docs/                           CC̄=0.0    ←in:0  →out:0
  │ README.md                  413L  0C    1m  CC=0.0    ←0
  │ runtime-v2-improvements.md   371L  0C    1m  CC=0.0    ←0
  │ generator.md               326L  0C    0m  CC=0.0    ←0
  │ ci-cd.md                   143L  0C    0m  CC=0.0    ←0
  │ contract.md                119L  0C    1m  CC=0.0    ←0
  │ llm.md                     119L  1C    2m  CC=0.0    ←0
  │ publishing.md               92L  0C    0m  CC=0.0    ←0
  │
  generated/                      CC̄=0.0    ←in:0  →out:0
  │ README.md                   60L  1C    1m  CC=0.0    ←0
  │
  url-test/                       CC̄=0.0    ←in:0  →out:0
  │ README.md                  125L  3C    2m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! calls.yaml                2961L  0C    0m  CC=0.0    ←0
  │ !! project.yaml               777L  0C    0m  CC=0.0    ←0
  │ !! context.md                 682L  0C    0m  CC=0.0    ←0
  │ !! map.toon.yaml              501L  0C  262m  CC=0.0    ←0
  │ README.md                  340L  0C    0m  CC=0.0    ←0
  │ calls.toon.yaml            315L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         105L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         78L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           58L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  55L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     Makefile                                  0L

COUPLING:
                                  src.markpact                 README                   SUMD               examples                scripts  examples.fastapi-todo
           src.markpact                     ──                    347                     94                     ←1                                             2  !! fan-out
                 README                   ←347                     ──                                           ←49                     ←3                         hub
                   SUMD                    ←94                                            ──                     ←2                                                hub
               examples                      1                     49                      2                     ──                                                !! fan-out
                scripts                                             3                                                                   ──                       
  examples.fastapi-todo                     ←2                                                                                                                 ──
  CYCLES: none
  HUB: SUMD/ (fan-in=96)
  HUB: README/ (fan-in=399)
  SMELL: examples/ fan-out=52 → split needed
  SMELL: src.markpact/ fan-out=443 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 8 groups | 49f 10757L | 2026-04-23

SUMMARY:
  files_scanned: 49
  total_lines:   10757
  dup_groups:    8
  dup_fragments: 17
  saved_lines:   92
  scan_ms:       5033

HOTSPOTS[7] (files with most duplication):
  src/markpact/notebook_converter.py  dup=79L  groups=1  frags=2  (0.7%)
  src/markpact/runtime/core.py  dup=24L  groups=2  frags=2  (0.2%)
  src/markpact/runtime/core_v2.py  dup=24L  groups=2  frags=2  (0.2%)
  src/markpact/cli/convert_cmd.py  dup=16L  groups=1  frags=2  (0.1%)
  src/markpact/auto_fix.py  dup=14L  groups=1  frags=2  (0.1%)
  src/markpact/config.py  dup=9L  groups=1  frags=3  (0.1%)
  examples/demo_live_markpact.py  dup=6L  groups=1  frags=2  (0.1%)

DUPLICATES[8] (ranked by impact):
  [53de7ca7b2b8d159] ! STRU  _parse_rmd_code_chunks  L=41 N=2 saved=41 sim=1.00
      src/markpact/notebook_converter.py:126-166  (_parse_rmd_code_chunks)
      src/markpact/notebook_converter.py:223-260  (_parse_quarto_code_chunks)
  [28d6f1d39ecfd0cc]   EXAC  _load_plugins  L=12 N=2 saved=12 sim=1.00
      src/markpact/runtime/core.py:78-89  (_load_plugins)
      src/markpact/runtime/core_v2.py:97-108  (_load_plugins)
  [092e6323444fbfe6]   EXAC  parse  L=12 N=2 saved=12 sim=1.00
      src/markpact/runtime/core.py:91-102  (parse)
      src/markpact/runtime/core_v2.py:110-121  (parse)
  [1aeee8024563e101]   STRU  _handle_list_examples  L=8 N=2 saved=8 sim=1.00
      src/markpact/cli/convert_cmd.py:12-19  (_handle_list_examples)
      src/markpact/cli/convert_cmd.py:22-29  (_handle_list_notebook_formats)
  [805c8fd6e0aa41d1]   STRU  _setup_env_with_venv_simple  L=7 N=2 saved=7 sim=1.00
      src/markpact/auto_fix.py:90-96  (_setup_env_with_venv_simple)
      src/markpact/auto_fix.py:279-285  (_setup_env_with_venv)
  [1bb09be55cf9f692]   STRU  set_model  L=3 N=3 saved=6 sim=1.00
      src/markpact/config.py:134-136  (set_model)
      src/markpact/config.py:139-141  (set_api_key)
      src/markpact/config.py:144-146  (set_api_base)
  [28156e4c54dd940f]   EXAC  name  L=3 N=2 saved=3 sim=1.00
      src/markpact/runtime/executors.py:26-28  (name)
      src/markpact/runtime/plugins.py:31-33  (name)
  [8696c3423bddd809]   STRU  ok  L=3 N=2 saved=3 sim=1.00
      examples/demo_live_markpact.py:383-385  (ok)
      examples/demo_live_markpact.py:388-390  (fail)

REFACTOR[8] (ranked by priority):
  [1] ○ extract_function   → src/markpact/utils/_parse_rmd_code_chunks.py
      WHY: 2 occurrences of 41-line block across 1 files — saves 41 lines
      FILES: src/markpact/notebook_converter.py
  [2] ○ extract_function   → src/markpact/runtime/utils/_load_plugins.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: src/markpact/runtime/core.py, src/markpact/runtime/core_v2.py
  [3] ○ extract_function   → src/markpact/runtime/utils/parse.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: src/markpact/runtime/core.py, src/markpact/runtime/core_v2.py
  [4] ○ extract_function   → src/markpact/cli/utils/_handle_list_examples.py
      WHY: 2 occurrences of 8-line block across 1 files — saves 8 lines
      FILES: src/markpact/cli/convert_cmd.py
  [5] ○ extract_function   → src/markpact/utils/_setup_env_with_venv_simple.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: src/markpact/auto_fix.py
  [6] ○ extract_function   → src/markpact/utils/set_model.py
      WHY: 3 occurrences of 3-line block across 1 files — saves 6 lines
      FILES: src/markpact/config.py
  [7] ○ extract_function   → src/markpact/runtime/utils/name.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: src/markpact/runtime/executors.py, src/markpact/runtime/plugins.py
  [8] ○ extract_function   → examples/utils/ok.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: examples/demo_live_markpact.py

QUICK_WINS[6] (low risk, high savings — do first):
  [1] extract_function   saved=41L  → src/markpact/utils/_parse_rmd_code_chunks.py
      FILES: notebook_converter.py
  [2] extract_function   saved=12L  → src/markpact/runtime/utils/_load_plugins.py
      FILES: core.py, core_v2.py
  [3] extract_function   saved=12L  → src/markpact/runtime/utils/parse.py
      FILES: core.py, core_v2.py
  [4] extract_function   saved=8L  → src/markpact/cli/utils/_handle_list_examples.py
      FILES: convert_cmd.py
  [5] extract_function   saved=7L  → src/markpact/utils/_setup_env_with_venv_simple.py
      FILES: auto_fix.py
  [6] extract_function   saved=6L  → src/markpact/utils/set_model.py
      FILES: config.py

EFFORT_ESTIMATE (total ≈ 3.8h):
  hard   _parse_rmd_code_chunks              saved=41L  ~123min
  easy   _load_plugins                       saved=12L  ~24min
  easy   parse                               saved=12L  ~24min
  easy   _handle_list_examples               saved=8L  ~16min
  easy   _setup_env_with_venv_simple         saved=7L  ~14min
  easy   set_model                           saved=6L  ~12min
  easy   name                                saved=3L  ~6min
  easy   ok                                  saved=3L  ~6min

METRICS-TARGET:
  dup_groups:  8 → 0
  saved_lines: 92 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 911 func | 52f | 2026-04-23

NEXT[9] (ranked by impact):
  [1] !! SPLIT           src/markpact/runtime/core_v3.py
      WHY: 651L, 4 classes, max CC=17
      EFFORT: ~4h  IMPACT: 11067

  [2] !! SPLIT           src/markpact/syncer.py
      WHY: 612L, 1 classes, max CC=15
      EFFORT: ~4h  IMPACT: 9180

  [3] !! SPLIT           src/markpact/notebook_converter.py
      WHY: 710L, 2 classes, max CC=11
      EFFORT: ~4h  IMPACT: 7810

  [4] !  SPLIT-FUNC      main  CC=24  fan=22
      WHY: CC=24 exceeds 15
      EFFORT: ~1h  IMPACT: 528

  [5] !  SPLIT-FUNC      run_service_with_tests  CC=16  fan=23
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 368

  [6] !  SPLIT-FUNC      RuntimeV2.execute  CC=16  fan=16
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 256

  [7] !  SPLIT-FUNC      run_with_auto_fix_llm  CC=18  fan=9
      WHY: CC=18 exceeds 15
      EFFORT: ~1h  IMPACT: 162

  [8] !  SPLIT-FUNC      _parse_blocks_to_state  CC=15  fan=9
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 135

  [9] !  SPLIT-FUNC      _parse_pypirc_section  CC=15  fan=7
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 105


RISKS[3]:
  ⚠ Splitting src/markpact/notebook_converter.py may break 25 import paths
  ⚠ Splitting src/markpact/runtime/core_v3.py may break 29 import paths
  ⚠ Splitting src/markpact/syncer.py may break 21 import paths

METRICS-TARGET:
  CC̄:          1.9 → ≤1.3
  max-CC:      24 → ≤12
  god-modules: 5 → 0
  high-CC(≥15): 8 → ≤4
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=4.5 → now CC̄=1.9
```

## Intent

Executable Markdown Runtime – run and manage entire projects directly from a single README.md file using specialized markpact code blocks and isolated Docker sandboxes.
