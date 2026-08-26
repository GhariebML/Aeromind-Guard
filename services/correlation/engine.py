import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from services.correlation.rules import CorrelationRule, DEFAULT_CORRELATION_RULES

logger = logging.getLogger("aeromind.correlation.engine")

class CorrelatedEvent(BaseModel):
    rule_id: str
    rule_name: str
    location_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    risk_boost: float
    severity: str
    action_directive: str
    matched_conditions: Dict[str, Any]
    description: str

class CorrelationEngine:
    """
    Multi-Modal Physical AI Correlation Engine.
    Correlates environmental sensor readings + thermal forecast + computer vision hazards.
    Includes time-windowed persistence, spatial cross-referencing, and duplicate suppression.
    """

    def __init__(
        self,
        rules: Optional[List[CorrelationRule]] = None,
        suppression_cooldown_seconds: float = 300.0  # 5 minute cooldown for identical rule/location
    ):
        self.rules = rules if rules is not None else list(DEFAULT_CORRELATION_RULES)
        self.suppression_cooldown_seconds = suppression_cooldown_seconds
        # In-memory deduplication cache: (location_id, rule_id) -> (last_triggered_timestamp, last_severity)
        self._trigger_cache: Dict[str, tuple] = {}

    def _get_cache_key(self, location_id: str, rule_id: str) -> str:
        return f"{location_id}:{rule_id}"

    def add_rule(self, rule: CorrelationRule):
        self.rules.append(rule)

    def evaluate(
        self,
        location_id: str,
        current_temp_c: float,
        anomaly_score: float,
        rate_of_change_c_per_hr: float,
        visual_event_types: List[str],
        people_in_danger_zone: int = 0,
        forecast_temp_c: Optional[float] = None,
        ignore_suppression: bool = False
    ) -> List[CorrelatedEvent]:
        matches: List[CorrelatedEvent] = []
        now = datetime.now(timezone.utc)
        now_ts = now.timestamp()

        for rule in self.rules:
            if not rule.is_active:
                continue

            matched = True
            reasons = {}

            # 1. Temperature condition
            if rule.min_temp_c is not None:
                if current_temp_c < rule.min_temp_c:
                    matched = False
                else:
                    reasons["temp"] = f"{current_temp_c:.1f}°C >= {rule.min_temp_c:.1f}°C"

            # 2. Anomaly score condition
            if matched and rule.min_anomaly_score is not None:
                if anomaly_score < rule.min_anomaly_score:
                    matched = False
                else:
                    reasons["anomaly"] = f"Score {anomaly_score:.2f} >= {rule.min_anomaly_score:.2f}"

            # 3. Rate of change condition
            if matched and rule.min_rate_of_change is not None:
                if rate_of_change_c_per_hr < rule.min_rate_of_change:
                    matched = False
                else:
                    reasons["rate_of_change"] = f"{rate_of_change_c_per_hr:.2f}°C/hr >= {rule.min_rate_of_change:.2f}°C/hr"

            # 4. Personnel in danger zone condition
            if matched and rule.min_people_in_danger_zone is not None:
                if people_in_danger_zone < rule.min_people_in_danger_zone:
                    matched = False
                else:
                    reasons["danger_zone_people"] = f"{people_in_danger_zone} personnel tracked in sector"

            # 5. Visual hazards confirmation condition
            if matched and rule.required_visual_events:
                missing_events = [ev for ev in rule.required_visual_events if ev not in visual_event_types]
                if missing_events:
                    matched = False
                else:
                    reasons["visual_events"] = rule.required_visual_events

            # 6. Duplicate Suppression & Cooldown Check
            if matched and reasons:
                severity = rule.severity_override or "HIGH"
                cache_key = self._get_cache_key(location_id, rule.rule_id)

                if not ignore_suppression and cache_key in self._trigger_cache:
                    last_ts, last_sev = self._trigger_cache[cache_key]
                    time_elapsed = now_ts - last_ts
                    # If within cooldown and severity has not escalated to CRITICAL, suppress duplicate alert
                    if time_elapsed < self.suppression_cooldown_seconds and (last_sev == "CRITICAL" or severity != "CRITICAL"):
                        logger.debug(f"[CorrelationEngine] Suppressed duplicate alert for {cache_key} ({time_elapsed:.1f}s < {self.suppression_cooldown_seconds}s)")
                        continue

                # Record trigger
                self._trigger_cache[cache_key] = (now_ts, severity)

                matches.append(CorrelatedEvent(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    location_id=location_id,
                    timestamp=now,
                    risk_boost=rule.risk_boost,
                    severity=severity,
                    action_directive=rule.action_directive,
                    matched_conditions=reasons,
                    description=f"{rule.description} [Matched: {', '.join(reasons.keys())}]"
                ))

        return matches
