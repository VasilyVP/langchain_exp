import os
from elevenlabs.client import ElevenLabs

el_client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
