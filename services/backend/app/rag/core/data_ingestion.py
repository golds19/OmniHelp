import os
import torch
import numpy as np
import io
import base64
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from .pdf_handler import load_pdf, split_pdf
from langchain_core.documents import Document


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
        self.model = CLIPModel.from_pretrained(self.model_name)
        self.processor = CLIPProcessor.from_pretrained(self.model_name)
        self.model.eval()

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
            features = self.model.get_image_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)
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
            features = self.model.get_text_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)
            return features.squeeze().numpy()


@dataclass
class DataEmbedding:
    """
    Handles PDF processing and embedding generation for text and images.
    """
    pdf_path: str
    embedder: Optional[CLIPEmbedder] = None
    all_docs: List = field(default_factory=list)
    all_embeddings: List = field(default_factory=list)
    image_data_store: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Initialize the CLIPEmbedder instance after dataclass initialization."""
        if self.embedder is None:
            self.embedder = CLIPEmbedder()

    def process_pdf(self):
        doc = load_pdf(self.pdf_path)
        return doc
    
    def process_and_embedd_docs(self):
        # loading the doc
        doc = self.process_pdf()

        for i, page in enumerate(doc):
            # Process text
            text = page.get_text()
            if text.strip():
                # create temporary document for splitting
                temp_doc = Document(page_content=text, metadata={"page": i, "type": "text"})
                text_chunks = split_pdf([temp_doc])

                # Embed each chunk using CLIP
                for chunk in text_chunks:
                    embedding = self.embedder.embed_text(chunk.page_content)
                    self.all_embeddings.append(embedding)
                    self.all_docs.append(chunk)
            
            # Process images
            # Convert PDF images to PIL format
            # Store as Base64
            # create CLIP embeddings for retrieval

            for img_index, img in enumerate(page.get_images(full=True)):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    # convert to PIL image
                    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

                    # create unique identifier
                    image_id = f"page_{i}_img_{img_index}"

                    # store image as base64 for later use with LLM model
                    buffered = io.BytesIO()
                    pil_image.save(buffered, format="PNG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    self.image_data_store[image_id] = img_base64
                    
                    # Embed document using CLIP
                    embedding = self.embedder.embed_image(pil_image)
                    self.all_embeddings.append(embedding)

                    # create document for image
                    img_doc = Document(page_content=f"[Image: {image_id}]", metadata={"page": i, "type": "image", "image_id": image_id})
                    self.all_docs.append(img_doc)
                except Exception as e:
                    print(f"Error processing image on page {i}, image {img_index}: {e}")
                    continue
        doc.close()
        return self.all_docs, self.all_embeddings, self.image_data_store


if __name__ == "__main__":
    print("testing")