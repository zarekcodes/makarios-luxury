"""Commands for the owner and for development.

Run them from the project root:

    uv run python -m app.cli seed                     # load the placeholder watches
    uv run python -m app.cli status <slug> on-hold    # or available, or sold
    uv run python -m app.cli admin-password <name>    # create an owner's admin account,
                                                      # or give it a new password
    uv run python -m app.cli admin-remove <name>      # delete an owner's admin account

The status command predates the admin area at /admin, which does the same.
"""

import argparse
import getpass
import sys
from collections.abc import Callable, Sequence

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import SessionLocal
from app.models import WatchStatus
from app.seed import seed
from app.services import admin_accounts
from app.services.inventory import WatchNotFound, set_status

# How each status is typed on the command line: ON_HOLD becomes "on-hold".
STATUS_ARGUMENTS = {status.name.lower().replace("_", "-"): status for status in WatchStatus}


def main(
    argv: Sequence[str] | None = None,
    session_factory: Callable[[], Session] = SessionLocal,
    settings: Settings | None = None,
    read_password: Callable[[str], str] = getpass.getpass,
) -> int:
    """Run one command and return the process exit code.

    The session factory, settings and password prompt are parameters so tests
    can hand in their own database, environment and typing.
    """
    settings = settings or get_settings()
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("seed", help="load the placeholder watches")
    status = commands.add_parser("status", help="mark a watch available, on hold, or sold")
    status.add_argument("slug", help="the watch's slug, e.g. aurelian-meridian-chronograph")
    status.add_argument("status", choices=STATUS_ARGUMENTS)
    password = commands.add_parser(
        "admin-password", help="create an owner's admin account, or give it a new password"
    )
    password.add_argument("username")
    remove = commands.add_parser("admin-remove", help="delete an owner's admin account")
    remove.add_argument("username")
    args = parser.parse_args(argv)

    with session_factory() as session:
        if args.command == "seed":
            # The placeholders are invented watches, so they must never be
            # offered to real buyers.
            if settings.is_production:
                print("Refusing to seed placeholder watches in production.", file=sys.stderr)
                return 1
            added = seed(session)
            print(f"Added {added} placeholder watch(es).")

        elif args.command == "status":
            try:
                watch = set_status(session, args.slug, STATUS_ARGUMENTS[args.status])
            except WatchNotFound:
                print(f"No watch has the slug {args.slug!r}.", file=sys.stderr)
                return 1
            print(f"{watch.name} ({watch.slug}) is now {watch.status.value.lower()}.")

        elif args.command == "admin-password":
            # Typed at a prompt that doesn't echo, rather than passed as an
            # argument, which the shell would keep in its history.
            new_password = read_password(f"New password for {args.username}: ")
            if read_password("Type it again: ") != new_password:
                print("The passwords don't match. Nothing changed.", file=sys.stderr)
                return 1
            try:
                admin_accounts.set_password(session, args.username, new_password)
            except admin_accounts.PasswordTooShort as error:
                print(f"Too short: {error}. Nothing changed.", file=sys.stderr)
                return 1
            print(f"{args.username} can sign in at /admin. Any older sessions are signed out.")

        elif args.command == "admin-remove":
            try:
                admin_accounts.remove(session, args.username)
            except admin_accounts.AdminNotFound:
                print(f"No admin account is named {args.username!r}.", file=sys.stderr)
                return 1
            print(f"Removed {args.username}. Their sessions stop working now.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
