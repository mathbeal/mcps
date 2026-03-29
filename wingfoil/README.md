# mcp-wingfoil

MCP server exposing 30 French wingfoil spots with 365-day wind and wave conditions. Raw data — Claude reasons about the best spots itself.

## Tools

| Tool | Description |
|------|-------------|
| `list_spots` | Paginated list of spots with monthly aggregated wind/wave stats and coordinates |
| `get_spot` | Full 365-day daily conditions for a specific spot |

## Setup

```bash
cp .env.example .env
uv sync
```

## Launch

```bash
uv run server.py
```

Runs on `http://127.0.0.1:8102` by default.

## Development

```bash
uv sync --group dev
uv run pytest -v
uv run pre-commit install
uv run pre-commit run --all-files
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Server host |
| `PORT` | `8102` | Server port |
