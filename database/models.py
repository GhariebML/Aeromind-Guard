import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime,
    ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship
from database.connection import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    users = relationship("User", back_populates="organization")
    locations = relationship("Location", back_populates="organization")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="OPERATOR")  # ADMIN, OPERATOR, ANALYST, VIEWER
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="users")

class Location(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, index=True)
    zone_type = Column(String(50), default="FACILITY")  # FACILITY, INDUSTRIAL, PERIMETER, URBAN, ROOFTOP
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation_m = Column(Float, default=0.0)
    baseline_temp_c = Column(Float, default=24.0)
    risk_threshold = Column(Float, default=70.0)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="locations")
    data_sources = relationship("DataSource", back_populates="location")
    cameras = relationship("Camera", back_populates="location")
    alerts = relationship("Alert", back_populates="location")
    risk_scores = relationship("RiskScore", back_populates="location")

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)  # FORTYGUARD, OPEN_METEO, IOT_SENSOR, SYNTHETIC_DEMO
    source_type = Column(String(50), nullable=False)  # WEATHER_API, THERMAL_SENSOR, IOT_STATION, UAV
    status = Column(String(50), default="ACTIVE")  # ACTIVE, INACTIVE, ERROR, NOT_CONFIGURED
    is_demo = Column(Boolean, default=False)
    config = Column(JSON, default=dict)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    location = relationship("Location", back_populates="data_sources")
    readings = relationship("EnvironmentalReading", back_populates="data_source")

