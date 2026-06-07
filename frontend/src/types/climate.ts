export interface Location {
  region: string;
  lat: number | null;
  lon: number | null;
}

export interface ClimateRecord {
  id: string;
  source_type: string;
  location: Location;
  timestamp: string;
  temperature_c: number | null;
  precipitation_mm: number | null;
  humidity_pct: number | null;
  co2_ppm: number | null;
  is_anomaly: boolean;
  is_archived: boolean;
  ingestion_id: string | null;
  created_at: string;
}

export interface PaginatedClimateRecords {
  items: ClimateRecord[];
  total: number;
  page: number;
  limit: number;
}

export interface ClimateSummaryItem {
  region: string;
  period: string;
  avg_temperature_c: number | null;
  total_precipitation_mm: number | null;
  record_count: number;
  anomaly_count: number;
}

export interface ClimateSummaryResponse {
  items: ClimateSummaryItem[];
}