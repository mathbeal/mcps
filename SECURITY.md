# Security Policy

## Reporting a vulnerability

This is a personal project. If you find a security issue, open a GitHub issue marked **[SECURITY]** or contact the owner directly.

## Secret handling

- Never commit `.env` files — they are gitignored in every server directory.
- All secrets (API keys, IBANs, tokens) must be loaded from environment variables, never hardcoded.
- Logs must never emit secrets, even in exception handlers — enforced by the `code-reviewer` agent.
