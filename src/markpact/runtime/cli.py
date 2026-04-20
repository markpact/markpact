"""CLI for markpact runtime.

Usage:
    python -m markpact.runtime.cli migration.md
    python -m markpact.runtime.cli migration.md --dry-run
    python -m markpact.runtime.cli migration.md --plugins ./custom_plugins
"""
import argparse
import sys
from pathlib import Path

from .core import Runtime, RuntimeConfig


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
    
    # Create config
    config = RuntimeConfig(
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
    
    # Initialize runtime
    try:
        from .core_v2 import RuntimeV2
        runtime = RuntimeV2(str(file_path), config=config)
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
    
    # Execute
    try:
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
