import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aeromind.alert.engine")

class AlertRecord(BaseModel):
    id: str
    location_id: str
    event_id: Optional[str] = None
    title: str
    message: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    status: str = "OPEN"  # OPEN, ACKNOWLEDGED, RESOLVED, REOPENED
    channels: List[str] = Field(default_factory=lambda: ["DASHBOARD", "WEBSOCKET"])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    reopened_at: Optional[datetime] = None
    reopened_by: Optional[str] = None
    audit_history: List[Dict[str, Any]] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

class AlertEngine:
    """
    Physical AI Alert Engine.
    Manages complete alarm lifecycle: OPEN -> ACKNOWLEDGED -> RESOLVED -> REOPENED
    Tracks structured audit log trails for safety compliance.
    """

    def __init__(self):
        self._active_alerts: Dict[str, AlertRecord] = {}

    def create_alert(
        self,
        location_id: str,
        title: str,
        message: str,
        severity: str,
        event_id: Optional[str] = None,
        channels: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertRecord:
        alert_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        record = AlertRecord(
            id=alert_id,
            location_id=location_id,
            event_id=event_id,
            title=title,
            message=message,
            severity=severity,
            status="OPEN",
            channels=channels or ["DASHBOARD", "WEBSOCKET"],
            created_at=now,
            audit_history=[
                {"action": "CREATED", "timestamp": now.isoformat(), "details": f"Alarm triggered with severity {severity}"}
            ],
            metadata_json=metadata or {}
        )
        self._active_alerts[alert_id] = record
        return record

    def acknowledge_alert(self, alert_id: str, operator_name: str = "Lead Safety Officer", note: Optional[str] = None) -> Optional[AlertRecord]:
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            now = datetime.now(timezone.utc)
            alert.status = "ACKNOWLEDGED"
            alert.acknowledged_at = now
            alert.acknowledged_by = operator_name
            alert.audit_history.append({
                "action": "ACKNOWLEDGED",
                "timestamp": now.isoformat(),
                "operator": operator_name,
                "note": note or "Operator acknowledged active hazard"
            })
            return alert
        return None

    def resolve_alert(self, alert_id: str, operator_name: str = "Lead Safety Officer", note: Optional[str] = None) -> Optional[AlertRecord]:
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            now = datetime.now(timezone.utc)
            alert.status = "RESOLVED"
            alert.resolved_at = now
            alert.resolved_by = operator_name
            alert.audit_history.append({
                "action": "RESOLVED",
                "timestamp": now.isoformat(),
                "operator": operator_name,
                "note": note or "Hazard condition mitigated"
            })
            return alert
        return None

    def reopen_alert(self, alert_id: str, operator_name: str = "Lead Safety Officer", reason: str = "Hazard recurring") -> Optional[AlertRecord]:
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            now = datetime.now(timezone.utc)
            alert.status = "REOPENED"
            alert.reopened_at = now
            alert.reopened_by = operator_name
            alert.audit_history.append({
                "action": "REOPENED",
                "timestamp": now.isoformat(),
                "operator": operator_name,
                "reason": reason
            })
            return alert
        return None
