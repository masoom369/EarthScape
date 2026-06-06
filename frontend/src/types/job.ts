export interface JobLog {
  id: string;
  job_type: string;
  job_name: string;
  status: string;
  hdfs_input?: string;
  hdfs_output?: string;
  duration_seconds?: number;
  triggered_by: string;
  started_at: string;
  completed_at?: string;
  error?: string;
}

export interface PaginatedJobs {
  items: JobLog[];
  total: number;
  page: number;
  limit: number;
}
