#!/usr/bin/env python3
"""
Script to create chat tables directly using SQLAlchemy.
This is a workaround for Alembic migration issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection_manager import DatabaseManager
from app.database.models import Base, ChatSession, ChatMessage
from app.config import get_settings
import asyncio

async def create_chat_tables():
    """Create chat tables if they don't exist."""
    db_manager = None
    try:
        settings = get_settings()
        db_manager = DatabaseManager()
        
        # Initialize the database connection
        await db_manager.initialize()
        
        print("Creating chat tables...")
        
        # Check if tables exist first
        check_sessions = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='chat_sessions';
        """
        
        check_messages = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='chat_messages';
        """
        
        sessions_result = await db_manager.execute_query_safe(check_sessions, database_type="app")
        messages_result = await db_manager.execute_query_safe(check_messages, database_type="app")
        
        if not sessions_result.get("data"):
            print("Creating chat_sessions table...")
            create_sessions_sql = """
            CREATE TABLE chat_sessions (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                title VARCHAR(255),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL,
                updated_at DATETIME,
                last_message_at DATETIME,
                message_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users (id)
            );
            """
            await db_manager.execute_query_safe(create_sessions_sql, database_type="app")
            
            # Create index
            create_index_sql = "CREATE INDEX ix_chat_sessions_user_id ON chat_sessions (user_id);"
            await db_manager.execute_query_safe(create_index_sql, database_type="app")
            print("✅ chat_sessions table created")
        else:
            print("✅ chat_sessions table already exists")
            
        if not messages_result.get("data"):
            print("Creating chat_messages table...")
            create_messages_sql = """
            CREATE TABLE chat_messages (
                id VARCHAR(36) PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL,
                message_type VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                query_id VARCHAR(36),
                sql_query TEXT,
                query_result JSON,
                execution_time REAL,
                error_message TEXT,
                timestamp DATETIME NOT NULL,
                sequence_number INTEGER NOT NULL,
                FOREIGN KEY(session_id) REFERENCES chat_sessions (id)
            );
            """
            await db_manager.execute_query_safe(create_messages_sql, database_type="app")
            
            # Create index
            create_index_sql = "CREATE INDEX ix_chat_messages_session_id ON chat_messages (session_id);"
            await db_manager.execute_query_safe(create_index_sql, database_type="app")
            print("✅ chat_messages table created")
        else:
            print("✅ chat_messages table already exists")
            
        print("\n🎉 Chat tables setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if db_manager:
            await db_manager.close_all_connections()

if __name__ == "__main__":
    asyncio.run(create_chat_tables())
