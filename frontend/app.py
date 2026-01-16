import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Backend URL
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Log Explorer", page_icon="🔍", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Global Fonts */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    
    /* Chat Messages */
    .stChatMessage {
        background-color: transparent;
    }
    .stChatMessage.user-message {
        background-color: #e3f2fd;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 500;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2c3e50;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar - Navigation & Upload
st.sidebar.title("🔍 Log Explorer")
page = st.sidebar.radio("Go to", ["💬 Chat with Logs", "📊 Dashboard"])

st.sidebar.divider()
st.sidebar.header("Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Log CSV", type=["csv"])

if uploaded_file:
    with st.spinner("Processing file..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            response = requests.post(f"{API_URL}/upload", files=files)
            
            if response.status_code == 200:
                st.sidebar.success(f"Processed {response.json().get('records_processed')} records.")
            else:
                st.sidebar.error(f"Error: {response.text}")
        except requests.exceptions.ConnectionError:
            st.sidebar.error("Cannot connect to backend. Is FastAPI running?")

# --- PAGE: CHAT ---
if page == "💬 Chat with Logs":
    st.title("💬 Chat with your Logs")
    st.caption("Ask questions about your uploaded logs using RAG + Ollama.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask about errors, specific events, or trends..."):
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Call Backend API
        try:
            chat_resp = requests.post(f"{API_URL}/chat", json={"query": prompt})
            if chat_resp.status_code == 200:
                data = chat_resp.json()
                answer = data["answer"]
                context_logs = data.get("context", [])
                
                # Format the response
                full_response = answer
                if context_logs:
                    full_response += "\n\n**Context (Top Matches):**"
                    for i, log in enumerate(context_logs[:3]):
                        full_response += f"\n- `{log['timestamp']}` [{log['level']}]: {log['message']}"

                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(full_response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                error_msg = "Sorry, I encountered an error communicating with the backend."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        except Exception as e:
            st.error(f"Error: {e}")
        except requests.exceptions.ConnectionError:
             st.error("Cannot connect to backend.")

# --- PAGE: DASHBOARD ---
elif page == "📊 Dashboard":
    st.title("📊 Log Metrics Dashboard")
    
    try:
        # 1. Fetch Summary
        summary_resp = requests.get(f"{API_URL}/summary")
        if summary_resp.status_code == 200:
            summary = summary_resp.json()
            
            # Display Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Logs", summary["total_count"])
            col2.metric("Errors", summary["error_count"], delta_color="inverse")
            col3.metric("Warnings", summary["warning_count"], delta_color="inverse")
            
            start_time = pd.to_datetime(summary["start_time"]) if summary["start_time"] else None
            end_time = pd.to_datetime(summary["end_time"]) if summary["end_time"] else None
            duration = end_time - start_time if start_time and end_time else "N/A"
            col4.metric("Time Span", str(duration).split('.')[0] if duration != "N/A" else "N/A")

            st.divider()

            # 2. Filtering & Data Table
            st.subheader("Explore Logs")
            
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                level_filter = st.selectbox("Filter by Level", ["ALL", "INFO", "WARNING", "ERROR"])
            with filter_col2:
                keyword_filter = st.text_input("Search Keyword")

            # Prepare filter payload
            payload = {}
            if level_filter != "ALL":
                payload["level"] = level_filter
            if keyword_filter:
                payload["keyword"] = keyword_filter
                
            # Fetch filtered logs
            logs_resp = requests.post(f"{API_URL}/filter", json=payload)
            if logs_resp.status_code == 200:
                logs_data = logs_resp.json()
                
                if logs_data:
                    df = pd.DataFrame(logs_data)
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    
                    # Show Dataframe
                    st.dataframe(
                        df, 
                        column_config={
                            "timestamp": st.column_config.DatetimeColumn("Timestamp", format="D MMM YYYY, h:mm a"),
                            "level": st.column_config.TextColumn("Level"),
                            "message": st.column_config.TextColumn("Message"),
                            "source": st.column_config.TextColumn("Source"),
                        },
                        use_container_width=True
                    )
                    
                    # Visualizations
                    st.subheader("Visualizations")
                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        st.caption("Logs by Level")
                        level_counts = df["level"].value_counts()
                        st.bar_chart(level_counts)
                    
                    with chart_col2:
                        st.caption("Logs over Time (Minute Intervals)")
                        if not df.empty:
                            # Group by minute
                            time_counts = df.set_index("timestamp").resample("T").size()
                            st.line_chart(time_counts)

                else:
                    st.info("No logs match the current filters.")
            else:
                st.error("Failed to fetch logs.")

    except requests.exceptions.ConnectionError:
        st.warning("Waiting for backend connection... Please ensure `uvicorn backend.main:app --reload` is running.")
