import pytest
from services.alert_engine.engine import AlertEngine

def test_alert_lifecycle_complete_workflow():
    engine = AlertEngine()
    
    # 1. Create alert
    alert = engine.create_alert(
        location_id="ZONE-BESS-01",
        title="Thermal Hazard Alert",
        message="Critical rate of change exceeded",
        severity="CRITICAL"
    )
    assert alert.status == "OPEN"
    assert len(alert.audit_history) == 1
    assert alert.audit_history[0]["action"] == "CREATED"

    # 2. Acknowledge alert
    ack_alert = engine.acknowledge_alert(alert.id, operator_name="Officer Sarah", note="Inspecting thermal camera")
    assert ack_alert is not None
    assert ack_alert.status == "ACKNOWLEDGED"
    assert ack_alert.acknowledged_by == "Officer Sarah"
    assert len(ack_alert.audit_history) == 2
    assert ack_alert.audit_history[1]["action"] == "ACKNOWLEDGED"

    # 3. Resolve alert
    res_alert = engine.resolve_alert(alert.id, operator_name="Officer Sarah", note="Coolant manifold valve cycled")
    assert res_alert is not None
    assert res_alert.status == "RESOLVED"
    assert len(res_alert.audit_history) == 3
    assert res_alert.audit_history[2]["action"] == "RESOLVED"

    # 4. Reopen alert
    reopened = engine.reopen_alert(alert.id, operator_name="Supervisor Chen", reason="Temperature spiking again")
    assert reopened is not None
    assert reopened.status == "REOPENED"
    assert len(reopened.audit_history) == 4
