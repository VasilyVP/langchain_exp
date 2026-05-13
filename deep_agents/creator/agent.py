import sys
import os
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from dotenv import load_dotenv
from langchain.messages import HumanMessage
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig

from deep_agents.creator.web_search_tool import generate_cover, generate_social_image
from deep_agents.creator.helpers import load_subagents

load_dotenv(verbose=True)

# Enable LangSmith tracing with a default project name if not set in the environment
os.environ.setdefault("LANGSMITH_PROJECT", "deep-agents-creator")

DIR = Path(__file__).resolve().parent

DATA_DIR = Path(__file__).resolve().with_name("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

model = init_chat_model(
    model="google_genai:gemma-4-31b-it"
)  # "google_genai:gemini-3.1-flash-lite")


def create_content_writer():
    """Create a content writer agent configured by filesystem files."""
    return create_deep_agent(
        model=model,
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=[generate_cover, generate_social_image],
        subagents=load_subagents(DIR / "subagents.yaml"),
        backend=FilesystemBackend(root_dir=DATA_DIR, virtual_mode=True),
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py <task description>")
        sys.exit(1)

    task = " ".join(sys.argv[1:])

    print(f"Invoking content writer agent with task: {task}\n")

    try:
        agent = create_content_writer()
        config: RunnableConfig = {
            "configurable": {"thread_id": "content-builder-demo"},
            "run_name": "content-writer-stream",
            "tags": ["deep-agents", "creator", "streaming"],
            "metadata": {"entrypoint": "deep_agents.creator.agent"},
        }

        for chunk in agent.stream(
            {"messages": [HumanMessage(content=task)]},
            config=config,
            stream_mode="updates",
        ):
            for node, update in chunk.items():
                if not update or not (messages := update.get("messages")):
                    continue

                # Some versions return raw lists, others return wrappers with a .value list.
                msg_list = messages.value if hasattr(messages, "value") else messages
                if not isinstance(msg_list, list):
                    continue

                for msg in msg_list:
                    if hasattr(msg, "content") and msg.content:
                        print(f"[{node}] {msg.content}")
    except Exception as e:
        print(f"Error during agent execution: {e}")
