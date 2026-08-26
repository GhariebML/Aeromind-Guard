import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

# Standard System Error Model
class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    error_code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Standard WebSocket Event Envelope
class WebSocketEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_type: str = Field(..., description="e.g. telemetry.updated, risk.updated, alert.created")
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = Field(default_factory=dict)

# Location Schemas
class LocationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    code: str
    zone_type: str = "FACILITY"
    latitude: float
    longitude: float
    elevation_m: float = 0.0
    baseline_temp_c: float = 24.0
    risk_threshold: float = 70.0
    is_active: bool = True
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

class LocationCreate(LocationBase):
    organization_id: Optional[str] = None

class LocationResponse(LocationBase):
    id: str
    current_risk_score: float = 0.0
    current_severity: str = "LOW"
    current_temp_c: float = 24.0
    created_at: datetime

# Temperature Reading Schemas
class TemperatureReadingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    location_id: str
    source_id: Optional[str] = None
    timestamp: datetime
    ambient_temp_c: float
    surface_temp_c: Optional[float] = None
    heat_index_c: Optional[float] = None
    rate_of_change_c_per_hr: float = 0.0
    is_anomaly: bool = False
    anomaly_score: float = 0.0
    source_provider: str = "INTERNAL"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

class TemperatureReadingResponse(TemperatureReadingBase):
    id: str

# Environmental Reading Schemas
class EnvironmentalReadingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    location_id: str
    source_id: Optional[str] = None
    timestamp: datetime
    metric: str
    value: float
    unit: str
    quality: float = 1.0
    is_anomaly: bool = False
    anomaly_score: float = 0.0
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

class EnvironmentalReadingResponse(EnvironmentalReadingBase):
    id: str

# Anomaly Schemas
class AnomalyResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    metric: str
    value: float
    baseline: float
    z_score: float
    rate_of_change: float
    anomaly_score: float  # Normalized 0 to 1
    is_anomaly: bool
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    timestamp: datetime
    location_id: str

# Risk Engine Schemas
class RiskFactorBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    category: str  # ENVIRONMENTAL, VISUAL, TEMPORAL, PROXIMITY, FORECAST
    score_contribution: float
    weight: float
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)

class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    location_id: str
    location_name: Optional[str] = None
    timestamp: datetime
    overall_score: float = Field(..., ge=0.0, le=100.0)
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    factors: List[RiskFactorBreakdown]
    calculation_breakdown: str
    is_anomaly_present: bool
    recommended_action: Optional[str] = None

# Forecast Schemas
class ForecastBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    location_id: str
    forecast_timestamp: datetime
    hour_offset: int = 1
    predicted_temp_c: float
    predicted_humidity_pct: Optional[float] = None
    predicted_risk_score: float = 0.0
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    provider: str = "FORTYGUARD"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

# Camera & Detection Schemas
class CameraBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    location_id: str
    name: str
    code: str
    stream_url: Optional[str] = None
    camera_type: str = "CCTV_OPTICAL"
    status: str = "ONLINE"
    fps: float = 30.0
    resolution: str = "1920x1080"
    fov_degrees: float = 90.0
    danger_zones: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True

class CameraResponse(CameraBase):
    id: str
    created_at: datetime

class DetectionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    object_id: str
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    timestamp: datetime
    camera_id: str
    track_id: Optional[int] = None
    in_danger_zone: bool = False
    source_frame: int = 0
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

class TrackedObjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    track_id: int
    class_name: str
    bbox: List[float]
    first_seen: datetime
    last_seen: datetime
    total_frames: int = 1
    avg_velocity_px_per_s: float = 0.0
    trajectory: List[List[float]] = Field(default_factory=list)
    is_active: bool = True
    in_danger_zone: bool = False

# Video Analysis Job Schemas
class VideoJobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    job_id: str
    video_path: str
    camera_id: Optional[str] = None
    location_id: Optional[str] = None
    status: str  # QUEUED, PROCESSING, COMPLETED, FAILED
    progress_pct: float
    total_frames: int
    processed_frames: int
    fps: float
    detections_count: int
    events_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    summary_report: Optional[Dict[str, Any]] = None

# Alert Schemas
class AlertBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    location_id: str
    event_id: Optional[str] = None
    title: str
    message: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    status: str = "OPEN"  # OPEN, ACKNOWLEDGED, RESOLVED
    channels: List[str] = Field(default_factory=lambda: ["DASHBOARD", "WEBSOCKET"])
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

class AlertResponse(AlertBase):
    id: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class AlertActionRequest(BaseModel):
    operator_name: str = "Lead Safety Officer"
    note: Optional[str] = None

# AI Decision Schemas
class AIDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    location_id: str
    timestamp: datetime
    action: str
    priority: str
    explanation: str
    evidence: Dict[str, Any]
    confidence: float
    recommended_response: str
    grounded_context: Dict[str, Any]

# Copilot Schemas
class CopilotQueryRequest(BaseModel):
    query: str
    location_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)

class CopilotQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    query: str
    answer: str
    grounded_data: Dict[str, Any]
    sources_used: List[str]
    is_llm_active: bool
    model_name: str
    timestamp: datetime
