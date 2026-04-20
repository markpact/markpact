"""CLI for markpact runtime.

Usage:
    python -m markpact.runtime.cli migration.md
    python -m markpact.runtime.cli migration.md --dry-run
    python -m markpact.runtime.cli migration.md --plugins ./custom_plugins
"""
import argparse
import sys
from pathlib import Path

from . import Runtime, RuntimeConfig, RuntimeV3, RuntimeConfigV3


def main():
    parser = argparse.ArgumentParser(
        prog="markpact-runtime",
        description="Universal deployment runtime for markpact markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run migration
    %(prog)s migration.md
    
    # Dry run (no changes)
    %(prog)s migration.md --dry-run
    
    # With custom plugins
    %(prog)s migration.md --plugins ./plugins --plugins ~/.markpact/plugins
    
    # Filter steps
    %(prog)s migration.md --step-filter "rsync.*"
    
    # With SSH key
    %(prog)s migration.md --ssh-key ~/.ssh/deploy_key
    
    # Reset state (fresh deployment)
    %(prog)s migration.md --reset-state
    
    # Resume after failure
    %(prog)s migration.md  # Automatically skips completed steps
    
    # Plan mode (preview changes, v3)
    %(prog)s migration.md --plan
    
    # Check current state (v3)
    %(prog)s migration.md --check-state
        """
    )
    
    parser.add_argument(
        "file",
        help="Path to markpact markdown file"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Show what would be done without executing"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="Verbose output"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output"
    )
    
    parser.add_argument(
        "--plugins", "-p",
        action="append",
        default=[],
        help="Path to plugin directory (can be used multiple times)"
    )
    
    parser.add_argument(
        "--step-filter", "-f",
        help="Regex to filter steps by id"
    )
    
    parser.add_argument(
        "--ssh-key", "-k",
        help="SSH private key for remote operations"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Default timeout for steps (seconds)"
    )
    
    parser.add_argument(
        "--retry",
        type=int,
        default=0,
        help="Default retry count for steps"
    )
    
    parser.add_argument(
        "--no-stop-on-error",
        action="store_true",
        help="Continue on step failure"
    )
    
    parser.add_argument(
        "--list-steps", "-l",
        action="store_true",
        help="List available steps without executing"
    )
    
    parser.add_argument(
        "--reset-state",
        action="store_true",
        help="Reset deployment state for fresh start"
    )
    
    parser.add_argument(
        "--state-file",
        default=".deploy-state.json",
        help="State file for idempotency tracking (default: .deploy-state.json)"
    )
    
    parser.add_argument(
        "--show-state",
        action="store_true",
        help="Show current deployment state and exit"
    )
    
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Preview changes without executing (v3: state reconciliation)"
    )
    
    parser.add_argument(
        "--check-state",
        action="store_true",
        help="Check current facts/state on target host (v3)"
    )
    
    parser.add_argument(
        "--use-v2",
        action="store_true",
        help="Use RuntimeV2 instead of v3 (backward compatibility)"
    )
    
    args = parser.parse_args()
    
    # Validate file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1
    
    # Show state if requested
    if args.show_state:
        from .state import StateManager
        state_mgr = StateManager(args.state_file)
        print(f"State file: {args.state_file}")
        print(f"Steps completed: {len(state_mgr.state.steps_done)}")
        for step_id in state_mgr.state.steps_done:
            print(f"  ✓ {step_id}")
        if state_mgr.state.failed_step:
            print(f"Failed step: {state_mgr.state.failed_step}")
        return 0
    
    # Create config (v3 by default, v2 if requested)
    if args.use_v2:
        from . import RuntimeConfigV2, RuntimeV2
        config = RuntimeConfigV2(
            dry_run=args.dry_run,
            verbose=not args.quiet,
            stop_on_error=not args.no_stop_on_error,
            plugin_paths=[Path(p) for p in args.plugins],
            ssh_key=args.ssh_key,
            timeout_default=args.timeout,
            retry_default=args.retry,
            state_file=args.state_file,
            reset_state=args.reset_state,
        )
    else:
        config = RuntimeConfigV3(
            dry_run=args.dry_run,
            verbose=not args.quiet,
            stop_on_error=not args.no_stop_on_error,
            plugin_paths=[Path(p) for p in args.plugins],
            ssh_key=args.ssh_key,
            timeout_default=args.timeout,
            retry_default=args.retry,
            state_file=args.state_file,
            reset_state=args.reset_state,
            plan_mode=args.plan,
        )
    
    # Initialize runtime
    try:
        if args.use_v2:
            from . import RuntimeV2
            runtime = RuntimeV2(str(file_path), config=config)
        else:
            from . import RuntimeV3
            runtime = RuntimeV3(str(file_path), config=config)
    except Exception as e:
        print(f"Error: Failed to initialize runtime: {e}", file=sys.stderr)
        return 1
    
    # List steps if requested
    if args.list_steps:
        blocks = runtime.parse()
        runtime._process_blocks(blocks)
        
        print(f"Steps in {args.file}:")
        for i, step in enumerate(runtime.steps, 1):
            risk_indicator = "⚠️" if step.risk in ("high", "medium") else "  "
            skip_indicator = ""
            if runtime.state_manager.is_step_done(step.id):
                skip_indicator = " [DONE]"
            print(f"  {i}. [{step.id}]{skip_indicator} {step.description} {risk_indicator}")
            print(f"      action: {step.action}, timeout: {step.timeout}s, retry: {step.retry}")
        return 0
    
    # Check state mode (v3)
    if args.check_state:
        if not hasattr(runtime, 'facts'):
            print("Error: --check-state requires RuntimeV3", file=sys.stderr)
            return 1
        print(f"[CHECK STATE] Target: {runtime.config_data.target if runtime.config_data else 'unknown'}")
        print(f"  Docker installed: {runtime.facts.check('docker_installed')}")
        return 0
    
    # Execute or Plan
    try:
        if args.plan and hasattr(runtime, 'plan'):
            # v3: Plan mode
            summary = runtime.plan(step_filter=args.step_filter)
            print(f"\n[PLAN SUMMARY]")
            print(f"  Total steps: {summary.total_steps}")
            print(f"  Would execute: {summary.successful}")
            print(f"  Would skip: {summary.skipped}")
            print(f"  Would fail: {summary.failed}")
            return 0
        elif hasattr(runtime, 'reconcile'):
            # v3: Reconcile mode
            summary = runtime.reconcile(step_filter=args.step_filter)
            return 0 if summary.failed == 0 else 1
        else:
            # v2: Execute mode
            success = runtime.execute(step_filter=args.step_filter)
            return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
