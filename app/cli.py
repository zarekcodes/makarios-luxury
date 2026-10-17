"""Commands for the owner and for development.

Run them from the project root:

    uv run python -m app.cli seed    # load the placeholder watches
"""

import argparse
import sys
from collections.abc import Callable, Sequence

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.seed import seed


def main(
    argv: Sequence[str] | None = None,
    session_factory: Callable[[], Session] = SessionLocal,
) -> int:
    """Run one command and return the process exit code.

    The session factory is a parameter so tests can hand in their own database.
    """
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("seed", help="load the placeholder watches")
    args = parser.parse_args(argv)

    with session_factory() as session:
        if args.command == "seed":
            added = seed(session)
            print(f"Added {added} placeholder watch(es).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
