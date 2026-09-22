from datetime import UTC, datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def current_year() -> int:
    return datetime.now(UTC).year


# Available in every template, so shared layout pieces like the footer copyright
# don't depend on each route remembering to pass it.
templates.env.globals["current_year"] = current_year
