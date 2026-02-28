"""
Singleton embedder module to prevent multiple CLIP model instantiations.

This module provides a cached singleton instance of CLIPEmbedder to avoid
loading the ~600MB model multiple times, significantly reducing memory usage
and improving latency.
"""
import logging
from functools import lru_cache
from dataclasses import dataclass, field
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class CLIPEmbedder:
    """
    Encapsulates CLIP model and provides embedding functionality for text and images.
    """
    model_name: str = "openai/clip-vit-base-patch32"
    model: CLIPModel = field(init=False)
    processor: CLIPProcessor = field(init=False)

    def __post_init__(self):
        """Initialize the CLIP model and processor after dataclass initialization."""
        logger.info(f"Loading CLIP model: {self.model_name}")
        self.model = CLIPModel.from_pretrained(self.model_name)
        self.processor = CLIPProcessor.from_pretrained(self.model_name)
        self.model.eval()
        logger.info("CLIP model loaded successfully")

    def embed_image(self, image_data):
        """
        Embed an image using the CLIP Model.

        Args:
            image_data: Either a file path string or a PIL Image object

        Returns:
            numpy.ndarray: Normalized image embedding vector
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

    def embed_text(self, text: str):
        """
        Embed text using CLIP.

        Args:
            text: The text string to embed

        Returns:
            numpy.ndarray: Normalized text embedding vector
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


@lru_cache(maxsize=1)
def get_embedder() -> CLIPEmbedder:
    """
    Get the singleton CLIPEmbedder instance.

    Uses lru_cache to ensure the model is only loaded once,
    saving ~600MB memory per avoided instantiation.

    Returns:
        CLIPEmbedder: The singleton embedder instance
    """
    return CLIPEmbedder()
