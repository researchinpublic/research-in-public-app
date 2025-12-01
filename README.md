# Research In Public: Agentic Support Ecosystem

**Capstone Project for:** [Kaggle's 5-Day AI Agents Intensive Course with Google](https://www.kaggle.com/learn-guide/5-day-agents)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5-green.svg)](https://ai.google.dev/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![Status](https://img.shields.io/badge/Status-Production-success.svg)](https://github.com/yaodu/research-in-public)

---

## Problem Statement

PhD students and early-career researchers face a critical gap in existing academic tools. While there are countless applications for managing manuscripts, datasets, and citations, there is a vacuum in tooling for the *human experience* of research—the emotional struggles, mental blocks, and iterative failures that define the research journey.

**Key Challenges:**
- **Emotional Isolation**: Researchers experience high rates of imposter syndrome, burnout, and anxiety with no specialized support
- **Invisible Struggles**: Academic struggles are often invisible, making it difficult to find peers with similar experiences across scientific disciplines
- **IP-Sharing Fear**: Researchers want to build a public brand on LinkedIn/X but fear accidentally sharing IP-sensitive information (PI names, reagent identifiers, unpublished data)
- **Fragmented Support**: No single system provides emotional validation, peer connection, content transformation, and IP safety in one integrated experience

**Research In Public** addresses this gap by transforming research struggles from private burdens into dual-value assets: immediate emotional support internally, and IP-safe public narratives externally.

---

## Why Agents?

A single AI agent cannot effectively handle the diverse needs of researchers. Each support function requires different personalities, expertise, and response styles:

- **Emotional support** needs warmth and validation (Mr. Rogers)
- **Grant critique** needs critical honesty (Carl Sagan)
- **Content transformation** needs poetic inspiration (Maya Angelou)
- **IP safety** needs careful scanning (no personality, just protection)
- **Peer matching** needs semantic understanding across disciplines

Our multi-agent architecture ensures each interaction feels authentic and purpose-built, rather than generic. Specialized agents with distinct personalities provide targeted support that a monolithic agent cannot deliver.

---

## Architecture

### System Overview

```
Frontend (Next.js) → Backend API (FastAPI) → Agent Orchestrator → Specialized Agents
                                                      ↓
                                    Intent Classifier → Vector Store (FAISS)
                                                      ↓
                                    Gemini Service → Embedding Service
```

### Multi-Agent System

The system consists of **five specialized agents** orchestrated through a centralized hub:

| Agent | Role | Personality | Technology |
|-------|------|-------------|------------|
| **Vent Validator** | Emotional support & active listening | Mr. Rogers | Gemini 2.5 Flash |
| **Semantic Matchmaker** | Peer connection engine | Oprah Winfrey | Vector embeddings + FAISS |
| **The Scribe** | Content drafting & brand building | Maya Angelou | Gemini 2.5 Pro |
| **The Guardian** | IP safety & compliance | Background agent | Gemini-based classification |
| **PI Simulator** | Grant critique & mentorship | Carl Sagan | Gemini 2.5 Pro |

### Key Components

**Agent Orchestrator** (`orchestration/agent_orchestrator.py`)
- Central coordinator that routes messages to appropriate agents
- Manages multi-agent workflows (e.g., emotional struggles trigger both Vent Validator and Matchmaker)
- Handles session management and conversation history

**Intent Classifier** (`orchestration/intent_classifier.py`)
- Analyzes user messages to determine intent (emotional, technical, shareable, grant)
- Routes to appropriate agent based on intent
- Uses keyword matching and Gemini-based classification

**Vector Search** (`services/vector_search_local.py`)
- FAISS-based similarity search for peer matching
- Uses `text-embedding-004` embeddings (768-dimensional vectors)
- Enables cross-disciplinary peer connections based on emotional/technical struggles

**Gemini Service** (`services/gemini_service.py`)
- Wrapper around Google Gemini API
- Supports both Flash (real-time) and Pro (deep understanding) models
- Handles structured output, chat completion, and text generation

**Embedding Service** (`services/embedding_service.py`)
- Generates vector embeddings using Google's `text-embedding-004`
- Calculates cosine similarity for peer matching
- Supports batch embedding generation

### Data Flow Example

1. User sends message: "I'm frustrated with my experiments failing"
2. Intent Classifier analyzes → Detects "emotional" intent
3. Orchestrator routes to Vent Validator agent
4. Vent Validator processes with Gemini 2.5 Flash → Returns empathetic response + emotional analysis metadata
5. Orchestrator detects emotional struggle → Triggers Matchmaker agent
6. Matchmaker generates embedding, searches FAISS index for similar struggles
7. Returns top 3 peer matches with similarity scores
8. Backend streams responses via Server-Sent Events (SSE)
9. Frontend displays streaming text and peer match cards

---

## Key Features

### 1. Emotional-Semantic Matching
Uses vector embeddings to connect researchers by *struggle* (e.g., "Dealing with a toxic PI" + "Western Blot failures"), not just by topic. This enables cross-disciplinary peer connections based on emotional and technical similarity.

### 2. Privacy-to-Public Pipeline
Transforms raw, emotional venting into professional, IP-safe LinkedIn posts:
- **The Guardian** scans for IP risks (PI names, reagent identifiers, unpublished data)
- **The Scribe** completely rewrites content, transforming complaints into insights
- Output: Professional post with hashtags, all sensitive information removed

### 3. Intelligent Agent Routing
Auto Mode automatically routes users to the right agent based on intent detection, eliminating the need to manually select which agent to use.

### 4. Real-Time Streaming
Server-Sent Events (SSE) provide real-time streaming responses, creating a natural conversation experience similar to ChatGPT.

### 5. Struggle Map Visualization
Visual representation of peer struggles in high-dimensional vector space, showing users their position among peers with similar challenges.

---

## Technologies Used

### AI/ML Stack
- **Google Gemini 2.5 Flash**: Fast, real-time chat interactions
- **Google Gemini 2.5 Pro**: Deep understanding, 2M token context window
- **Google text-embedding-004**: 768-dimensional vector embeddings
- **FAISS**: Fast similarity search for peer matching
- **scikit-learn**: t-SNE and K-Means for Struggle Map clustering

### Backend
- **FastAPI**: Modern Python web framework with async support
- **Pydantic**: Type-safe data validation
- **Server-Sent Events (SSE)**: Real-time streaming responses
- **Python 3.8+**: Core language

### Frontend
- **Next.js 16**: React framework with App Router
- **TypeScript**: Type safety
- **React 19**: UI library
- **Zustand**: State management
- **Tailwind CSS**: Styling
- **ReactMarkdown**: Markdown rendering

### Deployment
- **Google Cloud Run**: Serverless container platform
- **Google Cloud Secret Manager**: Secure API key storage
- **Docker**: Containerization

---

## Installation & Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- Google Gemini API Key ([Get one here](https://aistudio.google.com/app/apikey))

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yaodu/research-in-public.git
cd research-in-public

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Set up environment variables
export GEMINI_API_KEY='your_api_key_here'
# Or create a .env file with: GEMINI_API_KEY=your_api_key_here

# Start both backend and frontend
python start_dev.py
```

This will start:
- FastAPI backend at `http://localhost:8000`
- Next.js frontend at `http://localhost:3000`

### Manual Start

**Terminal 1 - Backend:**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the Application

- **Frontend:** http://localhost:3000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/

---

## Project Structure

```
research-in-public/
├── agents/                 # AI agents
│   ├── base_agent.py      # Base agent class
│   ├── vent_validator.py  # Emotional support agent
│   ├── semantic_matchmaker.py  # Peer matching agent
│   ├── scribe.py          # Content drafting agent
│   ├── guardian.py        # IP safety agent
│   └── pi_simulator.py    # Grant critique agent
├── api/                   # FastAPI backend
│   └── main.py           # API routes and endpoints
├── config/                # Configuration
│   ├── prompts.py        # Agent system prompts
│   └── settings.py       # Application settings
├── data/                  # Data and schemas
│   ├── schemas.py        # Pydantic models
│   └── dummy_struggles.json  # Sample data
├── evaluation/            # Evaluation metrics
│   ├── empathy_scorer.py  # Empathy scoring
│   └── safety_checker.py  # Safety validation
├── frontend/              # Next.js frontend
│   ├── app/              # Next.js app router
│   ├── components/       # React components
│   └── lib/              # Utilities and stores
├── orchestration/         # Agent coordination
│   ├── agent_orchestrator.py  # Central orchestrator
│   └── intent_classifier.py  # Intent detection
├── services/              # Core services
│   ├── gemini_service.py  # Gemini API wrapper
│   ├── embedding_service.py  # Embedding generation
│   └── vector_search_local.py  # FAISS vector search
├── tools/                 # Function calling tools
│   ├── social_draft.py   # Social media drafting
│   └── academic_context.py  # Academic context retrieval
├── tests/                 # Test suite
│   └── test_agents.py    # Agent tests
├── requirements.txt       # Python dependencies
└── start_dev.py          # Development startup script
```

---

## Course Curriculum Alignment

This project implements all five days of the Kaggle 5-Day AI Agents Intensive Course:

- **Day 1: Agent Architectures** ✅
  - Multi-agent system with specialized agents
  - Centralized orchestration with intent-based routing
  - Parallel and sequential agent execution patterns

- **Day 2: Tools & MCP** ✅
  - Custom tools for content drafting and academic context retrieval
  - Tool interoperability and fallback mechanisms

- **Day 3: Memory & Context** ✅
  - Conversation history management
  - Context retrieval for personalized responses
  - Vector-based memory for peer matching

- **Day 4: Observability & Evaluation** ✅
  - Comprehensive logging and error handling
  - Agent performance evaluation (empathy, relevance, safety)
  - Real-time monitoring capabilities

- **Day 5: Production Deployment** ✅
  - Scalable architecture with session management
  - Production-ready error handling
  - Google Cloud Run deployment

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agents.py -v

# Run with coverage
pytest tests/ --cov=agents --cov=orchestration --cov-report=html
```

### Test Scenarios

- **Emotional Support:** "I'm frustrated with my research progress"
- **Technical Discussion:** "How does semantic search work?"
- **Grant Review:** "Can you review my grant proposal?"
- **Content Transformation:** "I finally figured out why my experiments failed"

---

## Deployment

For production deployment on Google Cloud Run, see [`docs/DEPLOYMENT_GCP.md`](docs/DEPLOYMENT_GCP.md).

---

## Current Limitations

**Social Media Posting:**
- The system **drafts** content but does not automatically post
- Users must manually review and share the drafted content

**Peer Matching:**
- The system **suggests** anonymous matches based on similar struggles
- No direct connections or messaging between matched users
- Uses demo data (no persistent user database)

---

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) file for details.

**Important Disclaimers:**
- This software is provided for **EDUCATIONAL AND DEMONSTRATION PURPOSES ONLY**
- This application is **NOT a medical tool** and does not provide medical advice, diagnosis, or treatment
- This application does **NOT act as a professional health advisor**, mental health counselor, or medical professional
- The AI agents are designed for educational demonstration and should not be relied upon for health or medical decisions
- See [NOTICE](NOTICE) file for complete disclaimers

---

## Acknowledgments

Built as a capstone project for Kaggle's 5-Day AI Agents Intensive Course with Google, demonstrating comprehensive understanding of multi-agent systems, tool integration, memory management, observability, and production deployment.

**Status:** ✅ **Production Ready** - All core features implemented and tested.

---

## Resources

- [Kaggle 5-Day AI Agents Course](https://www.kaggle.com/learn-guide/5-day-agents)
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Built with ❤️ for the research community**
