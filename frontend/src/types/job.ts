export type JobStatus = "queued" | "running" | "completed" | "failed";
export type MapReduceJobType = "temperature_agg" | "precipitation_totals" | "anomaly_scores";
export type MLModelType = "anomaly_detection" | "trend_prediction" | "correlation";

export interface JobLog {
  id: string;
  job_type: string;
  job_name: string;
  status: JobStatus;
  hdfs_input: string | null;
  hdfs_output: string | null;
  duration_seconds: number | null;
  triggered_by: string;
  started_at: string;
  completed_at: string | null;
  error: string | null;
}

export interface PaginatedJobLogs {
  items: JobLog[];
  total: number;
  page: number;
  limit: number;
}