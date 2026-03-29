import streamlit as st
import pandas as pd
import json
import requests
import time
import mysql.connector

# --- Configuration ---
GEMINI_API_KEY = "AIzaSyAvdT9Vm491QHG7TZvNqWtOSL9soUVC_7I"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
MAX_RETRIES = 5
RETRY_DELAY = 1

# --- DATABASE SCHEMA ---
DATABASE_SCHEMA = """
TABLE martdatabase (
    `ItemId` INT PRIMARY KEY,
    `NameOfItem` VARCHAR(100),
    `Code` VARCHAR(45),
    `SaleQty` INT,
    `Amt` FLOAT,
    `Amt+GST` FLOAT,  <-- Update this line
    `ClosingST` INT,
    `Month` DATETIME,
    `Year` INT
)

CRITICAL INSTRUCTIONS FOR SQL GENERATION:
1. ALWAYS wrap ALL column names in backticks: `NameOfItem`, `Amt+GST`, `Month`, etc.
2. The `Month` column is DATETIME type - use MONTHNAME(`Month`) or MONTH(`Month`) for filtering
   - For month names: WHERE MONTHNAME(`Month`) = 'April'
   - For month numbers: WHERE MONTH(`Month`) = 4
   - For year: WHERE YEAR(`Month`) = 2025 OR use the `Year` column
3. For text search on items: WHERE `NameOfItem` LIKE '%keyword%'
4. Table name is 'martdatabase'

EXAMPLE VALID QUERIES:
- SELECT * FROM martdatabase WHERE MONTHNAME(`Month`) = 'April' AND `Year` = 2025
- SELECT `NameOfItem`, SUM(`Amt+GST`) as total FROM martdatabase WHERE `Year` = 2024 GROUP BY `NameOfItem`
- SELECT * FROM martdatabase WHERE `NameOfItem` LIKE '%DOVE%'
- SELECT `NameOfItem`, SUM(`SaleQty`) as TotalSales FROM martdatabase GROUP BY `NameOfItem` ORDER BY TotalSales DESC LIMIT 10
"""

# --- Database Interaction ---
def execute_mysql_query(sql_query: str) -> pd.DataFrame:
    """Executes a MySQL query and returns a Pandas DataFrame."""
    st.info(f"**Executing SQL:** `{sql_query}`")

    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASSWORD = "Prem@2004"
    DB_NAME = "mahaveermart"

    conn = None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        df = pd.read_sql(sql_query, conn)
        return df

    except Exception as e:
        st.error(f"**Database Query Error:** {e}")
        st.error("Please check that your query is valid and the table exists.")
        return pd.DataFrame()

    finally:
        if conn and conn.is_connected():
            conn.close()

# --- LLM API Function ---
def convert_nl_to_sql(nl_query: str) -> str:
    """Converts natural language to MySQL query using Gemini API."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "":
        st.error("Please set your GEMINI_API_KEY")
        return ""
        
    with st.status("Translating Natural Language to SQL...", expanded=True) as status:
        system_prompt = (
            "You are an expert MySQL query generator for a supermarket database.\n\n"
            "CRITICAL RULES:\n"
            "1. ALWAYS wrap ALL column names in backticks: `NameOfItem`, `Code`, `Amt+GST`, `Month`, `Year`, etc.\n"
            "2. Table name is 'martdatabase'\n"
            "3. `Month` column is DATETIME - MUST use MONTHNAME(`Month`) = 'April' or MONTH(`Month`) = 4\n"
            "4. NEVER compare `Month` directly to text like 'April' - always use MONTHNAME() or MONTH()\n"
            "5. When filtering by product name, use: WHERE `NameOfItem` LIKE '%searchterm%'\n"
            "6. Return ONLY valid MySQL syntax in JSON format\n\n"
            "Database Schema:\n" + DATABASE_SCHEMA
        )

        user_query = f"Convert this request to a MySQL query: {nl_query}"

        payload = {
            "contents": [{"parts": [{"text": user_query}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "sql_query": {
                            "type": "STRING",
                            "description": "Valid MySQL query"
                        }
                    }
                }
            }
        }

        headers = {'Content-Type': 'application/json'}

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                
                result = response.json()
                json_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '{}')
                parsed_json = json.loads(json_text)
                sql_query = parsed_json.get('sql_query', '').strip()
                
                status.update(label="Translation Complete ✓", state="complete")
                return sql_query

            except requests.exceptions.RequestException as e:
                time.sleep(RETRY_DELAY * (2**attempt))
                if attempt == MAX_RETRIES - 1:
                    st.error("Failed to connect to Gemini API")
                    status.update(label="Translation Failed", state="error")
                    return ""
            except (json.JSONDecodeError, KeyError) as e:
                st.error(f"Invalid API response: {e}")
                status.update(label="Translation Failed", state="error")
                return ""

        return ""

# --- Visualization ---
def display_results(df: pd.DataFrame, query: str):
    """Displays results in a table and chart."""
    if df.empty:
        st.warning("The query returned no data. Try refining your request.")
        return

    st.subheader("Query Results")
    
    # Display table
    st.markdown("Data Table")
    st.dataframe(df, use_container_width=True)

    # Visualization
    st.markdown("Visualization")
    
    if df.shape[1] == 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
        try:
            if 'month' in df.columns[0].lower() or 'year' in df.columns[0].lower():
                st.line_chart(df.set_index(df.columns[0]))
                st.caption("Line chart showing trend over time")
            else:
                st.bar_chart(df.set_index(df.columns[0]))
                st.caption(f"Bar chart comparing {df.columns[0]}")
        except Exception as e:
            st.info("Chart rendering skipped - displaying table only")
    else:
        st.info("Tip: Ask for aggregated data (e.g., 'total sales by month') for better visualizations")

# --- Streamlit App ---
st.set_page_config(page_title="Supermarket Analytics Chatbot", layout="wide")

st.title("🛒 Supermarket Analytics Chatbot")
st.markdown("""
Ask questions about your sales data in natural language!

**Examples:**
- *"Show me total sales for April 2024"*
- *"What items contain 'DETTOL' in their name?"*
- *"Total Amt+GST by month"*
- *"Top 10 products by sales quantity"*
""")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            st.markdown(message["content"])
            if message.get("data") is not None:
                display_results(message["data"], message["query"])

# Handle user input
if prompt := st.chat_input("Ask about your sales data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            sql_query = convert_nl_to_sql(prompt)
            
            if sql_query:
                df_results = execute_mysql_query(sql_query)
                response_message = "Data fetched successfully!"
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_message,
                    "data": df_results,
                    "query": sql_query
                })
                
                st.markdown(response_message)
                display_results(df_results, sql_query)
            else:
                error_msg = "Could not generate SQL query. Please rephrase your request."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "data": None,
                    "query": ""
                })

# Sidebar
st.sidebar.header("Configuration")
if GEMINI_API_KEY:
    st.sidebar.success("Gemini API Key configured")
else:
    st.sidebar.error("Gemini API Key missing")

st.sidebar.header("Database Info")
st.sidebar.code("""Table: martdatabase
Columns:
- ItemId (INT)
- NameOfItem (VARCHAR)
- Code (VARCHAR)
- SaleQty (INT)
- Amt (FLOAT)
- Amt+GST (FLOAT)
- ClosingST (INT)
- Month (VARCHAR) ← TEXT not DATETIME
- Year (INT)""", language="text")

st.sidebar.header("Tips")
st.sidebar.markdown("""
- Use month names: "April", "January"
- Refer to columns naturally
- Ask for aggregations: "total", "sum", "average"
- Filter by year: "in 2024", "for 2025"
""")