import os
import io
import base64
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from PIL import Image
from langchain_core.documents import Document
from .pdf_handler import load_pdf, split_pdf
from .embedder import CLIPEmbedder, get_embedder

logger = logging.getLogger(__name__)


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
    text_docs: List = field(default_factory=list)  # Text documents only for BM25Retriever

    def __post_init__(self):
        """Initialize the CLIPEmbedder instance after dataclass initialization."""
        if self.embedder is None:
            self.embedder = get_embedder()

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

                    # Store text docs separately for BM25Retriever
                    self.text_docs.append(chunk)
            
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
                    logger.warning(f"Error processing image on page {i}, image {img_index}: {e}")
                    continue
        doc.close()
        return self.all_docs, self.all_embeddings, self.image_data_store, self.text_docs