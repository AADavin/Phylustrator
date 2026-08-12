# Releasing Phylustrator

Phylustrator publishes to PyPI **and creates the GitHub Release** automatically when a version
tag is pushed, via
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC). No API token is stored
anywhere — PyPI trusts this repo's release workflow (`.github/workflows/release.yml`).

## One-time setup (do this once, on PyPI)

Register this repo as a trusted publisher for the `phylustrator` project:

1. Open **https://pypi.org/manage/project/phylustrator/settings/publishing/**
2. Under **Add a new publisher → GitHub**, enter:
   | Field | Value |
   |---|---|
   | Owner | `AADavin` |
   | Repository name | `Phylustrator` |
   | Workflow name | `release.yml` |
   | Environment name | *(leave blank)* |
3. Click **Add**.

That's the whole setup — no secrets, no tokens to rotate.

## Cutting a release

The version is single-sourced from `pyproject.toml` (`__version__` reads it back via
`importlib.metadata`). To release `X.Y.Z`:

```bash
# 1. bump the version in pyproject.toml:  version = "X.Y.Z"
git commit -am "release: X.Y.Z"

# 2. tag and push — pushing the tag is what triggers build + publish
git tag vX.Y.Z
git push && git push --tags
```

The **Release** workflow then runs the test suite, builds the sdist + wheel, checks the tag matches
the version, and publishes to PyPI. Follow it under the repo's **Actions** tab. Nothing else to run.

> Bump the **patch** (`0.1.0 → 0.1.1`) for fixes, the **minor** (`0.1.0 → 0.2.0`) for new features.
