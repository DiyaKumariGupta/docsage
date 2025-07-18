import os
from pinecone import Pinecone, ServerlessSpec

# Optional: load from .env if not using actual key directly
api_key = os.environ.get("PINECONE_API_KEY", "your-actual-api-key-here")

pc = Pinecone(api_key=api_key)

index_name = "docsage-index"  # Name your index

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # ✅ Must match OpenAI embedding
        metric="cosine",  # cosine similarity is common for semantic search
        spec=ServerlessSpec(
            cloud="aws",  # or "gcp"
            region="us-east-1"  # or your Pinecone project region
        )
    )
    print(f"✅ Created index '{index_name}' with 1536 dimensions.")
else:
    print(f"ℹ️ Index '{index_name}' already exists.")
