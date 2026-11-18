"""Everything the app imports must be installed in production, not only in development.

The production image installs with `uv sync --no-dev`, so a package the app
imports but that only the dev group pulls in is missing there, while the tests,
which run with the dev group, pass. That's how Pillow, listed as dev-only,
crashed the 2026-11-18 deploy (`No module named 'PIL'`). This test applies
production's rule: every third-party import under app/ must come from a
runtime dependency in pyproject.toml, directly or through one of its own.
"""

import ast
import sys
import tomllib
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parent.parent


def imported_top_level_modules() -> set[str]:
    """The top-level names imported anywhere in app/, e.g. "PIL" for `from PIL import Image`."""
    names: set[str] = set()
    for path in (ROOT / "app").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return names - set(sys.stdlib_module_names) - {"app"}


def runtime_distributions() -> set[str]:
    """Every distribution `uv sync --no-dev` installs: the runtime list and all it requires."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    pending = [Requirement(line) for line in project["dependencies"]]
    seen: set[str] = set()
    while pending:
        requirement = pending.pop()
        name = canonicalize_name(requirement.name)
        if name in seen:
            continue
        seen.add(name)
        for line in metadata.requires(requirement.name) or []:
            dependency = Requirement(line)
            # Keep a dependency only if it applies here: no marker, or a
            # marker that holds for one of the extras asked for (or none).
            extras = requirement.extras or {""}
            if dependency.marker is None or any(
                dependency.marker.evaluate({"extra": extra}) for extra in extras
            ):
                pending.append(dependency)
    return seen


def test_every_import_in_the_app_is_a_runtime_dependency() -> None:
    providers = metadata.packages_distributions()
    runtime = runtime_distributions()

    missing = {
        module: sorted(providers.get(module, ["(not installed)"]))
        for module in imported_top_level_modules()
        if not any(canonicalize_name(dist) in runtime for dist in providers.get(module, []))
    }

    assert not missing, (
        f"imported by app/ but not installed in production: {missing}. "
        "Add them with `uv add <package>` (not --dev)."
    )
