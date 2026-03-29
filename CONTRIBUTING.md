# Contributing

## Development workflow

```bash
# 1. Set up each server you want to work on
cd <server>
uv sync --group dev
uv run pre-commit install

# 2. Make your changes

# 3. Run tests
uv run pytest --cov --cov-fail-under=100

# 4. Run quality checks
uv run pre-commit run --all-files

# Or from the repo root, for all servers at once:
make test
make lint
```

## Standards

All standards are defined in `AGENTS.md`. Key rules:

- Python 3.14+, modern type annotations (`X | None`, `list[X]`, not `Optional[X]`)
- Cyclomatic complexity ≤ 19 per function
- Test coverage = 100%
- No `print()` — use `logger.*`
- No secrets in logs, even in exception handlers
- Docstrings in clear English, imperative mood

## Adding a new MCP server

Use the `mcp-builder` Claude agent — it scaffolds everything following project standards:

```
add a new MCP server for <description>
```

## PR format

- Title: `[AI]: <title in english>`
- Description: bullet list < 5 lines
- Must include: `Coverage score: xx, max complexity: yy`
- All tests and pre-commit must pass before creating a PR

Use the `git-ops` Claude agent to create PRs with the correct format.

## Branching strategy

This project follows a **trunk-based development** workflow:

- `master` is the trunk — always deployable.
- Create short-lived **feature branches** named `feat/<description>` (e.g. `feat/add-health-check`).
- Bug fixes use `fix/<description>`.
- Chores and maintenance use `chore/<description>`.
- Merge via pull request only — squash merge preferred to keep trunk history linear.
- Delete feature branches after merge.

## Branch protection

The `master` branch is protected:
- Direct pushes are forbidden — all changes go through pull requests.
- CI must pass (test + lint + build + healthcheck jobs) before merging.
- Force-pushes are disabled.
