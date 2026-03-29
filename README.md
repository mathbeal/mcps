# mcps

[![CI](https://github.com/mathbeal/mcps/actions/workflows/ci.yml/badge.svg)](https://github.com/mathbeal/mcps/actions/workflows/ci.yml)

Personal MCP server monorepo — [FastMCP](https://github.com/jlowin/fastmcp) servers for Claude, containerized with Docker.

Each subdirectory is an independent MCP server (Python 3.14 + FastMCP), containerized and configured independently. A single `docker compose up` starts all of them.

## Prerequisites

### Docker

Install Docker Engine and the Compose plugin:

```bash
# Ubuntu / Debian / WSL2
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

Verify:

```bash
docker --version
docker compose version
```

## Quick start

```bash
git clone <repo-url> ~/mcps
cd ~/mcps

# Set up the repo
make setup

# Start all servers
docker compose up -d
```

All servers restart automatically unless stopped (`restart: unless-stopped`).

| Server   | URL                   | Description                           |
|----------|-----------------------|---------------------------------------|
| gps      | http://localhost:8101 | Distance between GPS coordinates      |
| wingfoil | http://localhost:8102 | French wingfoil spots, raw data for Claude to reason about |

## Claude configuration

Add to your Claude `claude_desktop_config.json` (or equivalent MCP config file):

```json
{
  "mcpServers": {
    "gps": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8101/mcp"]
    },
    "wingfoil": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8102/mcp"]
    }
  }
}
```

Stop all servers:

```bash
docker compose down
```

## Logs

```bash
# All servers (live)
docker compose logs -f

# Single server
docker compose logs -f gps
docker compose logs -f wingfoil

# Last N lines
docker compose logs --tail=50 wingfoil
```

## Servers

### gps — port 8101

Distance calculator between two GPS coordinates using the Haversine formula.

| Tool | Description |
|------|-------------|
| `distance_between_points` | Distance in km and nautical miles between two lat/lon points |

### wingfoil — port 8102

French wingfoil spots database — 30 spots with 365-day conditions, raw data for Claude to reason about.

| Tool | Description |
|------|-------------|
| `list_spots` | Paginated list of spots with monthly aggregated wind/wave stats and coordinates |
| `get_spot` | Full 365-day daily conditions for a specific spot |

## Claude Code hooks

Hooks are configured in `.claude/settings.local.json` (gitignored — personal, not committed).

### Block `--no-verify` (PreToolUse)

Prevents bypassing the pre-commit gate on any `git commit --no-verify` attempt:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python3 -c \"import json, sys; data = json.load(sys.stdin); cmd = data.get('tool_input', {}).get('command', ''); print(json.dumps({'continue': False, 'stopReason': 'Blocked: --no-verify bypasses pre-commit hooks. Fix the issues instead.'}) if '--no-verify' in cmd else json.dumps({'continue': True}))\""
      }]
    }]
  }
}
```

### Remind to test before committing (Stop)

Displays a reminder at the end of every Claude Code session:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python3 -c \"import json; print(json.dumps({'systemMessage': 'Reminder: run make test && make lint before committing.'}))\""
      }]
    }]
  }
}
```

## Claude Agents

Agents live in `.claude/agents/` and are loaded automatically by Claude Code in this directory. Each agent is a specialized assistant scoped to a task.

### `mcp-builder` — Scaffold a new MCP server

Scaffolds a new server following all project standards from day one: `server.py`, `Dockerfile`, `pyproject.toml`, tests, pre-commit config, and a new entry in `docker-compose.yml`. Assigns the next available port starting from 8102.

**Trigger:** "add a new MCP server for X"

### `code-reviewer` — Pre-commit code review

Runs `pre-commit run --all-files` on all changed repos and fixes failures. Also rewrites docstrings in clear English, adds doctests where applicable, and modernizes type annotations to Python 3.14+ syntax (`X | None`, `list[X]`, etc.).

**Trigger:** "review my changes" or use proactively before committing

### `git-ops` — Git and PR operations

Handles PR creation with the correct format (`[AI]: <title>`), cross-repo change summaries, pre-commit validation across all repos, and safe branch cleanup.

**Trigger:** "create a PR" or "run pre-commit on all repos"

## Adding a new server

Use the `mcp-builder` agent — describe the new server and it will scaffold everything following project standards (agent-ready from day one).

## Development

```bash
make test    # run pytest --cov on all repos
make lint    # run pre-commit on all repos
make setup   # uv sync + pre-commit install on all repos
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow, coding standards, and PR format.

## License

[MIT](LICENSE)
