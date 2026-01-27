import os
import qdrant_client

# ✅ Set LlamaIndex Settings first
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.mlx import MLXLLM

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.llm = MLXLLM(model_name="mlx-community/Meta-Llama-3.1-8B-Instruct-4bit")

# ✅ Now import the rest
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "hmi_rag_bge_small_v1")

def main():
    client = qdrant_client.QdrantClient(url=QDRANT_URL)
    vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION)

    # Re-hydrate an index view over the existing vector store
    index = VectorStoreIndex.from_vector_store(vector_store)

    query_engine = index.as_query_engine(similarity_top_k=6)

    while True:
        q = input("\nAsk> ").strip()
        if not q or q.lower() in {"exit", "quit"}:
            break
        resp = query_engine.query(q)
        print("\n--- Answer ---\n", resp)

if __name__ == "__main__":
    main()