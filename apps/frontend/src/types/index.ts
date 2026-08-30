export interface User {
  email: string;
  role: 'admin' | 'operator' | 'analyst' | string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

export interface Location {
  id: string;
  name: string;
  code: string;
  zone_type: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  baseline_temp_c: number;
  risk_threshold: number;
  current_risk_score: number;
  current_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  current_temp_c: number;
  metadata?: Record<string, any>;
}

export interface TemperatureReading {
  location_id: string;
  location_name?: string;
  timestamp: string;
  ambient_temp_c: number;
  surface_temp_c?: number;
  heat_index_c?: number;
  rate_of_change_c_per_hr: number;
  is_anomaly: boolean;
  anomaly_score: number;
  source_provider: string;
}

export interface RiskFactor {
  name: string;
  category: string;
  score_contribution: number;
  weight: number;
  description: string;
  evidence?: Record<string, any>;
}

export interface RiskScore {
  location_id: string;
  location_name?: string;
  timestamp: string;
  overall_score: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  factors: RiskFactor[];
  calculation_breakdown: string;
}

export interface Alert {
  id: string;
  location_id: string;
  location_name?: string;
  event_id?: string;
  title: string;
  message: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  created_at: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  resolved_at?: string;
  resolved_by?: string;
}

export interface AIDecision {
  id: string;
  location_id: string;
  location_name?: string;
  timestamp: string;
  action: string;
  priority: 'IMMEDIATE' | 'HIGH' | 'MEDIUM' | 'LOW';
  explanation: string;
  evidence: Record<string, any>;
  confidence: number;
  recommended_response: string;
}

export interface RiskEvent {
  id: string;
  location_id: string;
  location_name?: string;
  event_type: string;
  timestamp: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  confidence: number;
  description: string;
  evidence: Record<string, any>;
  snapshot_reference?: string;
}

export interface Camera {
  id: string;
  location_id: string;
  location_name?: string;
  name: string;
  code: string;
  camera_type: string;
  status: string;
  fps: number;
  resolution: string;
  stream_url?: string;
  danger_zones: Array<{
    name: string;
    polygon: number[][];
    severity?: string;
  }>;
}

export interface HardwareTelemetry {
  platform: string;
  cpu_model: string;
  cpu_cores: number;
  cpu_percent: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_percent: number;
  has_gpu: boolean;
  gpu_name?: string;
  cuda_available: boolean;
  cuda_version?: string;
  vram_total_mb?: number;
  vram_used_mb?: number;
}

export interface ProviderStatus {
  provider_name: string;
  status: 'CONNECTED' | 'DISCONNECTED' | 'ERROR' | 'NOT_CONFIGURED';
  base_url?: string;
  latency_ms?: number;
  message: string;
}

export interface SystemStatus {
  status: 'HEALTHY' | 'DEGRADED' | 'CRITICAL';
  uptime_seconds: number;
  database_connected: boolean;
  active_websocket_connections: number;
  hardware: HardwareTelemetry;
  providers: ProviderStatus[];
  inference_fps: number;
  active_camera_streams: number;
  demo_mode_active: boolean;
}

export interface ForecastPoint {
  location_id: string;
  forecast_timestamp: string;
  hour_offset: number;
  predicted_temp_c: number;
  predicted_humidity_pct: number;
  predicted_risk_score: number;
  confidence_interval_lower: number;
  confidence_interval_upper: number;
}

export interface VideoJobStatus {
  job_id: string;
  video_path: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress_pct: number;
  total_frames: number;
  processed_frames: number;
  fps: number;
  detections_count: number;
  events_count: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  summary_report?: any;
}
