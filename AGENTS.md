# Agents.md

## Dev environment
- python3.14.*
- Never install packages updates < 7 days existence.
- Update ci for test on next version of python: allow failure.

## Vocabulary
- Do not use synonyms, each concept must have one term.
- Ensure consistency between vocabulary/code/documentation.
- Create or update glossary.md sorted in alphabetic order, never committed.

## Implementation instructions
- Always add logs to new code.
- Ensure each function has max cyclomatic complexity of 19. *(enforced by pre-commit: pylint)*
- Rewrite docstring in better english if it can be rewritten.
- Uses doctests if it can be written in less than 5 lines.
- Annotate code with comments.
- Ensure no secrets will be displayed in logs, even during exceptions.

### Examples

**Good** — logging, modern annotations, doctest:
```python
def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two GPS points.

    >>> round(_haversine_km(48.8566, 2.3522, 51.5074, -0.1278), 1)
    343.6
    """
    logger.info("Computing haversine for (%f, %f) -> (%f, %f)", lat1, lon1, lat2, lon2)
    ...
```

**Bad** — print instead of logger, old annotations, no doctest:
```python
from typing import Optional, List

def haversine(lat1, lon1, lat2, lon2) -> Optional[float]:
    print(f"computing {lat1},{lon1} -> {lat2},{lon2}")  # no logger
    ...
```

## Testing instructions
- Ensure coverage = 100%. *(enforced by pre-commit: pytest --cov-fail-under=100)*
- Remove tests that does not modify coverage score.
- All new code in branch must be tested with appropriate test cases. *(enforced by pre-commit: pytest)*
- Create fixtures as often as you can to reduce tests complexity.

## Pre-commit hooks (automated)
Every project must have a `.pre-commit-config.yaml` enforcing:
- `check-yaml`, `end-of-file-fixer`, `trailing-whitespace`, `check-added-large-files`
- `isort` — import ordering
- `black` — formatting *(line-length configured in pyproject.toml)*
- `mypy` — type checking
- `pylint` — linting, complexity *(max-line-length and max_complexity configured in pyproject.toml)*
- `pytest` — full test suite with coverage gate

Run `pre-commit install` once per clone to activate the git hook. The hook runs automatically on every `git commit`.

**Important:** the root git hook only runs the root `.pre-commit-config.yaml`, which does not include per-server hooks (mypy, pylint, pytest). Always run `make lint && make test` before committing to catch all errors locally.

## Adding a new server

1. Port assignment: follow 810x sequence (gps=8101, wingfoil=8102, next=8103, …).
2. Use `/new-server <name> <description> <port>` to scaffold all required files.
3. Register in `docker-compose.yml`, `Makefile` (`REPOS`), and `.claude/skills/daily/SKILL.md`.
4. Copy `.pre-commit-config.yaml` verbatim from an existing server.
5. Each server has its own `uv` venv — run `make setup` after adding.

## Environment files

- Each server may have a `.env.example` committed to the repo.
- `make setup` copies `.env.example` → `.env` automatically if `.env` is absent.
- Never commit `.env` files.

## Versioning

Each server is versioned independently in its `pyproject.toml` using [Semantic Versioning](https://semver.org): `MAJOR.MINOR.PATCH`.

| Change | Bump | Example |
|--------|------|---------|
| Breaking change to a tool (renamed, removed, signature changed) | `MAJOR` | `1.0.0` → `2.0.0` |
| New tool or backward-compatible feature | `MINOR` | `1.0.0` → `1.1.0` |
| Bug fix, refactor, dependency update (no API change) | `PATCH` | `1.0.0` → `1.0.1` |

Rules:
- Bump the version in `pyproject.toml` in the same commit as the change.
- Tag the release: `git tag <server>-v<version>` (e.g. `gps-v1.2.0`).
- Pre-1.0 (`0.x.y`): minor bumps may include breaking changes.

## Commit instructions

Format: `<type>: <short description in english>`

- Types: `feat`, `fix`, `chore`, `docs`
- One line, no period at the end
- Examples:
  - `feat: add haversine distance tool`
  - `fix: handle missing wind data in score calculation`
  - `chore: update pre-commit hooks`
  - `docs: document port assignment convention`

## PR instructions
- All tests and pre-commit must be satisfied before creating PR.
- Use `/pr` to create a PR with the correct format automatically.
- Title: [AI]: <title in english>
- Description contains (<5 lines) list of changes summary for human.
- Coverage score: xx, max complexity: yy
