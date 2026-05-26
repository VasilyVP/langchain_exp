# langchain_exp

Examples for building practical AI workflows with LangChain, LangGraph, and Deep Agents.

## Highlights

- Tool-calling agents
- RAG and semantic search
- SQL agents with human approval
- Deep Agent orchestration with subagents
- Voice pipeline: STT -> Agent -> TTS
- Discord and Slack integration examples

## Tech stack

- Python 3.14+
- uv for Python dependency management
- Node.js or Bun for TypeScript/JS examples

## Quick start

```bash
# 1) Install Python deps
uv sync

# 2) Install JS deps (pick one)
bun install
# or
npm install

# 3) Add a .env file with the keys needed by the example you run

# 4) Run a sample
uv run python langchain_agents/weather_agent.py london
```

## Useful commands

```bash
make list_models
make test
make voice-sandwich

uv run pyright
```

## Example entry points

```bash
# RAG
uv run python langchain_agents/rag/agent.py --type auto

# SQL agent
uv run python langchain_agents/sql/agent.py

# Deep research agent
uv run python deep_agents/research/agent.py

# Voice app backend
uv run python -m langchain_agents.voice_sandwich.back_end.main
```

## Environment variables

Common keys used across examples:

- GOOGLE_API_KEY
- OPENAI_API_KEY
- LANGSMITH_API_KEY
- DAYTONA_API_KEY
- SLACK_BOT_TOKEN
- SLACK_CHANNEL_ID
- DISCORD_WEBHOOK_URL
- DISCORD_BOT_TOKEN
- DISCORD_APPLICATION_ID
- DISCORD_CHANNEL_ID

Use only the variables required by the specific script you run.

## Project layout

- langchain_agents: LangChain and LangGraph examples
- deep_agents: Deep Agent workflows and integrations
- .agents/skills: reusable skill instructions

## Notes

- Some integrations validate env vars at import/startup time.
- The repository includes both Python and TypeScript workflows.

## License

No license file is currently included.
