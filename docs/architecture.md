# Architecture

## Overview

`~/mcps` is a monorepo of independent [FastMCP](https://github.com/jlowin/fastmcp) servers. Each server exposes a set of tools over the Model Context Protocol (MCP) via HTTP (streamable-http transport). All servers run side-by-side via Docker Compose.

```
~/mcps/
├── wingfoil/   MCP server — French wingfoil spots & wind data
├── docker-compose.yml   starts all servers
└── Makefile             dev commands (setup, test, lint)
```

## Server anatomy

Each server follows the same structure:

```
<name>/
├── server.py              FastMCP app — tool definitions, entrypoint
├── database.py            (optional) data layer, pure functions
├── data/                  (optional) static datasets
├── tests/
│   └── test_server.py     pytest suite, coverage = 100%
├── Dockerfile             ghcr.io/astral-sh/uv:python3.14-bookworm-slim
├── pyproject.toml         dependencies + tool config (pylint, mypy, black)
├── .pre-commit-config.yaml  isort, black, mypy, pylint, xenon, pytest
├── .env.example           documented environment variables
└── README.md              tools table, setup, configuration reference
```

## Transport

All servers use FastMCP's `streamable-http` transport. Each listens on `0.0.0.0:<port>` when running in Docker, and on `127.0.0.1:<port>` when running locally.

| Server   | Local port |
|----------|------------|
| gps      | 8101       |
| wingfoil | 8102       |

## Quality gates

Every server enforces the same pre-commit pipeline:

1. **isort** — import ordering
2. **black** — formatting (line length 100)
3. **mypy** — strict type checking
4. **pylint** — static analysis
5. **xenon** — cyclomatic complexity ≤ D (≈ 19)
6. **pytest** — full test suite with coverage = 100%

## Adding a server

Use the `mcp-builder` Claude agent. It assigns the next available port, scaffolds all required files, and registers the server in `docker-compose.yml` and `Makefile`.
