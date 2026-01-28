from typing import List, Optional
import os
import qdrant_client

# LlamaIndex settings and imports
from llama_index.core import Settings, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# --------------------
# RAG (Qdrant + LlamaIndex) config
# --------------------
RAG_ENABLED = os.getenv("RAG_ENABLED", "1") == "1"
RAG_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
RAG_COLLECTION = os.getenv("RAG_COLLECTION", "durusai_docs")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "15"))
RAG_MAX_CHARS = int(os.getenv("RAG_MAX_CHARS", "3500"))

# Lazy-initialized RAG objects
_rag_index: Optional[VectorStoreIndex] = None
_rag_init_error: Optional[str] = None

# Path to HMI layout/reference doc (used for keyword fallback)
# Default relative to project root, not this file's folder.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
HMI_DOC_PATH = os.getenv(
    "HMI_DOC_PATH",
    os.path.join(_PROJECT_ROOT, "ai_reference", "hmi_config_layout_description.txt"),
)


def _init_rag_index() -> Optional[VectorStoreIndex]:
    """Initialize a VectorStoreIndex view over an existing Qdrant collection.

    This does NOT build the index; it just connects to the already-built collection.
    """
    global _rag_index, _rag_init_error

    if _rag_index is not None:
        return _rag_index
    if _rag_init_error is not None:
        return None

    if not RAG_ENABLED:
        _rag_init_error = "RAG disabled via RAG_ENABLED=0"
        return None

    try:
        # Ensure we use local embeddings (no OpenAI dependency)
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

        client = qdrant_client.QdrantClient(url=RAG_QDRANT_URL)
        vector_store = QdrantVectorStore(client=client, collection_name=RAG_COLLECTION)

        # Re-hydrate an index view over the existing vector store
        _rag_index = VectorStoreIndex.from_vector_store(vector_store)
        return _rag_index
    except Exception as e:
        _rag_init_error = str(e)
        return None


def _format_rag_context(nodes) -> str:
    """Turn retrieved nodes into a compact, source-attributed context block."""
    parts: List[str] = []
    total = 0

    for i, n in enumerate(nodes, 1):
        try:
            score = getattr(n, "score", None)
            node = getattr(n, "node", None)
            meta = (getattr(node, "metadata", None) or {}) if node is not None else {}
            path = meta.get("path") or meta.get("file_path") or meta.get("filename") or "unknown"
            text = node.get_content() if node is not None else ""
        except Exception:
            continue

        header = f"[Source {i}] score={score:.3f} path={path}" if score is not None else f"[Source {i}] path={path}"
        block = header + "\n" + text.strip() + "\n"

        if total + len(block) > RAG_MAX_CHARS:
            remaining = max(0, RAG_MAX_CHARS - total)
            if remaining > 0:
                parts.append(block[:remaining])
            break

        parts.append(block)
        total += len(block)

    return "\n---\n".join(parts).strip()


def get_rag_context(query: str) -> str:
    """Retrieve relevant chunks for a query from Qdrant and return a compact context string."""
    index = _init_rag_index()
    if index is None:
        return ""

    try:
        retriever = index.as_retriever(similarity_top_k=RAG_TOP_K)
        nodes = retriever.retrieve(query)
        return _format_rag_context(nodes)
    except Exception:
        # Don't fail the request if RAG fails; just return empty context.
        return ""


def _get_keyword_fallback_context(query: str) -> str:
    """If the prompt contains key HMI terms (label/button/view), inject
    the corresponding sections from the local HMI layout doc as a fallback.

    This ensures core component schemas are present even if vector retrieval
    misses or scores borderline.
    """
    try:
        q = (query or "").lower()
        want_label = "label" in q
        want_button = "button" in q
        want_view = "view" in q

        if not (want_label or want_button or want_view):
            return ""

        if not os.path.exists(HMI_DOC_PATH):
            return ""

        with open(HMI_DOC_PATH, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        # Heuristic section extraction: find headings and slice until next heading
        import re
        # Collect all potential headings to determine boundaries
        heading_pattern = re.compile(r"^\s*(?:[A-Z][A-Za-z\s]+(?:Component|Schema))\b.*$", re.MULTILINE)
        headings = list(heading_pattern.finditer(text))

        def extract_section(title_keywords: List[str]) -> Optional[str]:
            if not title_keywords:
                return None
            # Find start by matching any keyword set in a heading line
            for i, m in enumerate(headings):
                line = m.group(0).lower()
                if all(k in line for k in title_keywords):
                    start = m.start()
                    # Next heading boundary or end of file
                    end = headings[i + 1].start() if (i + 1) < len(headings) else len(text)
                    section = text[start:end].strip()
                    # Bound section length to avoid overly long context
                    return section[:1000]
            return None

        parts: List[str] = []
        if want_view:
            s = extract_section(["view", "schema"]) or extract_section(["view"])
            if s:
                parts.append("[Fallback] View Schema\n" + s)
        if want_label:
            s = extract_section(["label", "component"]) or extract_section(["label"])
            if s:
                parts.append("[Fallback] Label Component\n" + s)
        if want_button:
            s = extract_section(["button", "component"]) or extract_section(["button"])
            if s:
                parts.append("[Fallback] Button Component\n" + s)

        if not parts:
            return ""

        header = f"[Source fallback] path={HMI_DOC_PATH}"
        return header + "\n" + ("\n---\n".join(parts))
    except Exception:
        return ""
