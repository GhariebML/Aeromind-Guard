from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from apps.backend.src.auth import get_current_user
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db
from database.models import (
    Location, TemperatureReading, EnvironmentalReading,
    RiskScore, RiskEvent, Alert, AIDecision, Camera,
    Detection, Track, ModelVersion
)
from database.schemas import AlertActionRequest
from services.risk_engine.calculator import RiskEngine
from services.prediction_engine.forecaster import RiskForecaster
from apps.backend.src.websocket_hub import ws_hub

router = APIRouter(prefix="/api/v1", tags=["Physical AI Intelligence"], dependencies=[Depends(get_current_user)])

risk_engine = RiskEngine()
forecaster = RiskForecaster()

# --- LOCATIONS ---
@router.get("/locations")
async def list_locations(db: Session = Depends(get_db)):
    locs = db.query(Location).filter_by(is_active=True).all()
    results = []
    for loc in locs:
        # Get latest risk score
        latest_risk = db.query(RiskScore).filter_by(location_id=loc.id).order_by(desc(RiskScore.timestamp)).first()
        latest_temp = db.query(TemperatureReading).filter_by(location_id=loc.id).order_by(desc(TemperatureReading.timestamp)).first()
        results.append({
            "id": loc.id,
            "name": loc.name,
            "code": loc.code,
            "zone_type": loc.zone_type,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "elevation_m": loc.elevation_m,
            "baseline_temp_c": loc.baseline_temp_c,
            "risk_threshold": loc.risk_threshold,
            "current_risk_score": latest_risk.overall_score if latest_risk else 15.0,
            "current_severity": latest_risk.severity if latest_risk else "LOW",
            "current_temp_c": latest_temp.ambient_temp_c if latest_temp else loc.baseline_temp_c,
            "metadata": loc.metadata_json
        })
    return results

# --- TEMPERATURE ---
@router.get("/temperature/current")
async def get_current_temperatures(db: Session = Depends(get_db)):
    locs = db.query(Location).filter_by(is_active=True).all()
    results = []
    for loc in locs:
        latest = db.query(TemperatureReading).filter_by(location_id=loc.id).order_by(desc(TemperatureReading.timestamp)).first()
        if latest:
            results.append({
                "location_id": loc.id,
                "location_name": loc.name,
                "timestamp": latest.timestamp,
                "ambient_temp_c": latest.ambient_temp_c,
                "surface_temp_c": latest.surface_temp_c,
                "heat_index_c": latest.heat_index_c,
                "rate_of_change_c_per_hr": latest.rate_of_change_c_per_hr,
                "is_anomaly": latest.is_anomaly,
                "anomaly_score": latest.anomaly_score,
                "source_provider": latest.source_provider
            })
    return results

