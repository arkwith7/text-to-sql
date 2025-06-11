from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import pandas as pd
from openai import AzureOpenAI
import json
import logging
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT and Security Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

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

# User Authentication Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    email: str
    full_name: str
    company: Optional[str] = None
    is_active: bool
    created_at: datetime
    token_usage: int = 0

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenUsageStats(BaseModel):
    user_id: str
    total_queries: int
    total_tokens: int
    last_query_at: Optional[datetime] = None

# Authentication functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user

def create_user_table():
    """Create users table if it doesn't exist"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    company VARCHAR(255),
                    hashed_password VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    token_usage INTEGER DEFAULT 0
                );
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_queries (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(36) REFERENCES users(id),
                    question TEXT NOT NULL,
                    sql_query TEXT NOT NULL,
                    tokens_used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.commit()
            logger.info("User tables created successfully")
    except Exception as e:
        logger.error(f"Error creating user tables: {e}")

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, email, full_name, company, hashed_password, is_active, created_at, token_usage
                FROM users WHERE email = :email
            """), {"email": email}).fetchone()
            
            if result:
                return dict(result._mapping)
            return None
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, email, full_name, company, is_active, created_at, token_usage
                FROM users WHERE id = :user_id
            """), {"user_id": user_id}).fetchone()
            
            if result:
                user_data = dict(result._mapping)
                return User(**user_data)
            return None
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None

def create_user(user_create: UserCreate) -> Optional[User]:
    """Create a new user"""
    try:
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_create.password)
        
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (id, email, full_name, company, hashed_password)
                VALUES (:id, :email, :full_name, :company, :hashed_password)
            """), {
                "id": user_id,
                "email": user_create.email,
                "full_name": user_create.full_name,
                "company": user_create.company,
                "hashed_password": hashed_password
            })
            conn.commit()
            
            return get_user_by_id(user_id)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

def update_user_token_usage(user_id: str, tokens_used: int):
    """Update user's token usage"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE users SET token_usage = token_usage + :tokens_used
                WHERE id = :user_id
            """), {"user_id": user_id, "tokens_used": tokens_used})
            conn.commit()
    except Exception as e:
        logger.error(f"Error updating token usage: {e}")

def log_user_query(user_id: str, question: str, sql_query: str, tokens_used: int = 1):
    """Log user query for analytics"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO user_queries (user_id, question, sql_query, tokens_used)
                VALUES (:user_id, :question, :sql_query, :tokens_used)
            """), {
                "user_id": user_id,
                "question": question,
                "sql_query": sql_query,
                "tokens_used": tokens_used
            })
            conn.commit()
            
            # Update user's total token usage
            update_user_token_usage(user_id, tokens_used)
    except Exception as e:
        logger.error(f"Error logging user query: {e}")

def get_user_stats(user_id: str) -> Optional[TokenUsageStats]:
    """Get user's usage statistics"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_queries,
                    SUM(tokens_used) as total_tokens,
                    MAX(created_at) as last_query_at
                FROM user_queries 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()
            
            if result:
                stats = dict(result._mapping)
                return TokenUsageStats(
                    user_id=user_id,
                    total_queries=stats['total_queries'] or 0,
                    total_tokens=stats['total_tokens'] or 0,
                    last_query_at=stats['last_query_at']
                )
            return TokenUsageStats(user_id=user_id, total_queries=0, total_tokens=0)
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return None

# Initialize database tables
create_user_table()

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

# Authentication endpoints
@app.post("/auth/register", response_model=Token)
async def register(user_create: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = get_user_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = create_user(user_create)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@app.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    """Login user"""
    user_data = get_user_by_email(user_login.email)
    if not user_data or not verify_password(user_login.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user_data["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    user = get_user_by_id(user_data["id"])
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@app.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@app.get("/auth/stats", response_model=TokenUsageStats)
async def get_my_stats(current_user: User = Depends(get_current_user)):
    """Get current user's usage statistics"""
    stats = get_user_stats(current_user.id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )
    return stats

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
async def execute_query(request: QueryRequest, current_user: User = Depends(get_current_user)):
    """Execute natural language query (authenticated users only)"""
    try:
        # Generate SQL from question
        sql_query = generate_sql_from_question(request.question)
        logger.info(f"Generated SQL for user {current_user.email}: {sql_query}")
        
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
        
        # Log user query for analytics
        log_user_query(current_user.id, request.question, sql_query, tokens_used=1)
        
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
