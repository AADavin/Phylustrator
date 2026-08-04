"""The version the package reports is the version the source says it is.

``__version__`` reads ``importlib.metadata``, which is written **at install time**. In an editable
checkout that metadata is not regenerated when ``pyproject.toml`` changes, so a version bump leaves
the installed package reporting the old number while running the new code. It drifted two releases
that way — the source tree was 0.1.4 and `phylustrator.__version__` still said 0.1.0 — and nothing
noticed, because every other test exercises behaviour rather than the number.

That number is not decoration: ZOMBI2 pins `phylustrator>=0.1.4` and a run report records the
versions it was produced with. A stale one turns a provenance record into a wrong provenance record.

In CI this passes trivially — a fresh install cannot be stale. It exists for the working copy, where
the fix is `pip install -e . --no-deps` and the failure message says so.
"""

from __future__ import annotations

import importlib.metadata as metadata
import pathlib
import re
import sys

import pytest

import phylustrator

_ROOT = pathlib.Path(__file__).resolve().parent.parent

if sys.version_info >= (3, 11):
    import tomllib
else:                                       # pragma: no cover - the 3.10 backport
    import tomli as tomllib  # type: ignore[no-redef]


def _declared_version() -> str:
    path = _ROOT / "pyproject.toml"
    if not path.exists():
        pytest.skip("not running from a source checkout")
    with open(path, "rb") as f:
        return tomllib.load(f)["project"]["version"]


def test_the_reported_version_is_the_declared_one():
    declared = _declared_version()
    assert phylustrator.__version__ == declared, (
        f"phylustrator.__version__ is {phylustrator.__version__!r} but pyproject.toml declares "
        f"{declared!r}. The installed metadata is stale — regenerate it with "
        f"`pip install -e . --no-deps`. Until then anything reading the version, including a ZOMBI2 "
        f"run report, records the wrong one."
    )
    assert metadata.version("phylustrator") == declared


def test_the_version_is_a_release_number():
    """Guards the bump itself: a typo like `0.1.4.` or `v0.1.4` would tag and publish under a name
    nobody can pin."""
    assert re.fullmatch(r"\d+\.\d+\.\d+", _declared_version())
