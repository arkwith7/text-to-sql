export interface QueryRequest {
  question: string;
}

export interface QueryResponse {
  sql_query: string;
  data: Record<string, any>[];
  columns: string[];
  chart_suggestion?: string;
  insights?: string;
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
  last_query_at?: string;
}
