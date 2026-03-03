"""
Disk persistence for FAISS vector indexes and image data store.

save_index() — called after every /ingest to snapshot state to disk.
load_index() — called at startup to restore state without re-uploading.

Layout on disk:
  data/<index_type>/text/index.faiss   — text FAISS binary index (384-dim)
  data/<index_type>/text/index.pkl     — text FAISS docstore
  data/<index_type>/image/index.faiss  — image FAISS binary index (512-dim, optional)
  data/<index_type>/image/index.pkl    — image FAISS docstore
  data/<index_type>/images.json        — base64 image data store

BM25 is NOT pickled separately; it is rebuilt from the text FAISS docstore at load time.
"""
import json
import logging
from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever

from .config import AppConfig, HybridSearchConfig
from .vectorstore import CLIPEmbeddingWrapper, SentenceTransformerEmbeddingWrapper

logger = logging.getLogger(__name__)


def _resolve_base(index_type: str, session_id: Optional[str] = None) -> Path:
    """Return the base directory for a given index type and optional session."""
    base = Path(AppConfig.DATA_DIR) / index_type
    if session_id:
        base = base / session_id
    return base


def save_index(
    text_faiss_store: Optional[FAISS],
    image_faiss_store: Optional[FAISS],
    image_data_store: dict,
    index_type: str,
    session_id: Optional[str] = None,
):
    """
    Persist text and image FAISS indexes plus the image data store to disk.

    Args:
        text_faiss_store:  sentence-transformers FAISS (384-dim); required.
        image_faiss_store: CLIP FAISS (512-dim); may be None (no images in doc).
        image_data_store:  base64 image dict.
        index_type:        'standard' or 'agentic'.
        session_id:        optional UUID; omit for flat legacy layout.
    """
    base = _resolve_base(index_type, session_id)
    base.mkdir(parents=True, exist_ok=True)

    if text_faiss_store is not None:
        text_folder = base / "text"
        text_folder.mkdir(exist_ok=True)
        text_faiss_store.save_local(str(text_folder))
        logger.info(f"Saved text FAISS index to {text_folder}")

    if image_faiss_store is not None:
        image_folder = base / "image"
        image_folder.mkdir(exist_ok=True)
        image_faiss_store.save_local(str(image_folder))
        logger.info(f"Saved image FAISS index to {image_folder}")

    (base / "images.json").write_text(json.dumps(image_data_store), encoding="utf-8")
    logger.info(f"Saved {index_type} index to {base}")


def load_index(index_type: str, session_id: Optional[str] = None) -> Optional[dict]:
    """
    Load previously saved FAISS indexes, image store, and rebuild BM25.

    Returns a dict with keys:
        text_faiss_store, image_faiss_store, bm25_retriever, image_data_store
    or None if no saved index exists.

    Args:
        index_type:  'standard' or 'agentic'.
        session_id:  optional UUID; omit for flat legacy layout.
    """
    base = _resolve_base(index_type, session_id)
    text_folder = base / "text"

    if not (text_folder / "index.faiss").exists():
        logger.info(f"No saved {index_type} index found at {text_folder}")
        return None

    try:
        text_faiss_store = FAISS.load_local(
            str(text_folder),
            SentenceTransformerEmbeddingWrapper(),
            allow_dangerous_deserialization=True,
        )

        # Rebuild BM25 from the persisted text docstore
        all_text_docs = list(text_faiss_store.docstore._dict.values())
        bm25_retriever = None
        if all_text_docs:
            bm25_retriever = BM25Retriever.from_documents(all_text_docs)
            bm25_retriever.k = HybridSearchConfig.K_BM25_CANDIDATES

        # Load image FAISS if it exists
        image_faiss_store = None
        image_folder = base / "image"
        if (image_folder / "index.faiss").exists():
            image_faiss_store = FAISS.load_local(
                str(image_folder),
                CLIPEmbeddingWrapper(),
                allow_dangerous_deserialization=True,
            )
            logger.info(f"Loaded image FAISS index from {image_folder}")

        images_file = base / "images.json"
        image_data_store = (
            json.loads(images_file.read_text(encoding="utf-8"))
            if images_file.exists()
            else {}
        )

        logger.info(
            f"Loaded {index_type} index from {base} "
            f"({len(all_text_docs)} text chunks, "
            f"{'with' if image_faiss_store else 'no'} image index)"
        )
        return {
            "text_faiss_store": text_faiss_store,
            "image_faiss_store": image_faiss_store,
            "bm25_retriever": bm25_retriever,
            "image_data_store": image_data_store,
        }

    except Exception as e:
        logger.error(f"Failed to load {index_type} index from {base}: {e}")
        return None
