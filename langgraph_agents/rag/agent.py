from dotenv import load_dotenv
from pathlib import Path

load_dotenv(verbose=True)

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.graph import MessagesState
from IPython import get_ipython
from IPython.display import Image, display
from langchain_core.messages import HumanMessage

from langgraph_agents.rag.model import chat_model
from langgraph_agents.rag.retriever_tool import retriever_tool
from langgraph_agents.rag.grade_documents import grade_documents
from langgraph_agents.rag.rewrite_question import rewrite_question
from langgraph_agents.rag.generate_answer import generate_answer


def generate_query_or_respond(state: MessagesState):
    """Call the model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply respond to the user.
    """
    response = chat_model.bind_tools([retriever_tool]).invoke(state["messages"])
    return {"messages": [response]}


workflow = StateGraph(MessagesState)

# Define the nodes we will cycle between
workflow.add_node(generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([retriever_tool]))
workflow.add_node(rewrite_question)
workflow.add_node(generate_answer)

workflow.add_edge(START, "generate_query_or_respond")


# Route based on whether the model requested tool calls.
def route_on_tool_calls(state: MessagesState):
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


# Decide whether to retrieve
workflow.add_conditional_edges(
    "generate_query_or_respond",
    # Assess LLM decision (call `retriever_tool` tool or respond to the user)
    route_on_tool_calls,
    {
        # Translate the condition outputs to nodes in our graph
        "tools": "retrieve",
        END: END,
    },
)

# Edges taken after the `action` node is called.
workflow.add_conditional_edges(
    "retrieve",
    # Assess agent decision
    grade_documents,
)
workflow.add_edge("generate_answer", END)
workflow.add_edge("rewrite_question", "generate_query_or_respond")

graph = workflow.compile()


def show_or_save_graph_image() -> None:
    png_bytes = graph.get_graph().draw_mermaid_png()

    output_path = Path(__file__).with_name("rag_graph.png")
    output_path.write_bytes(png_bytes)
    print(f"Graph image saved to: {output_path}")


show_or_save_graph_image()


def run_agentic_rag() -> None:
    stream = graph.stream(
        {
            "messages": [
                HumanMessage(
                    content="What does Lilian Weng say about types of reward hacking?"
                )
            ]
        },
        stream_mode="messages",
    )
    for message_chunk, _metadata in stream:
        text = getattr(message_chunk, "content", "")
        if isinstance(text, str) and text:
            print(text, end="", flush=True)
    print()


run_agentic_rag()
