# AGENTS.md

This file helps AI coding agents work effectively in this repository.

## Project Snapshot

- Language: Python 3.14+
- Also contains TypeScript/Node components for selected integrations
- Package/dependency manager: `uv` (lockfile: `uv.lock`)
- Type checking config: `pyrightconfig.json` (`typeCheckingMode: standard`)
- Main code areas:
  - `langchain_agents/`: LangChain examples (weather, RAG, semantic search, SQL, voice sandwich, support bot)
  - `deep_agents/`: Deep Agents workflows and integration tools (research, creator, Slack/Discord, Daytona analysis)
  - `.agents/skills/`: reusable skills for LangChain/LangGraph/Deep Agents workflows

## Quick Start

1. Install dependencies:
  - `uv sync`
2. Prefer running scripts through `uv run`:
  - `uv run python langchain_agents/weather_agent.py london`
  - `uv run python langchain_agents/semantic_search/agent.py`
  - `uv run python deep_agents/analysis.py`
3. Useful Make targets:
  - `make test`
  - `make list_models`
  - `make voice-sandwich`

## Validation Commands

- Type checking:
  - `pyright`
- If `pyright` is not available globally, use:
  - `uv run pyright`
- Unit tests:
  - `uv run python -m unittest discover -s langchain_agents/voice_sandwich/tests -p "test*.py" -v`

## Environment and Secrets

- This repo relies on environment variables loaded from `.env` (via `python-dotenv`).
- Never print, paste, or commit secret values from `.env`.
- Required variables depend on script/tool:
  - `deep_agents/analysis.py` and Daytona flows: `DAYTONA_API_KEY`
  - `deep_agents/slack.py`: `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID` (validated at import time)
  - `deep_agents/discord.py`: `DISCORD_WEBHOOK_URL`
  - `langchain_agents/voice_sandwich/back_end/*`: ElevenLabs credentials
  - LLM integrations may require provider keys (for example Google/LangSmith).

## Code Conventions

- Keep changes small and local; avoid broad refactors unless requested.
- Preserve type hints and keep Pyright clean under current settings.
- Follow existing module boundaries:
  - Add Deep Agents integration/tooling code in `deep_agents/`.
  - Add LangChain examples and demos in `langchain_agents/`.
- Use descriptive errors for external API/tool failures (webhooks, Slack uploads, sandbox operations).
- Prefer executable script patterns already used in this repo (many files are intended to run directly).

## Known Pitfalls

- `deep_agents/slack.py` raises on import when Slack env vars are missing. Avoid importing it in contexts where Slack is not configured.
- `deep_agents/analysis.py` creates a Daytona sandbox and performs networked operations; treat it as an integration script, not a unit-test target.
- `langchain_agents/weather_agent.py` expects a required positional CLI arg (`city`).
- `deep_agents/creator/AGENTS.md` is a persona/system-prompt file for the creator agent, not project-level coding instructions.
- This repository mixes Python and TypeScript workflows; `uv` only manages Python dependencies.

## Practical Guidance for Agents

- Before editing, inspect the target script end-to-end because these files are executable examples with top-level runtime logic.
- When adding new integrations, gate failures with clear exceptions and avoid leaking secrets in logs.
- Prefer adding narrowly scoped helper functions over introducing new framework layers in this small codebase.
- Use `langgraph.json` as the source of truth for local LangGraph graph entry points.
