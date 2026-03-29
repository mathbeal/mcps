---
name: new-server
description: Scaffold a new FastMCP server in ~/mcps following all monorepo standards — server.py, pyproject.toml, Dockerfile, tests, pre-commit, docker-compose entry, Makefile REPOS entry.
---

Scaffold a new MCP server in the ~/mcps monorepo.

## Usage

```
/new-server <name> <description> <port>
```

Example: `/new-server weather "Weather forecast MCP server" 8103`

## Steps

### 1. Validate inputs

- `name` — lowercase, hyphens allowed, no spaces (e.g. `weather`)
- `description` — one-line description of the server's purpose
- `port` — next available port (current: gps=8101, wingfoil=8102 → use 810x)

### 2. Create directory structure

```
~/mcps/<name>/
├── server.py
├── pyproject.toml
├── Dockerfile
├── tests/
│   ├── __init__.py
│   └── test_server.py
└── .pre-commit-config.yaml  (copy from an existing server)
```

### 3. server.py

Minimal FastMCP server with at least one placeholder tool:

```python
"""MCP server — <description>."""

import logging

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("<name>")


@mcp.tool()
def placeholder() -> str:
    """Placeholder tool — replace with real implementation.

    >>> placeholder()
    'ok'
    """
    logger.info("placeholder called")
    return "ok"


if __name__ == "__main__":
    import os
    mcp.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "<port>")))
```

### 4. pyproject.toml

Copy from `gps/pyproject.toml`, then update:
- `name` → `mcp-<name>`
- `description` → provided description
- Keep all dev dependencies and tool config identical

### 5. Dockerfile

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_SYSTEM_PYTHON=1

RUN uv pip install "fastmcp>=2.0"

COPY server.py ./

EXPOSE <port>

CMD ["python", "server.py"]
```

### 6. tests/test_server.py

Minimal test covering the placeholder tool at 100% coverage:

```python
"""Tests for <name> server."""

import pytest
from server import placeholder


def test_placeholder() -> None:
    """placeholder returns ok."""
    assert placeholder() == "ok"
```

### 7. .pre-commit-config.yaml

Copy verbatim from `gps/.pre-commit-config.yaml`.

### 8. Register in monorepo

**docker-compose.yml** — add service:
```yaml
  <name>:
    build:
      context: ./<name>
    ports:
      - "<port>:<port>"
    env_file:
      - path: ./<name>/.env
        required: false
    environment:
      HOST: "0.0.0.0"
      PORT: "<port>"
    restart: unless-stopped
```

**Makefile** — add `<name>` to the `REPOS` variable:
```makefile
REPOS := gps wingfoil <name>
```

**daily skill** — add `<name>` to the repos list in `.claude/skills/daily/SKILL.md`.

### 9. Initialize

```bash
cd ~/mcps/<name>
uv sync --group dev
uv run pre-commit install
```

### 10. Verify

```bash
cd ~/mcps/<name>
uv run pytest --cov --cov-fail-under=100
uv run pre-commit run --all-files
```

Coverage must be 100% before the scaffold is considered complete.
