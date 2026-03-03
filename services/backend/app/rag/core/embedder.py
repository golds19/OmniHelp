"""
Singleton embedder module providing two model-backed embedding singletons:

- CLIPEmbedder  (get_embedder):      image embedding + CLIP text-for-image queries (512-dim)
- TextEmbedder  (get_text_embedder): text chunk + text query embedding (384-dim)

CLIP's text encoder has a hard 77-token limit that silently truncates chunks
beyond ~300 characters. TextEmbedder uses BAAI/bge-small-en-v1.5 (512-token
limit, 384-dim) which handles full document chunks without truncation and
produces substantially better semantic similarity for text-to-text tasks.
CLIP is kept only for image embedding and cross-modal image-retrieval queries
(text → image FAISS index).
"""
import logging
from functools import lru_cache
from dataclasses import dataclass, field
import numpy as np
import torch
import transformers
from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class CLIPEmbedder:
    """
    Encapsulates CLIP model for IMAGE embedding and cross-modal image queries.

    Do NOT use embed_text for indexing text chunks — the 77-token limit silently
    truncates longer passages. Use TextEmbedder for text chunks instead.
    embed_text is retained here solely to embed short query strings against
    the image FAISS index (enabling text → image retrieval).
    """
    model_name: str = "openai/clip-vit-base-patch32"
    model: CLIPModel = field(init=False)
    processor: CLIPProcessor = field(init=False)

    def __post_init__(self):
        """Initialize the CLIP model and processor after dataclass initialization."""
        logger.info(f"Loading CLIP model: {self.model_name}")
        # Suppress the benign "UNEXPECTED position_ids" load report emitted by
        # newer transformers when the checkpoint pre-dates dynamic position buffers.
        prev_verbosity = transformers.logging.get_verbosity()
        transformers.logging.set_verbosity_error()
        self.model = CLIPModel.from_pretrained(self.model_name)
        self.processor = CLIPProcessor.from_pretrained(self.model_name)
        transformers.logging.set_verbosity(prev_verbosity)
        self.model.eval()
        logger.info("CLIP model loaded successfully")

    def embed_image(self, image_data) -> np.ndarray:
        """
        Embed an image using the CLIP Model.

        Args:
            image_data: Either a file path string or a PIL Image object

        Returns:
            numpy.ndarray: Normalized 512-dim image embedding vector
        """
        if isinstance(image_data, str):
            image = Image.open(image_data).convert("RGB")
        else:
            image = image_data

        inputs = self.processor(images=image, return_tensors="pt")
        with torch.no_grad():
            output = self.model.get_image_features(**inputs)
            logger.debug(f"get_image_features returned type: {type(output).__name__}")
            if isinstance(output, torch.Tensor):
                features = output
            elif hasattr(output, 'image_embeds'):
                features = output.image_embeds
            elif hasattr(output, 'pooler_output'):
                features = output.pooler_output
            else:
                features = output[0]
            features = torch.nn.functional.normalize(features, dim=-1)
            return features.squeeze().numpy()

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a short text string using CLIP for querying the image FAISS index.

        CLIP text and image embeddings share the same 512-dim space, enabling
        cross-modal retrieval (find images via text queries). Retained for use
        by CLIPEmbeddingWrapper on the image index only.

        WARNING: truncates to 77 tokens. Do not use for document text chunks.
        """
        inputs = self.processor(
            text=text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=77
        )
        with torch.no_grad():
            output = self.model.get_text_features(**inputs)
            logger.debug(f"get_text_features returned type: {type(output).__name__}")
            if isinstance(output, torch.Tensor):
                features = output
            elif hasattr(output, 'text_embeds'):
                features = output.text_embeds
            elif hasattr(output, 'pooler_output'):
                features = output.pooler_output
            else:
                features = output[0]
            features = torch.nn.functional.normalize(features, dim=-1)
            return features.squeeze().numpy()


class TextEmbedder:
    """
    Text embedding using BAAI/bge-small-en-v1.5 (384-dim, 512-token limit).

    Used for:
    - Embedding text chunks at ingestion time (no 77-token truncation)
    - Embedding text queries against the text FAISS index
    - Computing answer-source similarity in hallucination detection
    """
    MODEL_NAME = "BAAI/bge-small-en-v1.5"

    def __init__(self):
        logger.info(f"Loading text embedding model: {self.MODEL_NAME}")
        self.model = SentenceTransformer(self.MODEL_NAME)
        logger.info("Text embedding model loaded successfully")

    def encode(self, text: str, normalize_embeddings: bool = True) -> np.ndarray:
        """Embed a single text string. Returns a normalized 384-dim numpy array."""
        return self.model.encode(text, normalize_embeddings=normalize_embeddings)

    def encode_batch(self, texts: list, normalize_embeddings: bool = True) -> np.ndarray:
        """Embed a list of texts. Returns a 2-D (N, 384) numpy array."""
        return self.model.encode(texts, normalize_embeddings=normalize_embeddings)


@lru_cache(maxsize=1)
def get_embedder() -> CLIPEmbedder:
    """
    Get the singleton CLIPEmbedder instance (image embedding + image-index queries).

    Uses lru_cache to ensure the ~600MB model is only loaded once.
    """
    return CLIPEmbedder()


@lru_cache(maxsize=1)
def get_text_embedder() -> TextEmbedder:
    """
    Get the singleton TextEmbedder instance (text chunk embedding + text-index queries).

    Uses lru_cache to ensure the model is only loaded once.
    """
    return TextEmbedder()
