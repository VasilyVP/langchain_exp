import asyncio
import base64
import contextlib
import logging
from typing import Any, AsyncIterator, cast

from elevenlabs.realtime.connection import RealtimeEvents
from elevenlabs.realtime.scribe import AudioFormat, CommitStrategy

from langchain_agents.voice_sandwich.back_end.elevenlabs import el_client

logger = logging.getLogger(__name__)

MIN_MEANINGFUL_CHARS = 2


def _is_likely_garbled_text(text: str) -> bool:
    """Detect common mojibake/replacement-character transcripts.

    We do not rely on one fixed marker because providers can emit different
    garbled patterns depending on transport/decoding behavior.
    """
    stripped = text.strip()
    if not stripped:
        return True

    # Unicode replacement character indicates failed decoding.
    replacement_count = stripped.count("\ufffd")
    if replacement_count >= MIN_MEANINGFUL_CHARS:
        return True

    # If mostly punctuation/symbols and no letters/digits, it's usually noise.
    alnum_count = sum(ch.isalnum() for ch in stripped)
    if alnum_count == 0 and len(stripped) >= MIN_MEANINGFUL_CHARS:
        return True

    return False


def _extract_event_text(payload: object) -> str:
    """Extract transcript text from realtime event payloads."""
    if not isinstance(payload, dict):
        return ""

    text = payload.get("transcript")
    if not isinstance(text, str):
        text = payload.get("text")

    if isinstance(text, str):
        return text.strip()
    return ""


async def stt_stream(
    audio_stream: AsyncIterator[bytes],
) -> AsyncIterator[str]:
    """Transcribe async audio chunks with ElevenLabs realtime STT over WebSocket."""

    speech_to_text_client = cast(Any, el_client.speech_to_text)
    connection = await speech_to_text_client.realtime.connect({
        "model_id": "scribe_v2_realtime",
        "audio_format": AudioFormat.PCM_16000,
        "sample_rate": 16000,
        "commit_strategy": CommitStrategy.VAD,
        "include_timestamps": True,
        "language_code": None,
    })
    logger.info("STT realtime connection established")
    events: asyncio.Queue[str | Exception] = asyncio.Queue()

    def on_transcript(payload: object) -> None:
        text = _extract_event_text(payload)
        if _is_likely_garbled_text(text):
            logger.debug("STT ignored likely garbled transcript: %r", text)
            return
        if text:
            events.put_nowait(text)

    def on_error(payload: object) -> None:
        if isinstance(payload, dict):
            message = payload.get("error")
            details = message if isinstance(message, str) else str(payload)
        else:
            details = str(payload)
        events.put_nowait(RuntimeError(f"ElevenLabs realtime STT error: {details}"))

    connection.on(RealtimeEvents.COMMITTED_TRANSCRIPT, on_transcript)
    connection.on(RealtimeEvents.ERROR, on_error)

    async def send_audio() -> None:
        async for chunk in audio_stream:
            if not chunk:
                continue

            encoded_chunk = base64.b64encode(chunk).decode("ascii")
            await connection.send({"audio_base_64": encoded_chunk})
            logger.debug("STT sent audio chunk size=%d", len(chunk))

    sender_task = asyncio.create_task(send_audio())

    try:
        while True:
            event_task = asyncio.create_task(events.get())
            done, pending_tasks = await asyncio.wait(
                {event_task, sender_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            if sender_task in done:
                for pending_task in pending_tasks:
                    pending_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await event_task

                sender_exception = sender_task.exception()
                if sender_exception is not None:
                    raise sender_exception
                break

            event = event_task.result()
            if isinstance(event, Exception):
                raise event

            logger.info("STT transcript: %s", event)
            yield event
    finally:
        sender_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sender_task
        await connection.close()
        logger.info("STT realtime connection closed")
