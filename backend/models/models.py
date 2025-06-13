"""
SQLAlchemy models for the application database.

These models define the structure for:
- User management
- Authentication tokens
- Query analytics
- System events
- Performance metrics
"""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Float, Integer, Text, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid

# Import the Base from database.connection_manager to ensure models are registered correctly
from database.connection_manager import Base

class User(Base):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    company = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True), nullable=True)
    token_usage = Column(Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', role='{self.role}')>"

class RefreshToken(Base):
    """Refresh token model for JWT token management."""
    
    __tablename__ = "refresh_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    device_info = Column(JSON, nullable=True)  # Store device/browser info
    
    user = relationship("User")

    def __repr__(self):
        return f"<RefreshToken(id='{self.id}', user_id='{self.user_id}', active='{self.is_active}')>"

class QueryAnalytics(Base):
    """Query analytics model for tracking SQL query execution."""
    
    __tablename__ = "query_analytics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=False)
    execution_time = Column(Float, nullable=False)  # in seconds
    row_count = Column(Integer, nullable=False)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    chart_type = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    
    user = relationship("User")

    def __repr__(self):
        return f"<QueryAnalytics(id='{self.id}', user_id='{self.user_id}', success='{self.success}')>"

class Event(Base):
    """General event tracking model."""
    
    __tablename__ = "events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    event_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True) # Support for IPv4 and IPv6
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(36), nullable=True)
    
    user = relationship("User")

    def __repr__(self):
        return f"<Event(id='{self.id}', type='{self.event_type}', user_id='{self.user_id}')>"

class PerformanceMetric(Base):
    """Performance metrics model for system monitoring."""
    
    __tablename__ = "performance_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    additional_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<PerformanceMetric(name='{self.metric_name}', value='{self.metric_value}')>"

class UserSession(Base):
    """User session tracking model."""
    
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    session_start = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    session_end = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    queries_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id='{self.user_id}', active='{self.is_active}')>"

class APIKey(Base):
    """API key model for programmatic access."""
    
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    permissions = Column(JSON, nullable=True)  # Granular permissions
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    user = relationship("User")

    def __repr__(self):
        return f"<APIKey(id='{self.id}', name='{self.key_name}', active='{self.is_active}')>"

class QueryTemplate(Base):
    """Query template model for saved/common queries."""
    
    __tablename__ = "query_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)  # Null for public templates
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    question_template = Column(Text, nullable=False)
    sql_template = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Admin verified
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    user = relationship("User")

    def __repr__(self):
        return f"<QueryTemplate(id='{self.id}', name='{self.name}', public='{self.is_public}')>"

class DatabaseSchema(Base):
    """Database schema information cache."""
    
    __tablename__ = "database_schemas"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    database_name = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    schema_info = Column(JSON, nullable=False)
    last_updated = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    row_count = Column(Integer, nullable=True)
    table_size = Column(String(50), nullable=True)  # Human readable size
    
    def __repr__(self):
        return f"<DatabaseSchema(database='{self.database_name}', table='{self.table_name}')>"

class AuditLog(Base):
    """Audit log model for security and compliance."""
    
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    user = relationship("User")
    
    def __repr__(self):
        return f"<AuditLog(id='{self.id}', action='{self.action}', success='{self.success}')>"

class SystemConfig(Base):
    """System configuration model."""
    
    __tablename__ = "system_config"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_key = Column(String(100), nullable=False, unique=True)
    config_value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False, nullable=False)  # Don't log sensitive configs
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    updated_by = Column(String(36), nullable=True)
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.config_key}', sensitive='{self.is_sensitive}')>"


class ChatSession(Base):
    """Chat session model for managing conversation sessions."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)  # Optional session title
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    message_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id='{self.id}', user_id='{self.user_id}', active='{self.is_active}')>"


class ChatMessage(Base):
    """Chat message model for storing individual messages in conversations."""
    
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Query-related fields (for assistant messages)
    query_id = Column(String(36), nullable=True)  # Link to query analytics
    sql_query = Column(Text, nullable=True)
    query_result = Column(JSON, nullable=True)  # Store query results as JSON
    execution_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    sequence_number = Column(Integer, nullable=False)  # Order within session
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id='{self.id}', type='{self.message_type}', session_id='{self.session_id}')>"
