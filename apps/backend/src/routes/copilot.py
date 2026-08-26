from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db
from database.models import Location, Alert, RiskScore, EnvironmentalReading, VideoEvent, AIDecision
from database.schemas import CopilotQueryRequest, CopilotQueryResponse
from services.copilot.agent import AeroMindCopilot

router = APIRouter(prefix="/api/v1/copilot", tags=["AI Copilot"])

copilot = AeroMindCopilot()

@router.post("/query", response_model=CopilotQueryResponse)
async def query_copilot(req: CopilotQueryRequest, db: Session = Depends(get_db)):
    # 1. Fetch grounded database state
    locations = db.query(Location).filter_by(is_active=True).all()
    loc_data = [{"id": l.id, "name": l.name, "baseline_temp": l.baseline_temp_c} for l in locations]

    # Active alerts
    alerts = db.query(Alert).filter(Alert.status.in_(["OPEN", "ACKNOWLEDGED"])).order_by(desc(Alert.created_at)).limit(8).all()
    alert_data = [{"id": a.id, "title": a.title, "message": a.message, "severity": a.severity, "status": a.status} for a in alerts]

    # Top risk scores
    risks = db.query(RiskScore).order_by(desc(RiskScore.timestamp)).limit(6).all()
    risk_data = []
    for r in risks:
        loc = db.query(Location).filter_by(id=r.location_id).first()
        risk_data.append({
            "location_id": r.location_id,
            "location_name": loc.name if loc else "Sector",
            "overall_score": r.overall_score,
            "severity": r.severity,
            "calculation_breakdown": r.calculation_breakdown
        })

    # Recent anomalies
    anomalies = db.query(EnvironmentalReading).filter_by(is_anomaly=True).order_by(desc(EnvironmentalReading.timestamp)).limit(6).all()
    anomaly_data = [{
        "metric": an.metric,
        "value": an.value,
        "anomaly_score": an.anomaly_score,
        "location_id": an.location_id
    } for an in anomalies]

    # Recent visual events
    video_events = db.query(VideoEvent).order_by(desc(VideoEvent.timestamp)).limit(6).all()
    video_data = [{
        "type": v.event_type,
        "severity": v.severity,
        "description": v.description,
        "confidence": v.confidence
    } for v in video_events]

    # Recent AI decisions
    decisions = db.query(AIDecision).order_by(desc(AIDecision.timestamp)).limit(4).all()
    decision_data = [{
        "action": d.action,
        "priority": d.priority,
        "explanation": d.explanation
    } for d in decisions]

    grounded_context = {
        "locations": loc_data,
        "alerts": alert_data,
        "risk_assessments": risk_data,
        "anomalies": anomaly_data,
        "visual_hazards": video_data,
        "decisions": decision_data
    }

    # 2. Run grounded copilot reasoning
    result = await copilot.query(
        user_query=req.query,
        grounded_data=grounded_context,
        conversation_history=req.conversation_history
    )

    return result
