"""Commands for the owner and for development.

Run them from the project root:

    uv run python -m app.cli seed                     # load the placeholder watches
    uv run python -m app.cli status <slug> on-hold    # or available, or sold

The status command is the owner's way to mark a watch until the admin area
(#23) exists.
"""

import argparse
import sys
from collections.abc import Callable, Sequence

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import SessionLocal
from app.models import WatchStatus
from app.seed import seed
from app.services.inventory import WatchNotFound, set_status

# How each status is typed on the command line: ON_HOLD becomes "on-hold".
STATUS_ARGUMENTS = {status.name.lower().replace("_", "-"): status for status in WatchStatus}


def main(
    argv: Sequence[str] | None = None,
    session_factory: Callable[[], Session] = SessionLocal,
    settings: Settings | None = None,
) -> int:
    """Run one command and return the process exit code.

    The session factory and settings are parameters so tests can hand in their
    own database and environment.
    """
    settings = settings or get_settings()
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("seed", help="load the placeholder watches")
    status = commands.add_parser("status", help="mark a watch available, on hold, or sold")
    status.add_argument("slug", help="the watch's slug, e.g. aurelian-meridian-chronograph")
    status.add_argument("status", choices=STATUS_ARGUMENTS)
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
