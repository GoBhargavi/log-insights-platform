from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
try:
    from .models import LogSummary, LogEntry, FilterRequest, ChatRequest, ChatResponse
    from . import services
    from .rag_service import rag_service
except ImportError:
    from models import LogSummary, LogEntry, FilterRequest, ChatRequest, ChatResponse
    import services
    from rag_service import rag_service

import logging
import os
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

#Imported required libraries for Fast API and utility functions from utility files. 

#initializing Fast API
app = FastAPI(title="Log & Metrics Explorer API")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Log Insights Platform...")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    logger.info(f"Configured Ollama URL: {ollama_url}")
    logger.info(f"Configured Ollama Model: {model}")
    
    try:
        resp = requests.get(ollama_url, timeout=3)
        if resp.status_code == 200:
            logger.info("Successfully connected to Ollama service.")
        else:
            logger.warning(f"Ollama reachable, but returned status code: {resp.status_code}")
    except requests.exceptions.ConnectionError:
        logger.error(f"Failed to connect to Ollama at {ollama_url}. RAG features will return errors.")
    except Exception as e:
        logger.error(f"Unexpected error when checking Ollama: {e}")

#Defined API endpoints for file upload, log summary, log filtering, and chat with logs.
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads and parses a CSV log file."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    content = await file.read()
    try:
        services.clear_store() # Reset for this simple demo
        count = services.parse_csv_file(content)
        
        # Trigger Indexing
        rag_service.index_logs(services.get_all_logs())
        
        return {"message": "File parsed and indexed successfully", "records_processed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summary", response_model=LogSummary)
def get_summary():
    """Returns summary statistics of the loaded logs."""
    return services.calculate_summary()

@app.post("/filter", response_model=List[LogEntry])
def get_filtered_logs(criteria: FilterRequest):
    """Returns list of logs matching the filter criteria."""
    return services.filter_logs(criteria)

@app.post("/chat", response_model=ChatResponse)
def chat_with_logs(request: ChatRequest):
    """Searches logs and returns a heuristic answer."""
    return rag_service.generate_response(request.query)

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
