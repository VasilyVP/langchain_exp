from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.tools import tool
from functools import lru_cache
from langgraph_agents.rag.seed import doc_splits


@lru_cache(maxsize=1)
def _get_retriever():
    vectorstore = InMemoryVectorStore.from_documents(
        documents=doc_splits,
        embedding=OpenAIEmbeddings(),
    )
    return vectorstore.as_retriever()


@tool
def retrieve_blog_posts(query: str) -> str:
    """Search and return information about Lilian Weng blog posts."""
    
    retriever = _get_retriever()
    retrieved_docs = retriever.invoke(query)
    
    return "\n\n".join([doc.page_content for doc in retrieved_docs])


retriever_tool = retrieve_blog_posts
