"""
Disk persistence for FAISS vector index and image data store.

save_index() — called after every /ingest to snapshot state to disk
load_index() — called at startup to restore state without re-uploading

BM25 is NOT pickled separately; it is rebuilt from the FAISS docstore
(which LangChain persists as a pickle alongside the FAISS binary index).
"""
import json
import logging
from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever

from .config import AppConfig, HybridSearchConfig
from .vectorstore import CLIPEmbeddingWrapper

logger = logging.getLogger(__name__)


def _index_folder(index_type: str) -> Path:
    """Return the directory used for a given index type ('standard' or 'agentic')."""
    return Path(AppConfig.DATA_DIR) / index_type


def save_index(faiss_store: FAISS, image_data_store: dict, index_type: str):
    """
    Persist the FAISS vector index and image data store to disk.

    Writes:
      data/<index_type>/index.faiss  — binary FAISS index
      data/<index_type>/index.pkl    — LangChain docstore (Document objects)
      data/<index_type>/images.json  — base64 image data store

    Ingesting a new PDF overwrites the previous files.
    """
    folder = _index_folder(index_type)
    folder.mkdir(parents=True, exist_ok=True)

    faiss_store.save_local(str(folder))
    (folder / "images.json").write_text(
        json.dumps(image_data_store), encoding="utf-8"
    )
    logger.info(f"Saved {index_type} index to {folder}")


def load_index(index_type: str) -> Optional[dict]:
    """
    Load a previously saved FAISS index, image store, and rebuild BM25.

    Returns a dict with keys:
        faiss_store, bm25_retriever, image_data_store
    or None if no saved index exists.
    """
    folder = _index_folder(index_type)
    if not (folder / "index.faiss").exists():
        logger.info(f"No saved {index_type} index found at {folder}")
        return None

    try:
        faiss_store = FAISS.load_local(
            str(folder),
            CLIPEmbeddingWrapper(),
            allow_dangerous_deserialization=True,
        )

        images_file = folder / "images.json"
        image_data_store = (
            json.loads(images_file.read_text(encoding="utf-8"))
            if images_file.exists()
            else {}
        )

        # Rebuild BM25 from the persisted docstore — no separate pickle needed
        all_docs = list(faiss_store.docstore._dict.values())
        text_docs = [d for d in all_docs if d.metadata.get("type") == "text"]
        bm25_retriever = None
        if text_docs:
            bm25_retriever = BM25Retriever.from_documents(text_docs)
            bm25_retriever.k = HybridSearchConfig.K_BM25_CANDIDATES

        logger.info(
            f"Loaded {index_type} index from {folder} "
            f"({len(all_docs)} docs, {len(text_docs)} text chunks)"
        )
        return {
            "faiss_store": faiss_store,
            "bm25_retriever": bm25_retriever,
            "image_data_store": image_data_store,
        }

    except Exception as e:
        logger.error(f"Failed to load {index_type} index from {folder}: {e}")
        return None
