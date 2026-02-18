import fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from .config import PDFConfig


def load_pdf(path: str):
    doc = fitz.open(path)
    return doc


def split_pdf(pdfs: list[Document]):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=PDFConfig.CHUNK_SIZE,
        chunk_overlap=PDFConfig.CHUNK_OVERLAP
    )
    return splitter.split_documents(pdfs)