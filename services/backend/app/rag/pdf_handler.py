import os
import fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def load_pdf(path: str):
    doc = fitz.open(path)
    return doc

def split_pdf(pdfs: list[Document]):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    return splitter.split_documents(pdfs)