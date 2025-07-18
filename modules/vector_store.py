# --- vector_store.py ---
import os
import hashlib
from pinecone import Pinecone
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("docsage-index")

# Initialize OpenAI embedder
embedder = OpenAIEmbeddings()

def store_chunks_to_pinecone(chunks, filename, namespace="default"):
    """
    Store document chunks to Pinecone with filename as metadata and use custom namespace
    """
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedder.embed_documents(texts)

    vectors = [
        {
            "id": f"{i}-{hashlib.md5(chunk['text'].encode()).hexdigest()}",
            "values": embedding,
            "metadata": {
                "text": chunk["text"],
                "filename": chunk["filename"]
            }
        }
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    index.upsert(vectors=vectors, namespace=namespace)
