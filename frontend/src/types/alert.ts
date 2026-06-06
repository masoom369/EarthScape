export interface AlertRule {
  id: string;
  name: string;
  metric: string;
  operator: string;
  threshold: number;
  severity: string;
  is_active: boolean;
  created_by: string;
  created_at: string;
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  climate_record_id: string;
  triggered_value: number;
  severity: string;
  acknowledged: boolean;
  triggered_at: string;
}
