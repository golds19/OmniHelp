import os
import torch
import numpy as np
import io
import base64
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from .pdf_handler import load_pdf, split_pdf
from langchain_core.documents import Document


# Initializing the CLIP model for unified embeddings

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model.eval()

# define embedding functions for text and images

def embed_images(image_data):
    """Embed an image using the CLIP Model"""
    if isinstance(image_data, str):
        image = Image.open(image_data).convert("RGB")
    else: # if PIL image
        image = image_data

    inputs = clip_processor(images=image, return_tensors="pt")
    with torch.no_grad():
        features = clip_model.get_image_features(**inputs)
        # Normalize the features
        features = features / features.norm(dim=-1, keepdim=True)
        return features.squeeze().numpy()
    
def embed_text(text):
    """Embed text using CLIP"""
    inputs = clip_processor(
        text=text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=77 # CLIP's max token length
    )
    with torch.no_grad():
        features=clip_model.get_text_features(**inputs)
        # Normalize the features
        features = features / features.norm(dim=-1, keepdim=True)
        return features.squeeze().numpy()
    
class DataEmbedding:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.all_docs = []
        self.all_embeddings = []
        self.image_data_store = {}

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
                    embedding = embed_text(chunk.page_content)
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
                    embedding = embed_images(pil_image)
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
    path = "C:/Research Folder/AI Projects/Lifeforge/services/backend/app/rag/data/multimodal_sample.pdf"
    data_embedder = DataEmbedding(path)
    docs, embeddings = data_embedder.process_and_embedd_docs()
    
    print(f"{len(docs)} documents processed")
    print(f"{len(embeddings)} embeddings generated")