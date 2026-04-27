"""Weather agent example."""

import argparse
import random

from langchain.agents import create_agent


CITY_TEMPERATURE_RANGES: dict[str, tuple[int, int]] = {
    "dubai": (24, 39),
    "london": (7, 19),
    "new york": (5, 27),
    "singapore": (26, 33),
    "sydney": (10, 26),
    "tokyo": (8, 26),
}


def get_city_argument() -> str:
    parser = argparse.ArgumentParser(description="Get a generated weather report.")
    parser.add_argument("city", help="City to generate the weather for")
    args = parser.parse_args()
    return args.city.strip()


def get_temperature_range(city: str) -> tuple[int, int]:
    return CITY_TEMPERATURE_RANGES.get(city.strip().lower(), (12, 28))


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    low_bound, high_bound = get_temperature_range(city)
    high_temperature = random.randint(low_bound + 3, high_bound)
    low_temperature = random.randint(low_bound, high_temperature - 2)
    conditions = random.choice(["sunny", "partly cloudy", "cloudy", "breezy"])
    return (
        f"Today's weather in {city} is {conditions} with a high of "
        f"{high_temperature}°C and a low of {low_temperature}°C."
    )


def extract_response_text(messages: list) -> str:
    tool_response: str | None = None

    for message in reversed(messages):
        content_blocks = getattr(message, "content_blocks", None) or []
        text_parts = [
            block["text"].strip()
            for block in content_blocks
            if block.get("type") == "text" and block.get("text", "").strip()
        ]

        if not text_parts:
            continue

        text = "\n".join(text_parts)

        if getattr(message, "type", None) == "tool" and tool_response is None:
            tool_response = text
            continue

    if tool_response is not None:
        return tool_response

    for message in reversed(messages):
        if getattr(message, "type", None) != "ai":
            continue

        content_blocks = getattr(message, "content_blocks", None) or []
        text_parts = [
            block["text"].strip()
            for block in content_blocks
            if block.get("type") == "text" and block.get("text", "").strip()
        ]

        if not text_parts:
            continue

        text = "\n".join(text_parts)

        if text.startswith("<|python_tag|>"):
            continue

        if text.startswith('{"name":'):
            continue

        return text

    msg = "No displayable response found in agent output."
    raise ValueError(msg)


agent = create_agent(
    model="ollama:llama3.2:3b",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

city = get_city_argument()

result = agent.invoke(
    {"messages": [{"role": "user", "content": f"What's the weather in {city}?"}]}
)

print(extract_response_text(result["messages"]))
