from langchain.messages import HumanMessage
from langgraph.graph import MessagesState

from langgraph_agents.rag.model import chat_model

REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question:"
)


def rewrite_question(state: MessagesState):
    """Rewrite the original user question."""
    question = state["messages"][0].content
    prompt = REWRITE_PROMPT.format(question=question)
    response = chat_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [HumanMessage(content=response.content)]}
