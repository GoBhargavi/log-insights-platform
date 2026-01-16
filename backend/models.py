from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class LogEntry(BaseModel):
    """Represents a single parsed log line."""
    timestamp: datetime
    level: str  # e.g., INFO, ERROR, WARN
    message: str
    source: Optional[str] = None # e.g., module name

class LogSummary(BaseModel):
    """Summary statistics for the current dataset."""
    total_count: int
    error_count: int
    warning_count: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]

class FilterRequest(BaseModel):
    """Criteria to filter logs."""
    level: Optional[str] = None
    keyword: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    context: List[LogEntry]
