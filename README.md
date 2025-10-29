# OmniHelp

A multimodal RAG-powered support assistant with voice interaction capabilities.

## Overview

OmniHelp is an intelligent customer support tool that combines document retrieval, image understanding, and voice interaction to provide accurate, cited answers from your knowledge base.

## Features

- 🤖 **Multimodal RAG**: Query across documents, support tickets, and screenshots
- 🎤 **Voice I/O**: Speak your questions and hear responses
- 📚 **Smart Retrieval**: Vector-based search with clear source citations
- 💬 **Web Interface**: Simple chat UI with voice recording
- 🐳 **Easy Deploy**: Single Docker container setup

## Tech Stack

- **Backend**: Python (FastAPI)
- **Frontend**: Next.js + TypeScript
- **Vector DB**: [Your choice - Pinecone/Weaviate/ChromaDB]
- **LLM**: [Your model - GPT-4/Claude/etc.]
- **Voice**: Speech-to-text & text-to-speech APIs

## Current Status

**Phase 1 - Working MVP** ✅
- Text and voice chat functionality
- Document ingestion pipeline
- Vector search with citations
- Basic web UI

## Usage

1. **Upload Documents**: Ingest PDFs, images, or text files
2. **Ask Questions**: Type or speak your query
3. **Get Answers**: Receive cited responses with sources
4. **Voice Mode**: Toggle mic for hands-free interaction

## License

MIT