from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
try:
    from .models import LogEntry
except ImportError:
    from models import LogEntry

import os
from dotenv import load_dotenv

load_dotenv()

class RAGService:
    def __init__(self):
        # Load model name from env or default
        model_name = os.getenv("RAG_MODEL_NAME", "all-MiniLM-L6-v2")
        print(f"Loading RAG model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.embeddings = None
        self.logs: List[LogEntry] = []
        
    def index_logs(self, logs: List[LogEntry]):
        """Creates embeddings for the provided logs."""
        self.logs = logs
        if not logs:
            self.embeddings = None
            return

        # Prepare text to embed: simplify to "LEVEL: Message" for better semantic search
        texts = [f"{log.level}: {log.message}" for log in logs]
        self.embeddings = self.model.encode(texts)
        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches for logs relevant to the query."""
        if self.embeddings is None or not self.logs:
            return []
            
        query_embedding = self.model.encode([query])[0]
        
        # Calculate cosine similarity
        # (a . b) / (|a| * |b|)
        # sentence-transformers embeddings are already normalized usually, but let's be safe
        scores = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "log": self.logs[idx],
                "score": float(scores[idx])
            })
            
        return results

    def grade_relevance(self, query: str, log_entry: str) -> bool:
        """
        Agent 1: The Grader.
        Uses LLM to decide if a log entry is relevant to the query.
        Returns True if relevant, False otherwise.
        """
        prompt = f"""You are a log relevance checker. Determine if this log entry could help answer the question.

Question: {query}
Log Entry: {log_entry}

Consider the log relevant if:
- It directly answers the question
- It provides related context (e.g., warnings before errors, related system events)
- It mentions the same components or timeframes

Answer ONLY with 'YES' or 'NO'."""
        
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
        
        try:
            import requests
            response = requests.post(
                f"{ollama_base_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30 # Grader should be fast
            )
            if response.status_code == 200:
                answer = response.json().get("response", "").strip().upper()
                return "YES" in answer
        except Exception as e:
            print(f"Grader Error: {e}")
            return True # Fallback to permissive if grader fails
            
        return False

    def generate_response(self, query: str) -> Dict[str, Any]:
        """
        Retrieves relevant logs, grades them, and generates an answer using Local Ollama.
        """
        # 1. Retrieval
        raw_results = self.search(query, top_k=5) # Fetch more candidates for grading
        
        # 2. Grading (Agent 1)
        relevant_logs = []
        for res in raw_results:
            log = res['log']
            log_str = f"[{log.timestamp}] {log.level}: {log.message}"
            
            # Call Grader Agent
            if self.grade_relevance(query, log_str):
                relevant_logs.append(log)
        
        if not relevant_logs:
             return {
                "answer": "I found some logs, but after double-checking, none of them seemed directly relevant to your specific question.",
                "context": []
            }

        # 3. Generation (Agent 2)
        # Prepare Context String
        context_str = "\n".join([f"[{log.timestamp}] {log.level}: {log.message}" for log in relevant_logs])
        
        # Prepare Prompt for Ollama
        prompt = f"""You are a senior system reliability engineer analyzing logs.
Your goal is to explain EXACTLY what happened based on the provided log sequence.

Guidelines:
1. Look at the TIMESTAMP order. What happened first? What happened next?
2. Do NOT assume the application crashed unless you see a "CRITICAL" or "Shutting down" log.
3. If you see an ERROR followed by an INFO (e.g. "Retrying"), mention that the system attempted recovery.
4. Synthesize a short narrative: "First X happened, then Y happened."

Log Sequence:
{context_str}

User Question: {query}

Analysis:"""

        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
        
        answer = "Error generating response from Ollama."
        
        try:
            import requests
            response = requests.post(
                f"{ollama_base_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120 
            )
            if response.status_code == 200:
                answer = response.json().get("response", "No response content.")
            else:
                answer = f"Ollama Error ({response.status_code}): {response.text}"
        except Exception as e:
            answer = f"Failed to connect to Ollama: {str(e)}"

        return {
            "answer": answer,
            "context": relevant_logs
        }

# Global singleton
rag_service = RAGService()
