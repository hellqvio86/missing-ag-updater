import argparse
import sys

from .const import (
    ARCH_NAME,
    COLOR_BOLD,
    COLOR_ENDC,
    COLOR_HEADER,
    DEFAULT_CLI_BINARY,
    DEFAULT_HUB_DIR,
    DEFAULT_HUB_LAUNCHER,
    DEFAULT_IDE_DIR,
    DEFAULT_IDE_LAUNCHER,
    OS_NAME,
)
from .updater import update_cli, update_hub, update_ide
from .utils import print_error, print_info, print_success, print_warning


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-updater utility for Google Antigravity developer tools (Cross-Platform).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--check", action="store_true", help="Check for available updates without installing")
    parser.add_argument("--ide", action="store_true", help="Update only the Antigravity IDE")
    parser.add_argument("--hub", action="store_true", help="Update only the Antigravity Hub")
    parser.add_argument("--cli", action="store_true", help="Update only the Antigravity CLI")
    parser.add_argument("--force", action="store_true", help="Bypass version checks and active process warnings")
    parser.add_argument(
        "--dir-ide", type=str, default=DEFAULT_IDE_DIR, help="Override path to Antigravity IDE folder/bundle"
    )
    parser.add_argument(
        "--dir-hub", type=str, default=DEFAULT_HUB_DIR, help="Override path to Antigravity Hub folder/bundle"
    )
    parser.add_argument(
        "--path-cli", type=str, default=DEFAULT_CLI_BINARY, help="Override path to Antigravity CLI binary"
    )

    args = parser.parse_args()

    if OS_NAME == "unknown":
        print_error("Unsupported operating system.")
        sys.exit(1)

    # If no specific component is selected, default to all components
    update_all = not (args.ide or args.hub or args.cli)

    print(
        f"\n{COLOR_HEADER}{COLOR_BOLD}"
        "=== Unofficial Antigravity Applications Auto-Updater (missing-ag-updater) ==="
        f"{COLOR_ENDC}"
    )
    print_warning("This project is a community tool and is NOT affiliated with, sponsored by, or supported by Google.")
    print_info(f"Target Platform: {COLOR_BOLD}{OS_NAME} ({ARCH_NAME}){COLOR_ENDC}\n")

    success = True

    if args.ide or update_all:
        res = update_ide(args.dir_ide, DEFAULT_IDE_LAUNCHER, dry_run=args.check, force=args.force)
        success = success and res
        print()

    if args.hub or update_all:
        res = update_hub(args.dir_hub, DEFAULT_HUB_LAUNCHER, dry_run=args.check, force=args.force)
        success = success and res
        print()

    if args.cli or update_all:
        res = update_cli(args.path_cli, dry_run=args.check, force=args.force)
        success = success and res
        print()

    if success:
        print_success("Operation completed successfully.")
        sys.exit(0)
    else:
        print_error("One or more update operations failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
