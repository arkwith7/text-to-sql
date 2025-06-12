export interface QueryRequest {
  question: string;
  context?: string;
}

export interface QueryResponse {
  query_id?: string;
  sql_query: string;
  data: Record<string, any>[];
  columns: string[];
  row_count: number;
  chart_suggestion?: string;
  insights?: string;
  explanation?: string;
  confidence?: string;
  execution_time: number;
}

export interface TableInfo {
  table_name: string;
  columns: ColumnInfo[];
}

export interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
}

export interface SchemaInfo {
  tables: TableInfo[];
}

export type ChartType = 'bar' | 'line' | 'pie' | 'table';

// User Authentication Types
export interface UserCreate {
  email: string;
  password: string;
  full_name: string;
  company?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  company?: string;
  is_active: boolean;
  created_at: string;
  token_usage: number;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: User;
}

export interface TokenUsageStats {
  user_id: string;
  total_queries: number;
  total_tokens: number;
  input_tokens?: number;
  output_tokens?: number;
  last_query_at?: string;
  daily_usage?: Record<string, number>;
  monthly_usage?: Record<string, number>;
  average_tokens_per_query?: number;
}

// Chat Session Types
export interface ChatSession {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count: number;
}

export interface ChatMessage {
  message_id: string;
  session_id: string;
  user_message: string;
  ai_response: string;
  query_result?: Record<string, any>;
  timestamp: string;
  sequence_number: number;
}

export interface CreateSessionRequest {
  title?: string;
  context?: string;
}

export interface AddMessageRequest {
  user_message: string;
  ai_response: string;
  query_result?: Record<string, any>;
}

export interface SessionListResponse {
  sessions: ChatSession[];
  total_count: number;
}

export interface SessionMessagesResponse {
  session_id: string;
  messages: ChatMessage[];
  total_count: number;
}
