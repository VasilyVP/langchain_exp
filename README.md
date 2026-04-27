# Weather Agent

Small LangChain example that asks for a city name and returns a randomized weather summary with temperatures in a realistic range for that city.

## Requirements

- Python managed through `uv`
- Ollama installed locally
- The `llama3.2:3b` model available in Ollama

## Setup

Start Ollama and make sure the model used by the script is available:

```powershell
ollama serve
ollama pull llama3.2:3b
```

Install project dependencies:

```powershell
uv sync
```

## Run

Run the script from the project root:

```powershell
uv run python .\src\weather_agent.py
```

The script will prompt for a city:

```text
Enter a city:
```

Example session:

```text
Enter a city: London
Today's weather in London is sunny with a high of 19°C and a low of 10°C.
```

## Notes

- Temperatures are randomized on each run.
- Known cities use city-specific temperature ranges.
- Unknown cities fall back to a generic `0°C` to `30°C` range.
