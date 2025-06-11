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
