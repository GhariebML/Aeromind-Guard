import io
import csv
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db
from database.models import Alert, RiskScore, RiskEvent, Location, AIDecision

router = APIRouter(prefix="/api/v1/reports", tags=["Reports & Export"])

@router.get("/export")
async def export_operational_report(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    
    # Collect summary data
    alerts = db.query(Alert).order_by(desc(Alert.created_at)).limit(100).all()
    risks = db.query(RiskScore).order_by(desc(RiskScore.timestamp)).limit(100).all()
    events = db.query(RiskEvent).order_by(desc(RiskEvent.timestamp)).limit(100).all()
    decisions = db.query(AIDecision).order_by(desc(AIDecision.timestamp)).limit(50).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Report Type", "Timestamp (UTC)", "Entity ID", "Location", "Title / Metric", "Severity / Score", "Status / Action", "Details"])

        for a in alerts:
            loc = db.query(Location).filter_by(id=a.location_id).first()
            writer.writerow(["ALERT", a.created_at.isoformat(), a.id, loc.name if loc else a.location_id, a.title, a.severity, a.status, a.message])

        for r in risks:
            loc = db.query(Location).filter_by(id=r.location_id).first()
            writer.writerow(["RISK_SCORE", r.timestamp.isoformat(), r.id, loc.name if loc else r.location_id, "Composite Risk Score", r.overall_score, r.severity, r.calculation_breakdown.replace("\n", " | ") if r.calculation_breakdown else ""])

        for e in events:
            loc = db.query(Location).filter_by(id=e.location_id).first()
            writer.writerow(["RISK_EVENT", e.timestamp.isoformat(), e.id, loc.name if loc else e.location_id, e.event_type, e.severity, f"Score {e.risk_score}", e.description])

        for d in decisions:
            loc = db.query(Location).filter_by(id=d.location_id).first()
            writer.writerow(["AI_DECISION", d.timestamp.isoformat(), d.id, loc.name if loc else d.location_id, d.action, d.priority, "RECOMMENDATION", d.explanation])

        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=aeromind_incident_report_{now.strftime('%Y%m%d_%H%M%S')}.csv"}
        )

    # JSON output
    report = {
        "generated_at": now.isoformat(),
        "platform": "AeroMind ClimateGuard Physical AI Operations Center",
        "summary": {
            "total_alerts": len(alerts),
            "total_risk_assessments": len(risks),
            "total_events": len(events),
            "total_decisions": len(decisions)
        },
        "alerts": [{
            "id": a.id,
            "title": a.title,
            "severity": a.severity,
            "status": a.status,
            "created_at": a.created_at.isoformat(),
            "message": a.message
        } for a in alerts],
        "risk_assessments": [{
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "location_id": r.location_id,
            "overall_score": r.overall_score,
            "severity": r.severity,
            "breakdown": r.calculation_breakdown
        } for r in risks],
        "events": [{
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "event_type": e.event_type,
            "severity": e.severity,
            "risk_score": e.risk_score,
            "description": e.description
        } for e in events],
        "ai_decisions": [{
            "id": d.id,
            "timestamp": d.timestamp.isoformat(),
            "action": d.action,
            "priority": d.priority,
            "explanation": d.explanation,
            "recommended_response": d.recommended_response
        } for d in decisions]
    }

    return report

@router.get("/compliance-report")
async def generate_hse_compliance_report(db: Session = Depends(get_db)):
    """
    Generates an official audit-ready HSE / OSHA Compliance Incident Summary Document.
    """
    now = datetime.now(timezone.utc)
    alerts = db.query(Alert).order_by(desc(Alert.created_at)).limit(20).all()
    risks = db.query(RiskScore).order_by(desc(RiskScore.timestamp)).limit(20).all()
    locations = db.query(Location).all()

    critical_count = sum(1 for a in alerts if a.severity == "CRITICAL")
    high_count = sum(1 for a in alerts if a.severity == "HIGH")

    rows_html = "".join([
        f"""<tr>
            <td>{a.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
            <td><strong>{a.title}</strong></td>
            <td><span class="badge {a.severity.lower()}">{a.severity}</span></td>
            <td>{a.status}</td>
            <td>{a.acknowledged_by or 'UNACKNOWLEDGED'}</td>
            <td>{a.message}</td>
        </tr>""" for a in alerts
    ])

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AeroMind HSE Compliance Audit Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; color: #0f172a; line-height: 1.5; }}
        .header {{ border-bottom: 3px solid #0284c7; padding-bottom: 16px; margin-bottom: 24px; }}
        .title {{ font-size: 24px; font-weight: 800; color: #0f172a; margin: 0; }}
        .subtitle {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
        .metric-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; }}
        .metric-val {{ font-size: 20px; font-weight: 800; color: #0284c7; }}
        .metric-lbl {{ font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 12px; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }}
        th {{ background: #f1f5f9; font-weight: 700; }}
        .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 800; text-transform: uppercase; }}
        .critical {{ background: #ffe4e6; color: #e11d48; }}
        .high {{ background: #ffedd5; color: #ea580c; }}
        .medium {{ background: #fef9c3; color: #ca8a04; }}
        .low {{ background: #dcfce7; color: #16a34a; }}
        .footer {{ margin-top: 36px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="title">AeroMind ClimateGuard — Industrial HSE Incident & Audit Report</h1>
        <div class="subtitle">Generated on {now.strftime('%B %d, %Y at %H:%M:%S UTC')} | Classification: OFFICIAL AUDIT</div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-lbl">Total Incidents Recorded</div>
            <div class="metric-val">{len(alerts)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-lbl">Critical Severity Breaches</div>
            <div class="metric-val" style="color: #e11d48;">{critical_count}</div>
        </div>
        <div class="metric-card">
            <div class="metric-lbl">High Severity Hazards</div>
            <div class="metric-val" style="color: #ea580c;">{high_count}</div>
        </div>
        <div class="metric-card">
            <div class="metric-lbl">Monitored Sectors</div>
            <div class="metric-val">{len(locations)} ACTIVE</div>
        </div>
    </div>

    <h2 style="font-size: 16px; margin-top: 24px;">Incident Chronology & Operator Audit Log</h2>
    <table>
        <thead>
            <tr>
                <th>Timestamp (UTC)</th>
                <th>Incident Title</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Acknowledged By</th>
                <th>Operational Details</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="footer">
        AeroMind ClimateGuard Physical AI Operations Center — Deterministic Safety Compliance Engine — Abu Dhabi Industrial Facility
    </div>
</body>
</html>"""

    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"inline; filename=aeromind_hse_compliance_{now.strftime('%Y%m%d_%H%M%S')}.html"}
    )

