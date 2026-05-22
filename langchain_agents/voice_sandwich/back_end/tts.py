import asyncio
import logging
from typing import Any, AsyncIterator, cast

from langchain_agents.voice_sandwich.back_end.elevenlabs import el_client

logger = logging.getLogger(__name__)


async def tts_stream(
    text_stream: AsyncIterator[str],
) -> AsyncIterator[bytes]:
    """Convert each agent response text into ElevenLabs PCM audio chunks.

    This avoids waiting for a long-lived realtime session to finalize before
    audio is emitted to the websocket client.
    """
    text_to_speech_client = cast(Any, el_client.text_to_speech)

    def synthesize_once(text: str) -> list[bytes]:
        audio_stream = text_to_speech_client.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",
            text=text,
            model_id="eleven_flash_v2_5",
            output_format="pcm_16000",
            voice_settings=None,
        )
        return [chunk for chunk in audio_stream if isinstance(chunk, bytes) and chunk]

    async for text in text_stream:
        cleaned_text = text.strip()
        if not cleaned_text:
            continue

        try:
            audio_chunks = await asyncio.to_thread(synthesize_once, cleaned_text)
        except Exception:
            logger.exception("TTS synthesis failed for text: %r", cleaned_text)
            continue

        for chunk in audio_chunks:
            yield chunk