@router.get("/temperature/history")
async def get_temperature_history(
    location_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(TemperatureReading)
    if location_id:
        query = query.filter_by(location_id=location_id)
    records = query.order_by(desc(TemperatureReading.timestamp)).limit(limit).all()
    return [{
        "id": r.id,
        "location_id": r.location_id,
        "timestamp": r.timestamp,
        "ambient_temp_c": r.ambient_temp_c,
        "surface_temp_c": r.surface_temp_c,
        "rate_of_change_c_per_hr": r.rate_of_change_c_per_hr,
        "is_anomaly": r.is_anomaly,
        "anomaly_score": r.anomaly_score,
        "source_provider": r.source_provider
    } for r in reversed(records)]

# --- ENVIRONMENTAL READINGS ---
@router.get("/environment/readings")
async def get_environmental_readings(
    metric: Optional[str] = None,
    location_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(EnvironmentalReading)
    if location_id:
        query = query.filter_by(location_id=location_id)
    if metric:
        query = query.filter_by(metric=metric)
    records = query.order_by(desc(EnvironmentalReading.timestamp)).limit(limit).all()
    return [{
        "id": r.id,
        "location_id": r.location_id,
        "timestamp": r.timestamp,
        "metric": r.metric,
        "value": r.value,
        "unit": r.unit,
        "quality": r.quality,
        "is_anomaly": r.is_anomaly,
        "anomaly_score": r.anomaly_score
    } for r in reversed(records)]

# --- FORECAST ---
@router.get("/forecast")
async def get_forecast(location_id: Optional[str] = None, db: Session = Depends(get_db)):
    loc = None
    if location_id:
        loc = db.query(Location).filter_by(id=location_id).first()
    if not loc:
        loc = db.query(Location).filter_by(is_active=True).first()

    if not loc:
        raise HTTPException(status_code=404, detail="No active location found.")

    latest_temp = db.query(TemperatureReading).filter_by(location_id=loc.id).order_by(desc(TemperatureReading.timestamp)).first()
    curr_temp = latest_temp.ambient_temp_c if latest_temp else loc.baseline_temp_c
    roc = latest_temp.rate_of_change_c_per_hr if latest_temp else 0.2

    forecast_series = forecaster.forecast_risk_trajectory(
        location_id=loc.id,
        current_temp_c=curr_temp,
        rate_of_change_c_per_hr=roc,
        baseline_temp_c=loc.baseline_temp_c
    )
    return {
        "location_id": loc.id,
        "location_name": loc.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "series": forecast_series
    }

# --- ANOMALIES ---
@router.get("/anomalies")
async def get_anomalies(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    records = db.query(EnvironmentalReading).filter_by(is_anomaly=True).order_by(desc(EnvironmentalReading.timestamp)).limit(limit).all()
    results = []
    for r in records:
        loc = db.query(Location).filter_by(id=r.location_id).first()
        results.append({
            "id": r.id,
            "location_id": r.location_id,
            "location_name": loc.name if loc else "Unknown Sector",
            "timestamp": r.timestamp,
            "metric": r.metric,
            "value": r.value,
            "unit": r.unit,
            "anomaly_score": r.anomaly_score,
            "severity": "CRITICAL" if r.anomaly_score >= 0.8 else ("HIGH" if r.anomaly_score >= 0.6 else "MEDIUM")
        })
    return results

# --- RISK SCORES ---
@router.get("/risk/current")
async def get_current_risk_scores(db: Session = Depends(get_db)):
    locs = db.query(Location).filter_by(is_active=True).all()
    results = []
    for loc in locs:
        latest = db.query(RiskScore).filter_by(location_id=loc.id).order_by(desc(RiskScore.timestamp)).first()
        if latest:
            results.append({
                "location_id": loc.id,
                "location_name": loc.name,
                "timestamp": latest.timestamp,
                "overall_score": latest.overall_score,
                "severity": latest.severity,
                "factors": latest.factors_json,
                "calculation_breakdown": latest.calculation_breakdown
            })
    return results

@router.get("/risk/history")
async def get_risk_history(
    location_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(RiskScore)
    if location_id:
        query = query.filter_by(location_id=location_id)
    records = query.order_by(desc(RiskScore.timestamp)).limit(limit).all()
    return [{
        "id": r.id,
        "location_id": r.location_id,
        "timestamp": r.timestamp,
        "overall_score": r.overall_score,
        "severity": r.severity,
        "factors_count": len(r.factors_json or [])
    } for r in reversed(records)]

# --- EVENTS ---
@router.get("/events")
async def get_events(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    records = db.query(RiskEvent).order_by(desc(RiskEvent.timestamp)).limit(limit).all()
    results = []
    for r in records:
        loc = db.query(Location).filter_by(id=r.location_id).first()
        results.append({
            "id": r.id,
            "location_id": r.location_id,
            "location_name": loc.name if loc else "Sector",
            "event_type": r.event_type,
            "timestamp": r.timestamp,
            "severity": r.severity,
            "risk_score": r.risk_score,
            "confidence": r.confidence,
            "description": r.description,
            "evidence": r.evidence,
            "snapshot_reference": r.snapshot_reference
        })
    return results

# --- ALERTS ---
@router.get("/alerts")
async def get_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if status:
        query = query.filter_by(status=status)
    if severity:
        query = query.filter_by(severity=severity)
    records = query.order_by(desc(Alert.created_at)).limit(limit).all()
    results = []
    for r in records:
        loc = db.query(Location).filter_by(id=r.location_id).first()
        results.append({
            "id": r.id,
            "location_id": r.location_id,
            "location_name": loc.name if loc else "Sector",
            "event_id": r.event_id,
            "title": r.title,
            "message": r.message,
            "severity": r.severity,
            "status": r.status,
            "created_at": r.created_at,
            "acknowledged_at": r.acknowledged_at,
            "acknowledged_by": r.acknowledged_by,
            "resolved_at": r.resolved_at,
            "resolved_by": r.resolved_by
        })
    return results

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, action: AlertActionRequest, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.acknowledged_by = action.operator_name
    db.commit()
    await ws_hub.broadcast("ALERT_ACKNOWLEDGED", {"alert_id": alert_id, "by": action.operator_name})
    return {"message": "Alert acknowledged successfully", "alert_id": alert_id}

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, action: AlertActionRequest, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolved_by = action.operator_name
    db.commit()
    await ws_hub.broadcast("ALERT_RESOLVED", {"alert_id": alert_id, "by": action.operator_name})
    return {"message": "Alert resolved successfully", "alert_id": alert_id}

# --- DECISIONS & RECOMMENDATIONS ---
@router.get("/decisions")
async def get_decisions(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    records = db.query(AIDecision).order_by(desc(AIDecision.timestamp)).limit(limit).all()
    results = []
    for r in records:
        loc = db.query(Location).filter_by(id=r.location_id).first()
        results.append({
            "id": r.id,
            "location_id": r.location_id,
            "location_name": loc.name if loc else "Sector",
            "timestamp": r.timestamp,
            "action": r.action,
            "priority": r.priority,
            "explanation": r.explanation,
            "evidence": r.evidence,
            "confidence": r.confidence,
            "recommended_response": r.recommended_response
        })
    return results

# --- CAMERAS & STREAMS ---
@router.get("/cameras")
async def get_cameras(db: Session = Depends(get_db)):
    cameras = db.query(Camera).filter_by(is_active=True).all()
    results = []
    for c in cameras:
        loc = db.query(Location).filter_by(id=c.location_id).first()
        results.append({
            "id": c.id,
            "location_id": c.location_id,
            "location_name": loc.name if loc else "Sector",
            "name": c.name,
            "code": c.code,
            "camera_type": c.camera_type,
            "status": c.status,
            "fps": c.fps,
            "resolution": c.resolution,
            "danger_zones": c.danger_zones
        })
    return results

# --- MODEL VERSIONS ---
@router.get("/models")
async def get_models(db: Session = Depends(get_db)):
    models = db.query(ModelVersion).filter_by(is_active=True).all()
    return [{
        "id": m.id,
        "name": m.name,
        "task": m.task,
        "version": m.version,
        "framework": m.framework,
        "model_path": m.model_path,
        "is_active": m.is_active
    } for m in models]
