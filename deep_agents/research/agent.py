from datetime import datetime

from pathlib import Path
from time import sleep
from deepagents import create_deep_agent, SubAgent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langgraph.types import Overwrite
from deepagents.backends.filesystem import FilesystemBackend

from deep_agents.research.tavily_search_tool import tavily_search
from deep_agents.research.prompts import (
    RESEARCH_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
    RESEARCHER_INSTRUCTIONS,
)

max_concurrent_research_units = 3
max_researcher_iterations = 3

current_date = datetime.now().strftime("%Y-%m-%d")

INSTRUCTIONS = (
    RESEARCH_WORKFLOW_INSTRUCTIONS
    + "\n\n"
    + "=" * 80
    + "\n\n"
    + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
        max_concurrent_research_units=max_concurrent_research_units,
        max_researcher_iterations=max_researcher_iterations,
    )
)

research_sub_agent = SubAgent(
    name="research-agent",
    description="Delegate research to the sub-agent. Give one topic at a time.",
    system_prompt=RESEARCHER_INSTRUCTIONS.format(date=current_date),
    tools=[tavily_search],
)

model = init_chat_model(model="google_genai:gemini-3.1-flash-lite", temperature=0.0)

storage_dir = Path(__file__).resolve().with_name("storage")
storage_dir.mkdir(parents=True, exist_ok=True)


def clean_storage_files() -> None:
    """Remove only the generated report/request files from storage."""
    for file_name in ("final_report.md", "research_request.md"):
        file_path = storage_dir / file_name
        if file_path.exists() and file_path.is_file():
            file_path.unlink()


agent = create_deep_agent(
    model=model,
    backend=FilesystemBackend(root_dir=str(storage_dir), virtual_mode=True),
    tools=[tavily_search],
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent],
)

if __name__ == "__main__":
    clean_storage_files()
    print("Agent initialized. Starting research task...")

    user_request = input("Enter your research question: ")
    if not user_request.strip():
        print("No input provided. Exiting.")
        exit(0)

    for chunk in agent.stream(
        {"messages": [HumanMessage(content=user_request)]},
        stream_mode="updates",
    ):
        for node, update in chunk.items():
            if not update or not (messages := update.get("messages")):
                continue
            msg_list = messages.value if isinstance(messages, Overwrite) else messages
            for msg in msg_list:
                if hasattr(msg, "content") and msg.content:
                    print(msg.content)
