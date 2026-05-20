from dotenv import load_dotenv

load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
from langchain.agents.middleware.types import _InputAgentState
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langchain_agents.sql.db_setup import db_path
from langchain_agents.sql.prompt import get_prompt
from langchain_agents.sql.utils import collect_decisions

# question = "Which genre on average has the longest tracks?"

try:
    question = input("Enter your question about the database: ")
    if not question:
        print("No question provided. Exiting.")
        exit(0)

    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    model = ChatGoogleGenerativeAI(model="gemma-4-31b-it")
    toolkit = SQLDatabaseToolkit(db=db, llm=model)

    config: RunnableConfig = {"configurable": {"thread_id": "1"}}

    agent = create_agent(
        model,
        tools=toolkit.get_tools(),
        system_prompt=get_prompt(db.dialect, 5),
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={"sql_db_query": True},
                description_prefix="Tool execution pending approval",
            ),
        ],
        checkpointer=InMemorySaver(),
    )

    run_input: _InputAgentState | Command = {
        "messages": [{"role": "user", "content": question}]
    }

    stop_requested = False
    while True:
        interrupted = False
        for step in agent.stream(
            run_input,
            config,
            stream_mode="values",
        ):
            if "__interrupt__" in step:
                interrupt = step["__interrupt__"][0]
                decisions = collect_decisions(interrupt.value)
                if any(decision.get("type") == "reject" for decision in decisions):
                    print("Execution rejected. Stopping.")
                    stop_requested = True
                    break
                run_input = Command(resume={"decisions": decisions})
                interrupted = True
                break

            if "messages" in step:
                step["messages"][-1].pretty_print()

        if stop_requested or not interrupted:
            break

except Exception as e:
    print(f"An error occurred: {e}")
