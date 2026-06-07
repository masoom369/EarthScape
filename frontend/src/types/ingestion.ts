export interface IngestionLog {
  id: string;
  filename: string;
  file_hash: string;
  hdfs_path: string | null;
  format: string;
  record_count: number;
  status: "pending" | "success" | "failed";
  error_message: string | null;
  triggered_by: string;
  created_at: string;
}

export interface PaginatedIngestionLogs {
  items: IngestionLog[];
  total: number;
  page: number;
  limit: number;
}