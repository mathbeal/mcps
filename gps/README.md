# mcp-gps

MCP server for calculating great-circle distances between GPS coordinates using the Haversine formula.

## Tools

| Tool | Description |
|------|-------------|
| `distance_between_points` | Returns the distance between two GPS points in kilometres and nautical miles |

## Setup

```bash
cp .env.example .env
uv sync
```

## Launch

```bash
uv run server.py
```

Runs on `http://127.0.0.1:8101` by default.

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
| `PORT` | `8101` | Server port |
