import asyncio
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from typing import AsyncIterator

from dotenv import load_dotenv

load_dotenv()

SAMPLE_RECORDING = Path(__file__).with_name("recording.m4a")
EXPECTED_TRANSCRIPT = "one two three four five six seven"


def _normalize_transcript(text: str) -> str:
    lowered = text.lower()
    collapsed = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return " ".join(collapsed.split())


def _decode_m4a_to_pcm_16khz(path: Path) -> bytes:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise unittest.SkipTest("ffmpeg is required for STT integration test")

    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-f",
        "s16le",
        "-ac",
        "1",
        "-ar",
        "16000",
        "pipe:1",
    ]

    result = subprocess.run(command, check=True, capture_output=True)
    if not result.stdout:
        raise RuntimeError("Decoded PCM output is empty")
    return result.stdout


async def _iter_chunks(data: bytes, chunk_size: int = 3200) -> AsyncIterator[bytes]:
    for start in range(0, len(data), chunk_size):
        yield data[start : start + chunk_size]
        await asyncio.sleep(0)


class TestSttStreamIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_stt_stream_transcribes_sample_recording(self) -> None:
        if not os.environ.get("ELEVENLABS_API_KEY"):
            self.skipTest("ELEVENLABS_API_KEY is required for STT integration test")

        if not SAMPLE_RECORDING.exists():
            self.fail(f"Sample recording was not found at {SAMPLE_RECORDING}")

        pcm_audio = _decode_m4a_to_pcm_16khz(SAMPLE_RECORDING)

        from langchain_agents.voice_sandwich.stt import stt_stream

        parts: list[str] = []
        async for transcript_part in stt_stream(_iter_chunks(pcm_audio)):
            parts.append(transcript_part)

        final_text = _normalize_transcript(" ".join(parts))
        self.assertEqual(final_text, EXPECTED_TRANSCRIPT)


if __name__ == "__main__":
    unittest.main()
