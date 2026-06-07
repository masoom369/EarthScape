export interface MLResult {
  id: string;
  model_type: string;
  trained_at: string;
  record_count: number;
  accuracy_score: number | null;
  predictions: Record<string, unknown>[];
  anomaly_record_ids: string[];
  correlation_matrix: Record<string, Record<string, number | null>> | null;
  forecast_data: Array<{ region: string; date: string; forecast_temp_c: number }> | null;
  job_id: string | null;
}