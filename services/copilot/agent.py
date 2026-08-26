import os
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("aeromind.copilot")

class GroundedContext(BaseModel):
    locations_summary: List[Dict[str, Any]]
    active_alerts: List[Dict[str, Any]]
    highest_risk_scores: List[Dict[str, Any]]
    recent_anomalies: List[Dict[str, Any]]
    recent_video_events: List[Dict[str, Any]]

class AeroMindCopilot:
    """
    Physical AI Copilot.
    Grounded in exact database queries. Uses Ollama local LLM when available for natural language reasoning,
    and falls back to deterministic structured telemetry if Ollama is offline.
    """

    def __init__(self, ollama_url: Optional[str] = None, model_name: str = "llama3:latest"):
        self.ollama_url = (ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self.model_name = model_name

    async def check_ollama_status(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.ollama_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def query(
        self,
        user_query: str,
        grounded_data: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Executes grounded reasoning on structured real-time operational context.
        """
        now = datetime.now(timezone.utc)
        is_ollama_online = await self.check_ollama_status()

        # Build comprehensive grounded prompt
        system_prompt = (
            "You are AeroMind ClimateGuard Physical AI Copilot, an enterprise operations intelligence assistant.\n"
            "STRICT RULES:\n"
            "1. You MUST NEVER fabricate sensor values, risk scores, or location facts.\n"
            "2. Ground ALL answers strictly in the provided Operational System Context.\n"
            "3. If information is not in the context, explicitly state that live data is not available for that query.\n"
            "4. Provide crisp, high-urgency, professional responses for safety operators."
        )

        context_summary = f"""
OPERATIONAL SYSTEM CONTEXT:
- Current UTC Time: {now.isoformat()}
- Active Locations & Status: {grounded_data.get('locations', [])}
- Active Alerts ({len(grounded_data.get('alerts', []))} active): {grounded_data.get('alerts', [])}
- Highest Risk Locations: {grounded_data.get('risk_assessments', [])}
- Recent Anomalies: {grounded_data.get('anomalies', [])}
- Visual / Camera Hazards: {grounded_data.get('visual_hazards', [])}
- Latest AI Decisions: {grounded_data.get('decisions', [])}
"""

        sources_used = ["PostgreSQL/SQLite Operational Database", "Real-Time Risk Engine", "Visual Perception Feed"]

        if is_ollama_online:
            try:
                payload = {
                    "model": self.model_name,
                    "prompt": f"{system_prompt}\n\n{context_summary}\n\nUser Question: {user_query}\n\nAssistant Response:",
                    "stream": False,
                    "options": {"temperature": 0.2}
                }
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(f"{self.ollama_url}/api/generate", json=payload)
                    if resp.status_code == 200:
                        llm_text = resp.json().get("response", "").strip()
                        return {
                            "query": user_query,
                            "answer": llm_text,
                            "grounded_data": grounded_data,
                            "sources_used": sources_used + [f"Ollama ({self.model_name})"],
                            "is_llm_active": True,
                            "model_name": self.model_name,
                            "timestamp": now
                        }
            except Exception as e:
                logger.warning(f"[Copilot] Ollama call failed: {e}. Falling back to deterministic reasoning.")

        # Deterministic Grounded Reasoning Fallback
        q_lower = user_query.lower()
        alerts = grounded_data.get("alerts", [])
        risks = grounded_data.get("risk_assessments", [])
        anomalies = grounded_data.get("anomalies", [])
        hazards = grounded_data.get("visual_hazards", [])

        if "highest" in q_lower or "risk" in q_lower:
            if risks:
                top_risk = max(risks, key=lambda r: r.get("overall_score", 0))
                answer = (
                    f"**Highest Risk Location:** {top_risk.get('location_name', top_risk.get('location_id'))}\n"
                    f"- **Score:** {top_risk.get('overall_score')}/100 ({top_risk.get('severity')})\n"
                    f"- **Primary Action:** {top_risk.get('recommended_action', 'Inspect perimeter')}\n"
                    f"- **Breakdown:**\n{top_risk.get('calculation_breakdown', 'Nominal')}"
                )
            else:
                answer = "No elevated risk conditions are currently detected across monitored sectors."
        elif "alert" in q_lower or "attention" in q_lower or "active" in q_lower:
            if alerts:
                items = [f"- **[{a.get('severity')}]** {a.get('title')}: {a.get('message')} (Status: {a.get('status')})" for a in alerts[:5]]
                answer = f"**Currently Active Alerts ({len(alerts)}):**\n" + "\n".join(items)
            else:
                answer = "There are currently 0 active unresolved alerts in the system."
        elif "anomal" in q_lower or "temperature" in q_lower:
            if anomalies:
                items = [f"- **{a.get('metric')}** at {a.get('location_id')}: Value {a.get('value')} (Z-Score: {a.get('z_score')}, Score: {a.get('anomaly_score')}) — {a.get('reason')}" for a in anomalies[:4]]
                answer = f"**Recorded Environmental Anomalies:**\n" + "\n".join(items)
            else:
                answer = "All thermal and environmental readings are operating within normal baseline standard deviations."
        elif "hazard" in q_lower or "smoke" in q_lower or "fire" in q_lower or "camera" in q_lower:
            if hazards:
                items = [f"- **{h.get('type')}** (Confidence: {h.get('confidence')*100:.0f}%): {h.get('description', '')}" for h in hazards[:4]]
                answer = f"**Active Computer Vision Hazards:**\n" + "\n".join(items)
            else:
                answer = "Optical and thermal cameras report zero active visual hazards (no smoke, fire, or boundary breach)."
        else:
            answer = (
                f"**AeroMind Operations Overview:**\n"
                f"- **Active Alerts:** {len(alerts)}\n"
                f"- **Active Anomalies:** {len(anomalies)}\n"
                f"- **Visual Hazards:** {len(hazards)}\n"
                f"- **Top Monitored Risk:** {risks[0].get('overall_score', 0) if risks else 0}/100\n\n"
                f"*(Note: Ollama local LLM is currently offline at `{self.ollama_url}`. Presenting verified deterministic telemetry grounding).* "
            )

        return {
            "query": user_query,
            "answer": answer,
            "grounded_data": grounded_data,
            "sources_used": sources_used,
            "is_llm_active": False,
            "model_name": "Deterministic-Grounding-Engine (Ollama Offline)",
            "timestamp": now
        }
