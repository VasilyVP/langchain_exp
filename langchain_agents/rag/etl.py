import os

from bs4.filter import SoupStrainer
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

VECTOR_SIZE = 384
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "rag_documents"
QUADRANT_URL = os.getenv("QUADRANT_URL", "localhost:6333")

try:
    client = QdrantClient(url=f"http://{QUADRANT_URL}")

    embedding_model = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embedding_model,
    )
except Exception as e:
    print(f"Error connecting to Qdrant: {e}")
    exit(1)

collection_exists = client.collection_exists(COLLECTION_NAME)
etl_needed = not collection_exists or client.count(COLLECTION_NAME).count == 0

if not etl_needed:
    print(
        f"Collection '{COLLECTION_NAME}' already exists and contains "
        f"{client.count(COLLECTION_NAME).count} documents. Skipping ETL."
    )
else:
    # Load the web page
    bs = SoupStrainer(class_=("post-title", "post-header", "post-content"))
    loader = WebBaseLoader(
        web_paths=("https://lilianweng.github.io/posts/2024-07-07-hallucination/",),
        bs_kwargs={"parse_only": bs},
    )
    docs = loader.load()

    assert len(docs) == 1

    print(f"Total characters: {len(docs[0].page_content)}")

    # Split the document into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )
    all_splits = text_splitter.split_documents(docs)

    print(f"Split blog post into {len(all_splits)} sub-documents.")

    if not collection_exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )

    document_ids = vector_store.add_documents(documents=all_splits)

    print(f"Added {len(document_ids)} documents to the vector store.")
