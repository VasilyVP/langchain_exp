import os
import io
import csv
from daytona import Daytona, DaytonaConfig, CreateSandboxFromSnapshotParams
from dotenv import load_dotenv
from langchain_daytona import DaytonaSandbox

load_dotenv(verbose=True)

# from deep_agents.discord import make_discord_send_message
from langchain_core.runnables import RunnableConfig
from deep_agents.slack import make_slack_send_message
from langchain_core.utils.uuid import uuid7
from langgraph.checkpoint.memory import InMemorySaver
from deepagents import create_deep_agent

print("Setting up Daytona backend...")

daytona_config = DaytonaConfig(api_key=os.getenv("DAYTONA_API_KEY"))
sandbox = Daytona(config=daytona_config).create(
    CreateSandboxFromSnapshotParams(ephemeral=True)
)
backend = DaytonaSandbox(sandbox=sandbox)

print("Daytona backend is ready.")

try:
    # Dataset
    data = [
        ["Date", "Product", "Units Sold", "Revenue"],
        ["2025-08-01", "Widget A", 10, 250],
        ["2025-08-02", "Widget B", 5, 125],
        ["2025-08-03", "Widget A", 7, 175],
        ["2025-08-04", "Widget C", 3, 90],
        ["2025-08-05", "Widget B", 8, 200],
    ]

    text_buf = io.StringIO()
    writer = csv.writer(text_buf)
    writer.writerows(data)
    csv_bytes = text_buf.getvalue().encode("utf-8")
    text_buf.close()

    # Upload to backend
    backend.upload_files([("/home/daytona/data/sales_data.csv", csv_bytes)])

    print("Dataset uploaded to backend.")

    checkpointer = InMemorySaver()

    agent = create_deep_agent(
        model="google_genai:gemma-4-31b-it",  # gemini-3.1-flash-lite
        tools=[make_slack_send_message(backend)],
        backend=backend,
        checkpointer=checkpointer,
    )

    thread_id = str(uuid7())
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    input_message = {
        "role": "user",
        "content": (
            "Analyze /home/daytona/data/sales_data.csv and generate a beautiful plot. "
            "When finished, send your analysis and the plot to Slack using the tool."
        ),
    }

    print("Starting agent...")

    for step in agent.stream(
        {"messages": [input_message]},
        config,
        stream_mode="updates",
    ):
        for _, update in step.items():
            if (
                update
                and (messages := update.get("messages"))
                and isinstance(messages, list)
            ):
                for message in messages:
                    message.pretty_print()
except Exception as e:
    print(f"Error during agent execution: {e}")
finally:
    sandbox.stop()
    print("Sandbox stopped.")
