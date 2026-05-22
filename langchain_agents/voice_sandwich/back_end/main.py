from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from granian import Granian
from granian.constants import Interfaces
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
from langchain_agents.voice_sandwich.back_end.stt import stt_stream
from langchain_agents.voice_sandwich.back_end.agent import agent_stream
from langchain_agents.voice_sandwich.back_end.tts import tts_stream

app = FastAPI()


# Use in WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client accepted connection")

    async def websocket_audio_stream():
        """Yield audio bytes from WebSocket."""
        while True:
            try:
                data = await websocket.receive_bytes()
            except WebSocketDisconnect:
                raise
            yield data

    async def logged_agent_text_stream():
        async for agent_chunk in agent_stream(stt_stream(websocket_audio_stream())):
            logger.info("AGENT: %s", agent_chunk)
            yield agent_chunk

    try:
        # Pipeline: microphone audio -> STT transcript -> agent text -> TTS audio.
        async for audio_chunk in tts_stream(logged_agent_text_stream()):
            await websocket.send_bytes(audio_chunk)
    except WebSocketDisconnect:
        return
    except Exception:
        logger.exception("Voice pipeline failed")
    finally:
        logger.info("WebSocket client disconnected")


if __name__ == "__main__":
    server = Granian(
        "langchain_agents.voice_sandwich.back_end.main:app",
        port=8000,
        reload=True,
        interface=Interfaces.ASGI,
    )
    server.serve()
