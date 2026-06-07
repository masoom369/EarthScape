export type AlertSeverity = "low" | "medium" | "high";
export type AlertMetric = "temperature_c" | "precipitation_mm" | "co2_ppm" | "humidity_pct";
export type AlertOperator = ">" | "<" | "=" | ">=" | "<=";

export interface AlertRule {
  id: string;
  name: string;
  metric: AlertMetric;
  operator: AlertOperator;
  threshold: number;
  severity: AlertSeverity;
  is_active: boolean;
  created_by: string;
  created_at: string;
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  climate_record_id: string;
  triggered_value: number;
  severity: AlertSeverity;
  acknowledged: boolean;
  acknowledged_by: string | null;
  triggered_at: string;
  notification_log: Record<string, unknown> | null;
}

export interface PaginatedAlertEvents {
  items: AlertEvent[];
  total: number;
  page: number;
  limit: number;
}