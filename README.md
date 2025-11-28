# Lifeforge 🚀

> An advanced Multimodal RAG (Retrieval-Augmented Generation) system with hybrid search capabilities and intelligent agentic workflows.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 20+](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

Lifeforge is a production-ready RAG system that combines the power of multimodal understanding, hybrid search strategies, and agentic reasoning to deliver accurate and contextual responses from your documents.

---

## ✨ Features

### 🎯 Core Capabilities

- **Multimodal RAG**: Process and understand both text and images from PDF documents
- **Hybrid Search**: Combines BM25 (keyword-based) and dense vector search for optimal retrieval
- **Query Enhancement**: Automatic query expansion and decomposition for better results
- **Agentic Workflows**: ReAct agents that can reason and plan document retrieval strategies
- **Streaming Responses**: Real-time token streaming for better UX
- **Configurable LLMs**: Easily switch between GPT-4, GPT-4o, Claude, or other models via configuration

### 🔧 Technical Features

- **FastAPI Backend**: High-performance async API
- **Next.js Frontend**: Modern React-based UI with App Router
- **Docker Support**: Production-ready containerization with development mode
- **CI/CD Pipeline**: Automated testing and deployment with GitHub Actions
- **Health Checks**: Built-in monitoring and health endpoints
- **Hot-reload**: Development mode with automatic code reloading

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│                    Port: 3000                                │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                           │
│                    Port: 8000                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              RAG Pipeline                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │  PDF     │  │ Embeddings│  │  Vector  │          │   │
│  │  │ Handler  │─▶│ Generator │─▶│  Store   │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  │                      │                               │   │
│  │                      ▼                               │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │       Hybrid Retriever                        │  │   │
│  │  │   ┌──────────┐      ┌──────────┐            │  │   │
│  │  │   │   BM25   │      │  Dense   │            │  │   │
│  │  │   │ (Keyword)│      │ (Vector) │            │  │   │
│  │  │   └─────┬────┘      └────┬─────┘            │  │   │
│  │  │         └────────┬────────┘                  │  │   │
│  │  │                  ▼                           │  │   │
│  │  │         Reciprocal Rank Fusion              │  │   │
│  │  └──────────────────┬───────────────────────────┘  │   │
│  │                      ▼                               │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │        Agentic RAG (ReAct)                   │  │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │   │
│  │  │  │  Query   │  │  Agent   │  │   LLM    │  │  │   │
│  │  │  │ Enhancer │─▶│ Executor │─▶│ Response │  │  │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Python** 3.11+ (for local development)
- **Node.js** 20+ (for frontend development)
- API keys for OpenAI, Google, or other LLM providers

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/lifeforge.git
cd lifeforge
```

### 2. Set Up Environment Variables

**Windows (PowerShell)**:
```powershell
Copy-Item .env.example .env
notepad .env
```

**Linux/Mac**:
```bash
cp .env.example .env
nano .env
```

**Required variables**:
```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# LLM Configuration
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.2
```

### 3. Start with Docker

**Windows (PowerShell)**:
```powershell
# Enable script execution (one-time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Build and start
.\docker.ps1 build
.\docker.ps1 dev
```

**Linux/Mac**:
```bash
make build
make dev
```

**Any OS (Direct Docker Compose)**:
```bash
docker-compose build
docker-compose -f docker-compose.dev.yml up
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 📖 Usage

### Upload and Query Documents

#### 1. Ingest a PDF Document

**Using cURL**:
```bash
curl -X POST "http://localhost:8000/ingest-agentic" \
  -F "file=@/path/to/your/document.pdf"
```

**Using Python**:
```python
import requests

url = "http://localhost:8000/ingest-agentic"
files = {"file": open("document.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

#### 2. Query the Document

**Using cURL**:
```bash
curl -X POST "http://localhost:8000/query-agentic" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main findings?"}'
```

**Using Python**:
```python
import requests

url = "http://localhost:8000/query-agentic"
data = {"question": "What are the main findings?"}
response = requests.post(url, json=data)
print(response.json())
```

#### 3. Streaming Responses

```bash
curl -X POST "http://localhost:8000/query-agentic-stream" \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize the document"}' \
  --no-buffer
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ping` | GET | Health check |
| `/ingest` | POST | Ingest document (basic RAG) |
| `/query` | POST | Query documents (basic RAG) |
| `/ingest-agentic` | POST | Ingest document (agentic RAG) |
| `/query-agentic` | POST | Query with agent (agentic RAG) |
| `/query-agentic-stream` | POST | Streaming agent responses |

---

## ⚙️ Configuration

### LLM Models

Configure your LLM models in `.env`:

```env
# Main LLM for RAG responses
LLM_MODEL=gpt-4o-mini              # Options: gpt-4, gpt-4o, gpt-4o-mini, claude-3-opus, etc.
LLM_TEMPERATURE=0.2

# Query enhancement LLM (can be different/cheaper)
QUERY_ENHANCER_MODEL=gpt-4o-mini
QUERY_ENHANCER_TEMPERATURE=0.7
```

### Hybrid Search Configuration

Configure search behavior in `.env`:

```env
# Enable/Disable hybrid search
HYBRID_SEARCH_ENABLED=true

# Fusion weights (should sum to ~1.0)
BM25_WEIGHT=0.4                    # Keyword search weight
DENSE_WEIGHT=0.6                   # Vector search weight

# Number of results
K_TOTAL=5                          # Final results to return
K_BM25_CANDIDATES=10               # BM25 candidates to fetch
K_DENSE_CANDIDATES=10              # Dense candidates to fetch

# BM25 Parameters
BM25_K1=1.5                        # Term frequency saturation
BM25_B=0.75                        # Length normalization

# Query Expansion
QUERY_EXPANSION_ENABLED=true
NUM_QUERY_VARIATIONS=3
```

### Advanced Configuration

See [.env.example](.env.example) for all available configuration options.

---

## 📦 Tech Stack

### Backend

| Technology | Purpose |
|-----------|---------|
| **FastAPI** | High-performance async web framework |
| **LangChain** | LLM orchestration and RAG pipelines |
| **LangGraph** | Agentic workflow management |
| **FAISS** | Dense vector similarity search |
| **Rank-BM25** | Keyword-based retrieval |
| **PyMuPDF** | PDF processing and image extraction |
| **Sentence Transformers** | Text embeddings |
| **NLTK** | Text tokenization and processing |
| **Pydantic** | Data validation |

### Frontend

| Technology | Purpose |
|-----------|---------|
| **Next.js 16** | React framework with App Router |
| **React 19** | UI library |
| **TailwindCSS 4** | Utility-first CSS framework |
| **TypeScript** | Type-safe development |

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **GitHub Actions** | CI/CD pipeline |

---

## 🛠️ Development

### Local Development (Without Docker)

#### Backend

```bash
cd services/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Run development server
uvicorn app.api.app:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd services/frontend/multirag

# Install dependencies
npm install

# Run development server
npm run dev
```

### Docker Development Mode

Features hot-reload for both backend and frontend.

**Windows**:
```powershell
.\docker.ps1 dev
.\docker.ps1 logs-be    # View backend logs
.\docker.ps1 shell-be   # Open backend shell
```

**Linux/Mac**:
```bash
make dev
make logs-be            # View backend logs
make shell-be           # Open backend shell
```

### Available Commands

See all available commands:

**Windows**: `.\docker.ps1 help`
**Linux/Mac**: `make help`

Common commands:
- `build` - Build all Docker images
- `dev` - Start development mode (hot-reload)
- `up` - Start production mode
- `down` - Stop all services
- `logs` - View all logs
- `logs-be` / `logs-fe` - View backend/frontend logs
- `shell-be` / `shell-fe` - Open shell in container
- `clean` - Remove all containers and images
- `health` - Check service health

---

## 🚢 Deployment

### Quick Deploy with Docker Compose

```bash
# On your server
git clone https://github.com/yourusername/lifeforge.git
cd lifeforge

# Set up environment
cp .env.example .env
nano .env  # Add your API keys

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

### CI/CD Pipeline

The project includes a complete CI/CD pipeline with GitHub Actions:

**Pipeline Stages**:
1. **Test Backend** - Python linting and tests
2. **Test Frontend** - ESLint and build verification
3. **Build & Push** - Docker images to GitHub Container Registry
4. **Deploy** - Optional auto-deployment

**Setup**:
1. Push to `main` or `develop` branch
2. Pipeline runs automatically
3. Docker images are built and pushed to `ghcr.io`

**Enable Auto-Deploy**:
1. Add secrets in GitHub: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`
2. Uncomment the `deploy` job in `.github/workflows/ci-cd.yml`

### Cloud Deployment

**AWS ECS**:
```bash
ecs-cli configure --cluster lifeforge --region us-east-1
ecs-cli compose -f docker-compose.yml up
```

**Google Cloud Run**:
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/backend
gcloud run deploy backend --image gcr.io/PROJECT_ID/backend
```

For detailed deployment instructions, see [DOCKER.md](./DOCKER.md).

---

## 📚 Documentation

- **[DOCKER.md](./DOCKER.md)**: Complete Docker and deployment guide with Windows-specific commands
- **[.env.example](./.env.example)**: Configuration reference with all options
- **[API Documentation](http://localhost:8000/docs)**: Interactive API docs (when running)

---

## 📊 Project Structure

```
Lifeforge/
├── services/
│   ├── backend/                     # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/                # API endpoints
│   │   │   │   └── app.py          # Main FastAPI app
│   │   │   └── rag/                # RAG implementation
│   │   │       ├── core/           # Core RAG components
│   │   │       │   ├── config.py            # Configuration
│   │   │       │   ├── data_ingestion.py    # PDF processing
│   │   │       │   ├── vectorstore.py       # Vector store setup
│   │   │       │   ├── retriever.py         # Retrieval logic
│   │   │       │   ├── hybrid_retriever.py  # Hybrid search
│   │   │       │   ├── rag_pipeline.py      # RAG pipeline
│   │   │       │   └── rag_manager.py       # System manager
│   │   │       └── agent/          # Agentic RAG
│   │   │           ├── query_enhancer.py    # Query enhancement
│   │   │           ├── react_node.py        # ReAct agent
│   │   │           ├── agent_tools.py       # Agent tools
│   │   │           ├── rag_state.py         # State management
│   │   │           └── graph_builder.py     # LangGraph builder
│   │   ├── Dockerfile              # Production image
│   │   ├── requirements.txt        # Python dependencies
│   │   └── .dockerignore
│   └── frontend/
│       └── multirag/               # Next.js frontend
│           ├── app/                # App Router
│           ├── public/             # Static assets
│           ├── Dockerfile          # Production image
│           ├── Dockerfile.dev      # Development image
│           ├── next.config.ts      # Next.js config
│           ├── package.json        # Node dependencies
│           └── .dockerignore
├── .github/
│   └── workflows/
│       └── ci-cd.yml              # GitHub Actions pipeline
├── docker-compose.yml             # Production config
├── docker-compose.dev.yml         # Development config
├── Makefile                       # Commands (Linux/Mac)
├── docker.ps1                     # Commands (Windows PowerShell)
├── docker.bat                     # Commands (Windows CMD)
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── DOCKER.md                      # Docker documentation
└── README.md                      # This file
```

---

## 🔧 How It Works

### 1. Document Ingestion

```python
# services/backend/app/rag/core/data_ingestion.py

1. PDF Upload → PyMuPDF extracts text and images
2. Text Chunking → Split into semantic chunks
3. Embedding Generation → Sentence Transformers creates vectors
4. Storage → FAISS (dense) + BM25 (keyword) indexing
```

### 2. Hybrid Retrieval

```python
# services/backend/app/rag/core/hybrid_retriever.py

1. Query Enhancement → Generate variations and expansions
2. Parallel Search:
   - BM25: Keyword matching with TF-IDF
   - FAISS: Dense vector similarity
3. Fusion → Reciprocal Rank Fusion (RRF) combines results
4. Re-ranking → Return top-k documents
```

### 3. Agentic RAG

```python
# services/backend/app/rag/agent/graph_builder.py

1. ReAct Agent receives query
2. Agent plans retrieval strategy
3. Tools execution:
   - retrieve_documents()
   - query_enhancement()
4. LLM generates response with citations
5. Streaming output to user
```

---

## 🧪 Testing

### Run Tests

**Backend**:
```bash
cd services/backend
pytest tests/ -v
pytest tests/ -v --cov=app --cov-report=html
```

**Frontend**:
```bash
cd services/frontend/multirag
npm test
npm test -- --watch
```

---

## 🐛 Troubleshooting

### Common Issues

**Port already in use**:
```powershell
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Container keeps restarting**:
```bash
# Check logs
.\docker.ps1 logs-be    # Windows
make logs-be            # Linux/Mac

# Debug with shell
.\docker.ps1 shell-be   # Windows
make shell-be           # Linux/Mac
```

**Hot-reload not working (Windows)**:
Add to `docker-compose.dev.yml`:
```yaml
environment:
  - WATCHPACK_POLLING=true
```

For more troubleshooting, see [DOCKER.md](./DOCKER.md#troubleshooting).

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Style

- **Backend**: Follow PEP 8, use `black` for formatting
- **Frontend**: Use ESLint and Prettier
- **Commits**: Use conventional commit format

---

## 📈 Roadmap

- [x] Multimodal RAG with text and images
- [x] Hybrid search (BM25 + Dense vectors)
- [x] Query enhancement and expansion
- [x] Agentic RAG with ReAct agents
- [x] Docker and CI/CD setup
- [ ] Vector database options (Pinecone, Weaviate)
- [ ] Multi-document conversation history
- [ ] Custom embedding models
- [ ] Advanced re-ranking strategies
- [ ] Voice input/output integration

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Acknowledgments

- **LangChain** - LLM orchestration framework
- **FastAPI** - High-performance web framework
- **Next.js** - React framework
- **FAISS** - Efficient vector similarity search
- Open-source community for tools and inspiration

---

## 📬 Support

- **Documentation**: [DOCKER.md](./DOCKER.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/lifeforge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/lifeforge/discussions)

---

<div align="center">

**Built with ❤️ using FastAPI, LangChain, and Next.js**

⭐ Star this repo if you find it useful!

</div>
