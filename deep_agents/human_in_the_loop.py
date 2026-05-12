from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.utils.uuid import uuid7
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from dotenv import load_dotenv

load_dotenv(verbose=True)


@tool
def delete_file(path: str) -> str:
    """Delete a file from the filesystem."""
    return f"Deleted {path}"


@tool
def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    return f"Contents of {path}"


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return f"Sent email to {to}"


# Checkpointer is REQUIRED for human-in-the-loop
checkpointer = MemorySaver()

# <|think|>
system_prompt = """
        You are a helpful assistant that performs actions based on user instructions.
        Some actions require human approval before execution.
        Always call the relevant tool when the user asks for an action.
        """

print("Creating deep agent with human-in-the-loop tools...")

agent = create_deep_agent(
    model="google_genai:gemini-3.1-flash-lite", # gemini-3.1-flash-lite gemma-4-31b-it
    # system_prompt=system_prompt,
    tools=[delete_file, read_file, send_email],
    interrupt_on={
        "delete_file": True,  # Default: approve, edit, reject, respond
        "read_file": False,  # No interrupts needed
        "send_email": {"allowed_decisions": ["approve", "reject"]},  # No editing
    },
    checkpointer=checkpointer,  # Required!
)

config = RunnableConfig(configurable={"thread_id": str(uuid7())})

instruction = input(
    "Enter an instruction for the agent (read file, delete file, send email): "
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": instruction}]},
    config=config,
    version="v2",
)

if result.interrupts:
    # Extract interrupt information
    interrupt_value = result.interrupts[0].value
    action_requests = interrupt_value["action_requests"]
    review_configs = interrupt_value["review_configs"]

    # Create a lookup map from tool name to review config
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}

    print("config_map: ", config_map)

    decisions = []

    # Display the pending actions to the user
    for action in action_requests:
        review_config = config_map[action["name"]]
        print(f"Tool: {action['name']}")
        print(f"Arguments: {action['args']}")
        print(f"Allowed decisions: {review_config['allowed_decisions']}")

        # Get user decisions (one per action_request, in order)
        decision = (
            input(
                f"Enter your decision for the {action['name']} action (approve/reject): "
            )
            .strip()
            .lower()
        )

        if decision not in config_map[action["name"]]["allowed_decisions"]:
            print("Invalid decision. Defaulting to 'reject'.")
            decision = "reject"

        decisions.append({"type": decision})

    # Resume execution with decisions
    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config,
        version="v2",
    )

final_message = result.value["messages"][-1].content[-1]

if isinstance(final_message, str):
    print("Result string: ", final_message)
else:
    key = final_message.get("type", "unknown")
    print(f"Result ({key}): ", final_message[key])
