from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import pandas as pd
from openai import AzureOpenAI
import json
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Business Analytics Assistant", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

# Pydantic models
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    sql_query: str
    data: List[Dict[str, Any]]
    columns: List[str]
    chart_suggestion: Optional[str] = None
    insights: Optional[str] = None

class SchemaInfo(BaseModel):
    tables: List[Dict[str, Any]]

# Database schema information for LLM context
def get_database_schema():
    """Get database schema information"""
    try:
        with engine.connect() as conn:
            # Get all tables
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
            tables_result = conn.execute(text(tables_query)).fetchall()
            
            schema_info = []
            for table in tables_result:
                table_name = table[0]
                
                # Get columns for each table
                columns_query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = :table_name 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
                """
                columns_result = conn.execute(text(columns_query), {"table_name": table_name}).fetchall()
                
                columns = [
                    {
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2] == "YES"
                    }
                    for col in columns_result
                ]
                
                schema_info.append({
                    "table_name": table_name,
                    "columns": columns
                })
                
            return schema_info
    except Exception as e:
        logger.error(f"Error getting database schema: {e}")
        return []

def generate_sql_from_question(question: str) -> str:
    """Generate SQL query from natural language question using Azure OpenAI"""
    
    schema = get_database_schema()
    schema_text = ""
    
    for table in schema:
        schema_text += f"\nTable: {table['table_name']}\n"
        for col in table['columns']:
            schema_text += f"  - {col['name']} ({col['type']})\n"
    
    system_prompt = f"""You are a SQL expert. Convert natural language questions to SQL queries for a PostgreSQL database.

Database Schema:
{schema_text}

Important Notes:
- This is a Northwind database with e-commerce data
- Use proper PostgreSQL syntax
- Return only the SQL query, no explanations
- Use appropriate JOINs when needed
- Format dates properly
- Use LIMIT for large result sets (default: 100)

Example queries:
- "Show top 5 products by sales" → SELECT p.product_name, SUM(od.unit_price * od.quantity) as total_sales FROM products p JOIN order_details od ON p.product_id = od.product_id GROUP BY p.product_id, p.product_name ORDER BY total_sales DESC LIMIT 5;
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        # Remove any markdown formatting
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
            
        return sql_query.strip()
        
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating SQL: {str(e)}")

def suggest_chart_type(data: List[Dict], columns: List[str]) -> str:
    """Suggest appropriate chart type based on data"""
    if len(data) == 0:
        return "table"
    
    if len(columns) == 2:
        # Check if we have numeric data
        first_row = data[0]
        values = list(first_row.values())
        
        if isinstance(values[1], (int, float)):
            if len(data) <= 10:
                return "bar"
            else:
                return "line"
    
    if len(columns) > 2:
        return "table"
        
    return "table"

def generate_insights(question: str, data: List[Dict]) -> str:
    """Generate insights from the query results"""
    if not data:
        return "No data found for this query."
    
    # Limit data for LLM context
    sample_data = data[:5] if len(data) > 5 else data
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system", 
                    "content": "You are a business analyst. Provide brief, actionable insights from the query results. Focus on key trends, patterns, or recommendations. Keep it concise (2-3 sentences)."
                },
                {
                    "role": "user", 
                    "content": f"Question: {question}\n\nResults: {json.dumps(sample_data, default=str)}\n\nProvide insights:"
                }
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return "Unable to generate insights at this time."

@app.get("/")
async def root():
    return {"message": "Smart Business Analytics Assistant API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/schema")
async def get_schema():
    """Get database schema information"""
    try:
        schema = get_database_schema()
        return SchemaInfo(tables=schema)
    except Exception as e:
        logger.error(f"Error in get_schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute natural language query"""
    try:
        # Generate SQL from question
        sql_query = generate_sql_from_question(request.question)
        logger.info(f"Generated SQL: {sql_query}")
        
        # Execute SQL query
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            columns = list(result.keys())
            data = [dict(row._mapping) for row in result.fetchall()]
        
        # Convert any non-serializable types
        for row in data:
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None
                elif isinstance(value, pd.Timestamp):
                    row[key] = value.isoformat()
        
        # Suggest chart type
        chart_suggestion = suggest_chart_type(data, columns)
        
        # Generate insights
        insights = generate_insights(request.question, data)
        
        return QueryResponse(
            sql_query=sql_query,
            data=data,
            columns=columns,
            chart_suggestion=chart_suggestion,
            insights=insights
        )
        
    except Exception as e:
        logger.error(f"Error in execute_query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
