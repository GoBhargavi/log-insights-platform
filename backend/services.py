import csv
import io
from datetime import datetime
from typing import List, Optional
try:
    from .models import LogEntry, LogSummary, FilterRequest
except ImportError:
    from models import LogEntry, LogSummary, FilterRequest

# Global in-memory store
_LOG_STORE: List[LogEntry] = []

def clear_store():
    """Clears the global log store."""
    global _LOG_STORE
    _LOG_STORE = []

def add_log_entry(entry: LogEntry):
    """Adds a single entry to the store."""
    _LOG_STORE.append(entry)

def get_all_logs() -> List[LogEntry]:
    """Returns all stored logs."""
    return _LOG_STORE

def parse_csv_file(file_content: bytes) -> int:
    """
    Parses a CSV file content and populates the store.
    Expected CSV columns: timestamp, level, message, source (optional)
    Returns the number of records parsed.
    """
    decoded = file_content.decode("utf-8")
    io_stream = io.StringIO(decoded)
    reader = csv.DictReader(io_stream)
    
    count = 0
    new_entries = []
    
    for row in reader:
        # Basic validation and fallback
        try:
            ts_str = row.get("timestamp", "").strip()
            # Try parsing ISO format, fallback to now if empty (for demo robustness)
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str)
                except ValueError:
                    ts = datetime.now() # Fallback for demo
            else:
                ts = datetime.now()

            entry = LogEntry(
                timestamp=ts,
                level=row.get("level", "INFO").upper(),
                message=row.get("message", ""),
                source=row.get("source")
            )
            new_entries.append(entry)
            count += 1
        except Exception:
            continue # Skip malformed rows for now
            
    _LOG_STORE.extend(new_entries)
    return count

def calculate_summary() -> LogSummary:
    """Calculates summary stats from the current store."""
    if not _LOG_STORE:
        return LogSummary(
            total_count=0,
            error_count=0,
            warning_count=0,
            start_time=None,
            end_time=None
        )
    
    error_count = sum(1 for log in _LOG_STORE if log.level == "ERROR")
    warning_count = sum(1 for log in _LOG_STORE if log.level == "WARNING")
    
    # Sort by timestamp for start/end time
    sorted_logs = sorted(_LOG_STORE, key=lambda x: x.timestamp)
    
    return LogSummary(
        total_count=len(_LOG_STORE),
        error_count=error_count,
        warning_count=warning_count,
        start_time=sorted_logs[0].timestamp,
        end_time=sorted_logs[-1].timestamp
    )

def filter_logs(criteria: FilterRequest) -> List[LogEntry]:
    """Filters logs based on criteria."""
    filtered = _LOG_STORE
    
    if criteria.level:
        filtered = [log for log in filtered if log.level == criteria.level.upper()]
        
    if criteria.keyword:
        kw = criteria.keyword.lower()
        filtered = [log for log in filtered if kw in log.message.lower() or (log.source and kw in log.source.lower())]
        
    if criteria.start_date:
        filtered = [log for log in filtered if log.timestamp >= criteria.start_date]
        
    if criteria.end_date:
        filtered = [log for log in filtered if log.timestamp <= criteria.end_date]
        
    return filtered
