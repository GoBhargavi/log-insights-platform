# 📊 AI-Assisted Log & Metrics Explorer

A modern, full-stack application for analyzing system logs, visualizing metrics, and chatting with your data using local AI. 

Built with **FastAPI**, **Streamlit**, and **Ollama**.

## ✨ Key Features

- **Upload & Parse**: Ingest CSV log files instantly.
- **Interactive Dashboard**: Visualize error rates, warning trends, and log distribution over time.
- **RAG Chatbot**: Chat naturally with your logs using Retrieval-Augmented Generation.
- **Agentic Workflow**: A "Relevance Grader" agent validates search results to reduce hallucinations.
- **Local AI**: Fully private execution using **Ollama** (Llama 2, Llama 3.2, etc.).
- **Premium UI**: Polished interface with custom CSS and responsive design.

## 🛠️ Tech Stack

- **Backend**: FastAPI, Uvicorn, Pydantic
- **Frontend**: Streamlit, Pandas, Plotly (via Streamlit charts)
- **AI / ML**: SentenceTransformer (`all-MiniLM-L6-v2`), Ollama
- **Storage**: In-Memory (Vector embeddings & Log entries)

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed and running

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/log-explorer.git
cd log-explorer
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `backend/.env` file:
```env
PORT=8000
HOST=0.0.0.0
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
```

### 3. Run the Application
You need three terminal tabs:

**Terminal 1 (Ollama Service)**
```bash
ollama serve
```

**Terminal 2 (Backend)**
```bash
cd backend
python main.py
```

**Terminal 3 (Frontend)**
```bash
streamlit run frontend/app.py
```

### 4. Explore!
Open your browser to `http://localhost:8501`.

---

## 📈 Development Journey & Agentic Evolution

This project evolved from a simple log viewer to an intelligent, agentic system. Here is the step-by-step evolution:

| Stage | Feature Added | Description |
| :--- | :--- | :--- |
| **1. Foundation** | **FastAPI Backend** | Created `POST /upload` and `GET /summary` endpoints with Pydantic validation. |
| **2. Visualization** | **Streamlit UI** | Built a dashboard with metric cards and time-series line charts. |
| **3. RAG V1** | **Vector Search** | Integrated `sentence-transformers` to index logs and perform semantic search. |
| **4. RAG V2** | **Ollama Chat** | Connected a local LLM to generate natural language answers from log context. |
| **5. Experience** | **UI Design** | Switched to a "Chat-First" layout and injected custom CSS for a premium look. |
| **6. Accuracy** | **Agentic RAG** | **Crucial Upgrade**: Added a "Grader Agent" loop. <br>• **Problem**: The LLM was getting distracted by irrelevant logs. <br>• **Solution**: Implemented a step where an AI "Judge" evaluates if a retrieved log is actually relevant to the user's specific question *before* passing it to the answer generator. |
| **7. Tuning** | **Prompt Engineering** | **Refinement**: <br>• Adjusted the "Judge" to accept warnings as relevant context for errors.<br>• Instructed the "Generator" to act as an SRE, spotting patterns (e.g., "Retrying" logs) to avoid false claims about system crashes. |

## 🧠 Design Decisions

- **In-Memory Vector Store**: Kept architecture simple for a "drag-and-drop" analysis tool without external database dependencies.
- **Separation of Concerns**: Strict backend/frontend split allows independent scaling or replacing the UI later.
- **Local-First**: Prioritized privacy and zero-cost operation by using local embeddings and Ollama.
