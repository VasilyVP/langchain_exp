import os
from deepagents.backends import BackendProtocol
from langchain.tools import tool
from slack_sdk import WebClient

slack_token = os.getenv("SLACK_BOT_TOKEN")
channel_id = os.getenv("SLACK_CHANNEL_ID", None)

slack_client = WebClient(token=slack_token)

if not channel_id or not slack_token:
    raise ValueError(
        "SLACK_CHANNEL_ID and SLACK_BOT_TOKEN must be set in environment variables."
    )


def make_slack_send_message(backend: BackendProtocol):
    @tool(parse_docstring=True)
    def slack_send_message(text: str, file_path: str | None = None) -> str:
        """Send message, optionally including attachments such as images.

        Args:
            text: (str) text content of the message
            file_path: (str) file path of attachment in the filesystem.
        """
        try:
            if not file_path:
                slack_client.chat_postMessage(channel=str(channel_id), text=text)
            else:
                fp = backend.download_files([file_path])
                file_content = fp[0].content if fp else None
                if not file_content:
                    raise ValueError(f"No file returned for path: {file_path}")

                slack_client.files_upload_v2(
                    channel=channel_id,
                    content=file_content,
                    initial_comment=text,
                )

            return "Message sent."
        except Exception as e:
            print(f"Error sending message to Slack: {e}")
            return f"Failed to send message: {e}"

    return slack_send_message
