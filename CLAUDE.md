# Claude Code — Project Context

This is the `~/mcps` monorepo. Read `AGENTS.md` for all coding standards, vocabulary rules, testing requirements, and PR format before touching any code.

## Key facts

- `gps/` — GPS distance calculations using the Haversine formula (port 8101).
- `wingfoil/` — French wingfoil spots database with 365-day conditions (port 8102).
- Each server is an independent FastMCP server (Python 3.14+, `uv`, `pre-commit`).
- All servers are containerized and started via `docker compose up`.
- Run `make setup` to initialize all repos (uv sync, pre-commit install). Run once per clone.
- Run `make test` to test all repos, `make lint` to lint all repos.
- Custom Claude slash commands live in `.claude/skills/` — run `./install.sh` to activate them.
- Subagents live in `.claude/agents/` and are invoked automatically by Claude Code:
  - **code-reviewer** — reviews code against AGENTS.md standards, runs pre-commit, fixes docstrings and annotations.
  - **git-ops** — handles git operations, PR creation with correct format, pre-commit validation.
  - **mcp-builder** — scaffolds a new MCP server with all required files (alternative to `/new-server`).
  - **test-writer** — generates and maintains tests, enforces fixtures and the 100% coverage gate.
  - **daily** — generates standup summaries (agent version of `/daily`).
- Claude Code hooks are configured in `.claude/settings.local.json`:
  - **PreToolUse Bash** — blocks any `git commit --no-verify` attempt.
  - **Stop** — reminds to run `make test && make lint` at end of session.
- `/new-server <name> <description> <port>` — scaffold a new MCP server following all monorepo standards.
- `/pr` — create a PR with the correct title, description, coverage and complexity scores.
- `/daily` — generate a standup summary of yesterday's work across all repos.
