from pathlib import Path
import asyncio
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

VECTOR_SIZE = 384
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "documents"

DIR = Path(__file__).parent

# Load the PDF document
file_path = DIR / "data_sources" / "money-creation-in-the-modern-economy.pdf"
loader = PyPDFLoader(file_path)

docs = loader.load()

print("Docs len: ", len(docs))

# Split the document into smaller chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, add_start_index=True
)

all_splits = text_splitter.split_documents(docs)
print("All splits len: ", len(all_splits))

embedding_model = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)

# Initialize Qdrant client and create collection if it doesn't exist
client = QdrantClient(":memory:")

if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

vector_store = QdrantVectorStore(
    client=client,
    collection_name=COLLECTION_NAME,
    embedding=embedding_model,
)

# Add documents to the vector store
ids = vector_store.add_documents(documents=all_splits)

print("Ids: ", len(ids))


async def main():
    # Example query
    query = "What is the part of money are bank deposits?"
    results = await vector_store.asimilarity_search_with_score(query, k=1)

    doc, score = results[0]

    print("Results: ", doc.page_content)
    print("Score: ", score)


if __name__ == "__main__":
    asyncio.run(main())
