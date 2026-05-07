import os
from deepagents.backends import BackendProtocol
from langchain.tools import tool
import requests


def make_discord_send_message(backend: BackendProtocol):
    @tool(parse_docstring=True)
    def discord_send_message(text: str, file_path: str | None = None) -> str | None:
        message = None
        fp = None

        if not file_path:
            message = text
        else:
            fp = backend.download_files([file_path])
            if not fp:
                raise ValueError(f"No file returned for path: {file_path}")

            content = fp[0].content
            if isinstance(content, bytes):
                try:
                    message = content.decode("utf-8")
                except UnicodeDecodeError:
                    # Keep message delivery resilient for files with legacy encodings.
                    message = content.decode("latin-1", errors="replace")
            else:
                message = str(content)

        data = {"content": message}
        try:
            response = requests.post(
                str(os.getenv("DISCORD_WEBHOOK_URL") or ""), json=data
            )

            if response.status_code != 204:
                raise Exception(
                    f"Failed to send message to Discord: {response.status_code} - {response.text}"
                )

            print(f"Discord response.text: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending message to Discord: {e}")
            return None

        return response.text

    return discord_send_message
