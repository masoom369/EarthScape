export interface Location {
  region: string;
  lat?: number;
  lon?: number;
}

export interface ClimateRecord {
  id: string;
  source_type: string;
  location: Location;
  timestamp: string;
  temperature_c?: number;
  precipitation_mm?: number;
  humidity_pct?: number;
  co2_ppm?: number;
  is_anomaly: boolean;
  is_archived: boolean;
}

export interface ClimateSummaryItem {
  region: string;
  period: string;
  avg_temperature_c?: number;
  total_precipitation_mm?: number;
  record_count: number;
  anomaly_count: number;
}

export interface PaginatedClimate {
  items: ClimateRecord[];
  total: number;
  page: number;
  limit: number;
}
