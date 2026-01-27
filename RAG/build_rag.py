import os
from pathlib import Path

# ✅ Set embed model FIRST (before importing VectorStoreIndex, readers, etc.)
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.chunk_size = 800
Settings.chunk_overlap = 120

# --- Runtime configuration (env + sensible defaults) ---
# Required paths and hosts were previously undefined causing runtime errors.
# These defaults make local runs smooth while allowing overrides via env.
DATA_DIR = Path(os.environ.get("RAG_DATA_DIR", "../ai_reference"))
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
# Unify collection env var with server: prefer RAG_COLLECTION, fallback to QDRANT_COLLECTION
COLLECTION = os.getenv("RAG_COLLECTION") or os.getenv("QDRANT_COLLECTION", "durusai_docs")

# ✅ Now import the rest
import qdrant_client
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import Document
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.readers.json import JSONReader
# IMPORTANT:
# Set your embed model + LLM in env or code.
# If you're using OpenAI via LlamaIndex, export OPENAI_API_KEY.
# Otherwise configure a local embedding model in Settings before indexing.

def load_text_docs(data_dir: Path):
    # SimpleDirectoryReader supports .md and many common types.  [oai_citation:2‡LlamaIndex](https://developers.llamaindex.ai/python/framework/module_guides/loading/simpledirectoryreader/?utm_source=chatgpt.com)
    return SimpleDirectoryReader(
        input_dir=str(data_dir),
        recursive=True,
        required_exts=[".txt"],
        filename_as_id=True,
    ).load_data()

def load_json_docs(data_dir: Path):
    # LlamaIndex recommends a JSON-specific loader for JSON.  [oai_citation:3‡LlamaIndex](https://developers.llamaindex.ai/python/framework/module_guides/loading/simpledirectoryreader/?utm_source=chatgpt.com)
    reader = JSONReader(levels_back=2, collapse_length=200)
    docs: list[Document] = []

    for p in data_dir.rglob("*.json"):
        # Skip obvious noise/secrets if needed
        if p.name.lower() in {"package-lock.json", "tsconfig.json"}:
            continue

        json_docs = reader.load_data(input_file=str(p))
        for d in json_docs:
            # Helpful metadata for filtering later
            d.metadata = {
                **(d.metadata or {}),
                "path": str(p),
                "doc_type": "hmi_config",
                "ext": ".json",
            }
        docs.extend(json_docs)

    return docs

def main():
    if not DATA_DIR.exists():
        raise SystemExit(f"RAG_DATA_DIR not found: {DATA_DIR.resolve()}")

    print(f"Loading docs from: {DATA_DIR.resolve()}")

    text_docs = load_text_docs(DATA_DIR)
    json_docs = load_json_docs(DATA_DIR)

    # Tag text docs too and ensure path metadata is present for attribution
    for d in text_docs:
        existing_meta = d.metadata or {}
        # SimpleDirectoryReader typically provides file_path; keep it if present
        path = existing_meta.get("file_path") or existing_meta.get("filename") or existing_meta.get("id") or None
        d.metadata = {
            **existing_meta,
            "doc_type": "docs",
            "ext": ".txt",
            # normalized path key used by server for source formatting
            **({"path": path} if path else {}),
        }

    docs = text_docs + json_docs
    print(f"Loaded {len(docs)} documents")

    # Qdrant client + vector store
    client = qdrant_client.QdrantClient(url=QDRANT_URL)
    # Validate connectivity early with a lightweight call
    try:
        client.get_collections()
    except Exception as e:
        raise SystemExit(f"Unable to connect to Qdrant at {QDRANT_URL}: {e}")
    vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Build / upsert into Qdrant
    VectorStoreIndex.from_documents(docs, storage_context=storage_context)

    print(f"✅ Indexed into Qdrant collection: {COLLECTION} at {QDRANT_URL}")

if __name__ == "__main__":
    main()