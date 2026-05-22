import logging
from typing import AsyncIterator

from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.utils.uuid import uuid7
from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

logger = logging.getLogger(__name__)

#model = ChatGoogleGenerativeAI(model="gemma-4-31b-it")
model = init_chat_model(model="openai:gpt-5.4-mini", temperature=0.0)


# Define agent tools
def add_to_order(item: str, quantity: int) -> str:
    """Add an item to the customer's sandwich order."""
    return f"Added {quantity} x {item} to the order."


def confirm_order(order_summary: str) -> str:
    """Confirm the final order with the customer."""
    return f"Order confirmed: {order_summary}. Sending to kitchen."


# Create agent with tools and memory
agent = create_agent(
    model=model,
    tools=[add_to_order, confirm_order],
    system_prompt="""You are a helpful sandwich shop assistant.
    Your goal is to take the user's order. Be concise and friendly.
    Do NOT use emojis, special characters, or markdown.
    Your responses will be read by a text-to-speech engine.""",
    checkpointer=InMemorySaver(),
)


def _append_fragment(buffer: str, fragment: str) -> str:
    if not buffer:
        return fragment
    if buffer.endswith((" ", "\n", "\t")) or fragment.startswith((" ", "\n", "\t", ".", ",", "!", "?", ":", ";", "'", '"', ")", "]")):
        return f"{buffer}{fragment}"
    return f"{buffer} {fragment}"


async def agent_stream(
    text_stream: AsyncIterator[str],
) -> AsyncIterator[str]:
    """
    Transform stream: Voice Events → Voice Events (with Agent Responses)

    Passes through all upstream events and adds agent_chunk events
    when processing STT transcripts.
    """
    # Generate unique thread ID for conversation memory
    thread_id = str(uuid7())

    async for transcript in text_stream:
        cleaned_transcript = transcript.strip()
        if not cleaned_transcript:
            continue

        # Stream agent response with conversation context
        stream = agent.astream(
            {"messages": [HumanMessage(content=cleaned_transcript)]},
            {"configurable": {"thread_id": thread_id}},
            stream_mode="messages",
        )

        try:
            # Aggregate model chunks into a single TTS-ready response.
            full_response = ""
            async for message, _ in stream:
                if isinstance(message, AIMessageChunk):
                    chunk_text = message.text
                    if chunk_text and chunk_text.strip():
                        full_response = _append_fragment(full_response, chunk_text)

            if full_response.strip():
                yield full_response.strip()
        except Exception:
            logger.exception("Agent stream failed for transcript: %r", cleaned_transcript)
            yield "Sorry, I had trouble processing that. Please try again."
