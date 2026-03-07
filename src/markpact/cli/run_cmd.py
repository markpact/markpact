"""Run modes — normal run, Docker, test execution."""

from __future__ import annotations

import sys
from pathlib import Path

from ..runner import install_deps, run_cmd
from ..sandbox import Sandbox


def _handle_docker_mode(args, sandbox: Sandbox, deps: list[str], run_command: str | None, verbose: bool) -> int:
    """Handle Docker mode. Returns exit code."""
    from ..docker_runner import check_docker_available, generate_dockerfile, build_and_run_docker
    if not check_docker_available():
        print("[markpact] ERROR: Docker is not available. Install Docker first.", file=sys.stderr)
        return 1
    if args.dry_run:
        print(f"[markpact] Would build and run Docker container")
        print(f"[markpact] Deps: {', '.join(deps)}")
        print(f"[markpact] Run: {run_command}")
        return 0
    generate_dockerfile(sandbox.path, deps, run_command.strip() if run_command else "python -m http.server 8000")
    return build_and_run_docker(sandbox.path, verbose=verbose)


def _print_dry_run_tests(test_blocks: list) -> None:
    """Print dry-run test information."""
    print(f"[markpact] Would run tests:")
    for meta, body in test_blocks:
        print(f"  [{meta}]: {len(body.splitlines())} tests")


def _split_test_blocks(test_blocks: list) -> tuple[list, list]:
    """Split test blocks into HTTP and shell tests."""
    http_tests = [body for meta, body in test_blocks if "http" in meta.lower() or not meta]
    shell_tests = [body for meta, body in test_blocks if "shell" in meta.lower() or "bash" in meta.lower()]
    return http_tests, shell_tests


def _run_http_tests(run_command: str | None, http_tests: list, sandbox: Sandbox,
                    port: int, verbose: bool, test_only: bool) -> int | None:
    """Run HTTP tests and return exit code if test_only, None otherwise."""
    if not http_tests or not run_command:
        return None

    from ..tester import run_service_with_tests
    test_body = "\n".join(http_tests)
    exit_code, suite = run_service_with_tests(run_command, test_body, sandbox, port=port, verbose=verbose)
    if test_only:
        return exit_code
    return None


def _run_shell_tests(shell_tests: list, sandbox: Sandbox, verbose: bool) -> None:
    """Run shell tests and print summary."""
    if not shell_tests:
        return

    from ..tester import run_shell_tests
    shell_body = "\n".join(shell_tests)
    shell_suite = run_shell_tests(shell_body, sandbox, verbose=verbose)
    shell_suite.print_summary()


def _handle_test_mode(args, sandbox: Sandbox, run_command: str | None, test_blocks: list,
                      deps: list[str], verbose: bool) -> int:
    """Handle test mode. Returns exit code."""
    from ..auto_fix import find_free_port

    if args.dry_run:
        _print_dry_run_tests(test_blocks)
        return 0

    if deps:
        install_deps(deps, sandbox, verbose)

    port = find_free_port()
    http_tests, shell_tests = _split_test_blocks(test_blocks)

    http_exit_code = _run_http_tests(run_command, http_tests, sandbox, port, verbose, args.test_only)
    if http_exit_code is not None:
        return http_exit_code

    _run_shell_tests(shell_tests, sandbox, verbose)

    return 0


def _handle_normal_run(args, sandbox: Sandbox, run_command: str | None, deps: list[str], readme: Path, verbose: bool) -> int:
    """Handle normal run mode. Returns exit code."""
    if args.dry_run:
        print(f"[markpact] Would run: {run_command}")
        return 0

    if deps:
        install_deps(deps, sandbox, verbose)

    use_auto_fix = args.auto_fix and not args.no_auto_fix
    if use_auto_fix:
        from ..auto_fix import run_with_auto_fix_llm
        run_with_auto_fix_llm(run_command, sandbox, readme_path=readme, verbose=verbose, use_llm=args.auto_fix_llm)
    else:
        run_cmd(run_command, sandbox, verbose)
    return 0
