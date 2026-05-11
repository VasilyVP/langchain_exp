# AGENTS.md

This file helps AI coding agents work effectively in this repository.

## Project Snapshot

- Language: Python 3.14+
- Package/dependency manager: `uv` (lockfile: `uv.lock`)
- Type checking config: `pyrightconfig.json` (`typeCheckingMode: standard`)
- Main code areas:
  - `deep_agents/`: deep-agent workflows and Slack/Discord tool wrappers
  - `langchain/`: standalone LangChain example scripts (for example weather agent)

## Quick Start

1. Install dependencies:
  - `uv sync`
2. Activate virtual environment when needed:
  - PowerShell: `.venv/Scripts/Activate.ps1`
3. Prefer running scripts through `uv run`:
  - `uv run python langchain/weather_agent.py london`
  - `uv run python deep_agents/analysis.py`

## Validation Commands

- Type checking:
  - `pyright`
- If `pyright` is not available globally, use:
  - `uv run pyright`

## Environment and Secrets

- This repo relies on environment variables loaded from `.env` (via `python-dotenv`).
- Never print, paste, or commit secret values from `.env`.
- Required variables depend on script/tool:
  - `deep_agents/analysis.py` and `langchain_daytona` flow: `DAYTONA_API_KEY`
  - `deep_agents/slack.py`: `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID` (validated at import time)
  - `deep_agents/discord.py`: `DISCORD_WEBHOOK_URL`
  - LLM integrations may require provider keys (for example Google/LangSmith).

## Code Conventions

- Keep changes small and local; avoid broad refactors unless requested.
- Preserve type hints and keep Pyright clean under current settings.
- Follow existing module boundaries:
  - Add deep-agent integration/tooling code in `deep_agents/`.
  - Add simple LangChain examples in `langchain/`.
- Use descriptive errors for external API/tool failures (webhooks, Slack uploads, sandbox operations).

## Known Pitfalls

- `deep_agents/slack.py` raises on import when Slack env vars are missing. Avoid importing it in contexts where Slack is not configured.
- `deep_agents/analysis.py` creates a Daytona sandbox and performs networked operations; treat it as an integration script, not a unit-test target.
- `langchain/weather_agent.py` expects a required positional CLI arg (`city`).

## Practical Guidance for Agents

- Before editing, inspect the target script end-to-end because these files are executable examples with top-level runtime logic.
- When adding new integrations, gate failures with clear exceptions and avoid leaking secrets in logs.
- Prefer adding narrowly scoped helper functions over introducing new framework layers in this small codebase.