class EnvironmentalReading(Base):
    __tablename__ = "environmental_readings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("data_sources.id"), index=True)
    location_id = Column(String(36), ForeignKey("locations.id"), index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    metric = Column(String(100), nullable=False, index=True)  # ambient_temp, surface_temp, humidity, air_quality, wind_speed
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    quality = Column(Float, default=1.0)  # 0.0 to 1.0 confidence/quality score
    is_anomaly = Column(Boolean, default=False, index=True)
    anomaly_score = Column(Float, default=0.0)
    metadata_json = Column(JSON, default=dict)

    data_source = relationship("DataSource", back_populates="readings")

    __table_args__ = (
        Index("idx_env_reading_loc_time", "location_id", "timestamp"),
        Index("idx_env_reading_metric_time", "metric", "timestamp"),
    )

class TemperatureReading(Base):
    __tablename__ = "temperature_readings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(36), ForeignKey("locations.id"), index=True)
    source_id = Column(String(36), ForeignKey("data_sources.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    ambient_temp_c = Column(Float, nullable=False)
    surface_temp_c = Column(Float, nullable=True)
    heat_index_c = Column(Float, nullable=True)
    rate_of_change_c_per_hr = Column(Float, default=0.0)
    is_anomaly = Column(Boolean, default=False, index=True)
    anomaly_score = Column(Float, default=0.0)
    source_provider = Column(String(50), default="INTERNAL")
    metadata_json = Column(JSON, default=dict)

    __table_args__ = (
        Index("idx_temp_reading_loc_time", "location_id", "timestamp"),
    )

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(36), ForeignKey("locations.id"), index=True)
    generated_at = Column(DateTime(timezone=True), default=utc_now)
    forecast_timestamp = Column(DateTime(timezone=True), index=True)
    predicted_temp_c = Column(Float, nullable=False)
    predicted_humidity_pct = Column(Float, nullable=True)
    predicted_risk_score = Column(Float, default=0.0)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    provider = Column(String(50), default="FORTYGUARD")
    metadata_json = Column(JSON, default=dict)

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(36), ForeignKey("locations.id"), index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True)
    stream_url = Column(String(500), nullable=True)
    camera_type = Column(String(50), default="CCTV_OPTICAL")  # CCTV_OPTICAL, THERMAL, DRONE_UAV, EDGE_CAM
    status = Column(String(50), default="ONLINE")  # ONLINE, OFFLINE, DEGRADED
    fps = Column(Float, default=30.0)
    resolution = Column(String(50), default="1920x1080")
    fov_degrees = Column(Float, default=90.0)
    danger_zones = Column(JSON, default=list)  # Polygon coordinates for danger zones
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    location = relationship("Location", back_populates="cameras")
    video_events = relationship("VideoEvent", back_populates="camera")
    detections = relationship("Detection", back_populates="camera")

class VideoEvent(Base):
    __tablename__ = "video_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    camera_id = Column(String(36), ForeignKey("cameras.id"), index=True)
    location_id = Column(String(36), ForeignKey("locations.id"), index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # SMOKE_DETECTED, FIRE_DETECTED, PERSON_IN_DANGER_ZONE, VEHICLE_EVENT, CROWD_EVENT
    confidence = Column(Float, nullable=False)
    severity = Column(String(50), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    snapshot_path = Column(String(500), nullable=True)
    video_job_id = Column(String(100), nullable=True, index=True)
    metadata_json = Column(JSON, default=dict)

    camera = relationship("Camera", back_populates="video_events")

class Detection(Base):
    __tablename__ = "detections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    camera_id = Column(String(36), ForeignKey("cameras.id"), index=True)
    video_job_id = Column(String(100), nullable=True, index=True)
    frame_index = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    class_name = Column(String(100), nullable=False, index=True)  # person, vehicle, smoke, fire, machinery
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    track_id = Column(Integer, nullable=True, index=True)
    in_danger_zone = Column(Boolean, default=False)
    metadata_json = Column(JSON, default=dict)

    camera = relationship("Camera", back_populates="detections")

class Track(Base):
    __tablename__ = "tracks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    camera_id = Column(String(36), ForeignKey("cameras.id"), index=True)
    track_id = Column(Integer, nullable=False, index=True)
    class_name = Column(String(100), nullable=False)
    first_seen = Column(DateTime(timezone=True), default=utc_now)
    last_seen = Column(DateTime(timezone=True), default=utc_now)
    total_frames = Column(Integer, default=1)
    avg_velocity_px_per_s = Column(Float, default=0.0)
    trajectory = Column(JSON, default=list)  # list of [x, y, timestamp]
    is_active = Column(Boolean, default=True)

class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(36), ForeignKey("locations.id"), index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    overall_score = Column(Float, nullable=False)  # 0 to 100
    severity = Column(String(50), nullable=False)  # LOW (0-29), MEDIUM (30-59), HIGH (60-79), CRITICAL (80-100)
    temperature_anomaly_factor = Column(Float, default=0.0)
    visual_hazard_factor = Column(Float, default=0.0)
    rate_of_change_factor = Column(Float, default=0.0)
    proximity_hazard_factor = Column(Float, default=0.0)
    persistence_factor = Column(Float, default=0.0)
    forecast_multiplier = Column(Float, default=1.0)
    factors_json = Column(JSON, default=list)
    calculation_breakdown = Column(Text, nullable=True)

    location = relationship("Location", back_populates="risk_scores")

    __table_args__ = (
        Index("idx_risk_score_loc_time", "location_id", "timestamp"),
    )

class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(36), ForeignKey("locations.id"), index=True)
    event_type = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    severity = Column(String(50), nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, default=0.9)
    description = Column(Text, nullable=False)
    evidence = Column(JSON, default=dict)
    snapshot_reference = Column(String(500), nullable=True)
    related_tracks = Column(JSON, default=list)
    related_sensor_data = Column(JSON, default=dict)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(36), ForeignKey("locations.id"), index=True)
    event_id = Column(String(36), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="OPEN", index=True)  # OPEN, ACKNOWLEDGED, RESOLVED
    channels = Column(JSON, default=lambda: ["DASHBOARD", "WEBSOCKET"])
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(255), nullable=True)
    metadata_json = Column(JSON, default=dict)

    location = relationship("Location", back_populates="alerts")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(36), ForeignKey("locations.id"), index=True)
    risk_event_id = Column(String(36), nullable=True, index=True)
    priority = Column(String(50), default="HIGH")  # IMMEDIATE, HIGH, MEDIUM, LOW
    action = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    evidence = Column(JSON, default=dict)
    recommended_procedure = Column(Text, nullable=True)
    is_executed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class AIDecision(Base):
    __tablename__ = "ai_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_id = Column(String(36), ForeignKey("locations.id"), index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    action = Column(String(255), nullable=False)
    priority = Column(String(50), nullable=False)
    explanation = Column(Text, nullable=False)
    evidence = Column(JSON, default=dict)
    confidence = Column(Float, default=0.95)
    recommended_response = Column(Text, nullable=False)
    grounded_context = Column(JSON, default=dict)

class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_name = Column(String(100), nullable=False, index=True)  # INGESTION_STARTED, MODEL_INFERENCE, RISK_CALCULATED, etc.
    level = Column(String(50), default="INFO")  # INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    source = Column(String(100), default="BACKEND")
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    task = Column(String(100), nullable=False)  # DETECTION, TRACKING, ANOMALY, RISK
    version = Column(String(50), nullable=False)
    framework = Column(String(50), default="PYTORCH")
    model_path = Column(String(500), nullable=False)
    parameters_count = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    metrics = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_path = Column(String(500), nullable=False)
    camera_id = Column(String(36), ForeignKey("cameras.id"), nullable=True, index=True)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)
    status = Column(String(50), default="QUEUED", index=True)  # QUEUED, PROCESSING, COMPLETED, FAILED
    progress_pct = Column(Float, default=0.0)
    total_frames = Column(Integer, default=0)
    processed_frames = Column(Integer, default=0)
    fps = Column(Float, default=0.0)
    detections_count = Column(Integer, default=0)
    events_count = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    summary_report = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), index=True, nullable=True)
    user_role = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    prompt_category = Column(String(100), nullable=True)
    tool_requested = Column(String(100), nullable=True)
    tool_executed = Column(Boolean, default=False)
    authorization_status = Column(String(50), nullable=True) # AUTHORIZED, UNAUTHORIZED, N/A
    result_summary = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)

