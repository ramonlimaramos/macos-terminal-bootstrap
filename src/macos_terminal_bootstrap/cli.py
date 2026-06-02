from __future__ import annotations

import argparse
from pathlib import Path

from .installer import InstallOptions, Installer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ramon-terminal-bootstrap",
        description="Install Ramon terminal settings for Ghostty, Zsh, and Starship.",
    )
    parser.add_argument(
        "--home",
        type=Path,
        default=Path.home(),
        help="Target home directory. Defaults to the current user's home.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Show what would be installed.")
    plan.add_argument("--no-deps", action="store_true", help="Skip dependency plan.")

    install = subparsers.add_parser("install", help="Install configs and dependencies.")
    install.add_argument("--dry-run", action="store_true", help="Print actions without changing files.")
    install.add_argument("--no-deps", action="store_true", help="Skip Homebrew and git-based dependency setup.")
    install.add_argument("--no-configs", action="store_true", help="Skip dotfile/config installation.")

    doctor = subparsers.add_parser("doctor", help="Check installed tools and managed config files.")
    doctor.add_argument("--quiet", action="store_true", help="Only print problems.")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    options = InstallOptions(
        home=args.home.expanduser(),
        dry_run=getattr(args, "dry_run", False),
        install_dependencies=not getattr(args, "no_deps", False),
        install_configs=not getattr(args, "no_configs", False),
    )
    installer = Installer(options)

    if args.command == "plan":
        installer.plan(include_dependencies=not args.no_deps)
        return 0
    if args.command == "install":
        installer.install()
        return 0
    if args.command == "doctor":
        return 0 if installer.doctor(quiet=args.quiet) else 1

    raise AssertionError(f"Unhandled command: {args.command}")
