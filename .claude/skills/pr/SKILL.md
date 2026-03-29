---
name: pr
description: Create a pull request following the monorepo PR format defined in AGENTS.md — [AI] title, <5 lines description, coverage and complexity scores.
---

Create a pull request for the current branch following the ~/mcps monorepo standards.

## Pre-flight checks

Before creating the PR, verify:

1. All tests pass: `make test`
2. All linters pass: `make lint`
3. No uncommitted changes: `git status`

If any check fails, stop and fix the issues before proceeding.

## Collect metrics

For each repo with changes, run:

```bash
cd <repo>
uv run pytest --cov --cov-report=term-missing 2>&1 | grep "TOTAL"
uv run pylint <changed_files> --max-complexity=19 2>&1 | grep "complexity"
```

Extract:
- **Coverage score** — percentage from pytest-cov TOTAL line
- **Max complexity** — highest cyclomatic complexity reported by pylint

## PR format

**Title:** `[AI]: <concise title in english>`

**Body:**
```
## Changes
- <change 1>
- <change 2>
- <change 3>  (5 lines max total)

Coverage: <xx>% | Max complexity: <yy>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Create the PR

```bash
git push -u origin <current-branch>
gh pr create --title "[AI]: <title>" --body "$(cat <<'EOF'
## Changes
- <change 1>
...

Coverage: <xx>% | Max complexity: <yy>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Return the PR URL when done.
