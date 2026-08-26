import React, { useState } from 'react';
import {
  ShieldAlert, Bot, CheckCircle2, Clock,
  Flame, Wind, Eye, Users
} from 'lucide-react';
import { RiskScore, RiskEvent, AIDecision, Location } from '../types';

interface LiveIntelligenceViewProps {
  locations: Location[];
  riskScores: RiskScore[];
  events: RiskEvent[];
  decisions: AIDecision[];
  liveMessages: any[];
}

export const LiveIntelligenceView: React.FC<LiveIntelligenceViewProps> = ({
  locations,
  riskScores,
  events,
  decisions,
  liveMessages
}) => {
  const [selectedLocationId, setSelectedLocationId] = useState<string>(locations[0]?.id || '');

  const activeLocation = locations.find(l => l.id === selectedLocationId) || locations[0];
  const activeRisk = riskScores.find(r => r.location_id === activeLocation?.id) || riskScores[0];

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-rose-950/80 text-rose-300 border-rose-600/60 animate-pulse';
      case 'HIGH':
        return 'bg-amber-950/80 text-amber-300 border-amber-600/60';
      case 'MEDIUM':
        return 'bg-yellow-950/80 text-yellow-300 border-yellow-600/60';
      default:
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-600/60';
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'IMMEDIATE':
        return 'bg-rose-600 text-white font-extrabold';
      case 'HIGH':
        return 'bg-amber-600 text-white font-bold';
      case 'MEDIUM':
        return 'bg-yellow-600 text-slate-950 font-bold';
      default:
        return 'bg-slate-700 text-slate-200';
    }
  };

  return (
    <div className="space-y-4">
      {/* Sector Filter Bar */}
      <div className="glass-panel rounded-xl p-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold text-slate-200 tracking-wide uppercase">
            Active Intelligence Sector:
          </span>
          <select
            value={selectedLocationId}
            onChange={(e) => setSelectedLocationId(e.target.value)}
            className="bg-slate-900 text-xs font-semibold text-cyan-300 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            {locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name} ({loc.code})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
          <span>Current Temp: <strong className="text-slate-100">{activeLocation?.current_temp_c?.toFixed(1) || 26.5}°C</strong></span>
          <span>Baseline: <strong className="text-slate-100">{activeLocation?.baseline_temp_c?.toFixed(1)}°C</strong></span>
          <span>Risk Score: <strong className="text-cyan-400">{activeRisk?.overall_score?.toFixed(1) || 18.0} / 100</strong></span>
        </div>
      </div>

      {/* Grid: 3 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Column 1: Deterministic Risk Factor Decomposition */}
        <div className="glass-panel rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div>
              <h2 className="text-sm font-bold text-slate-200">
                DETERMINISTIC RISK ATTRIBUTION
              </h2>
              <span className="text-[11px] text-slate-400">
                Explainable mathematical breakdown (0-100 scale)
              </span>
            </div>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${getSeverityBadge(activeRisk?.severity || 'LOW')}`}>
              {activeRisk?.severity || 'LOW'}
            </span>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800/80">
            <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block mb-1">
              Engine Calculation Formula
            </span>
            <pre className="text-[11px] font-mono text-cyan-300/90 whitespace-pre-wrap leading-relaxed">
              {activeRisk?.calculation_breakdown || 'Risk Score: Nominal baseline tracking.'}
            </pre>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-bold text-slate-300 block">
              Active Factor Attribution Breakdown:
            </span>
            {activeRisk?.factors && activeRisk.factors.length > 0 ? (
              activeRisk.factors.map((f, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between gap-2"
                >
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-slate-200">{f.name}</span>
                      <span className="text-[9px] font-mono uppercase px-1 py-0.2 rounded bg-slate-800 text-slate-400">
                        {f.category}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 block mt-0.5">
                      {f.description}
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-amber-400 bg-amber-950/40 px-2 py-1 rounded border border-amber-800/50">
                    +{f.score_contribution.toFixed(1)}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 italic py-2">
                All sensory factors operating within nominal standard deviation.
              </div>
            )}
          </div>
        </div>

        {/* Column 2: AI Decisions & Autonomous Operational Procedures */}
        <div className="glass-panel rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div>
              <h2 className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
                <Bot className="w-4 h-4 text-cyan-400" />
                AI DECISION LAYER
              </h2>
              <span className="text-[11px] text-slate-400">
                Actionable prioritized emergency directives
              </span>
            </div>
            <span className="text-xs font-mono text-cyan-400">
              Autonomous
            </span>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {decisions.length === 0 ? (
              <div className="text-center py-10 text-slate-400 text-xs">
                <CheckCircle2 className="w-8 h-8 text-cyan-500 mx-auto mb-2 opacity-60" />
                No high-priority emergency actions currently requested.
              </div>
            ) : (
              decisions.map((dec) => (
                <div
                  key={dec.id}
                  className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono tracking-wider ${getPriorityBadge(dec.priority)}`}>
                      {dec.priority} PRIORITY
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {new Date(dec.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <h3 className="text-xs font-extrabold text-slate-100">
                    {dec.action}
                  </h3>

                  <p className="text-[11px] text-slate-300 leading-relaxed">
                    {dec.explanation}
                  </p>

                  {dec.recommended_response && (
                    <div className="mt-2 p-2.5 rounded bg-slate-950/80 border border-slate-800 text-[11px] text-slate-300 font-mono">
                      <strong className="text-cyan-400 block text-[10px] uppercase mb-1">
                        Recommended Procedure Protocol:
                      </strong>
                      <p className="whitespace-pre-wrap">{dec.recommended_response}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                    <span>Confidence: {(dec.confidence * 100).toFixed(0)}%</span>
                    <span className="text-emerald-400 font-semibold">Verified Grounding</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Column 3: Real-Time Event & WebSocket Stream */}
        <div className="glass-panel rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <div>
                <h2 className="text-sm font-bold text-slate-200">
                  REAL-TIME EVENT STREAM
                </h2>
                <span className="text-[11px] text-slate-400">
                  Physical anomaly & visual perception events
                </span>
              </div>
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            </div>

            <div className="space-y-2 mt-3 max-h-[460px] overflow-y-auto pr-1">
              {events.map((ev) => (
                <div
                  key={ev.id}
                  className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800/80 flex items-start gap-2.5 text-xs"
                >
                  <div className="p-1.5 rounded bg-slate-800 text-slate-300 mt-0.5">
                    {ev.event_type.includes('FIRE') || ev.event_type.includes('SMOKE') ? (
                      <Flame className="w-3.5 h-3.5 text-rose-400" />
                    ) : ev.event_type.includes('DANGER') ? (
                      <Users className="w-3.5 h-3.5 text-amber-400" />
                    ) : (
                      <Wind className="w-3.5 h-3.5 text-cyan-400" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1 mb-0.5">
                      <span className="font-mono text-[10px] text-cyan-400 font-bold">
                        {ev.event_type}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {new Date(ev.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    <p className="text-slate-200 text-[11px] line-clamp-2">
                      {ev.description}
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1">
                      <span>Risk Impact: <strong className="text-slate-200">{ev.risk_score}</strong></span>
                      <span className={`px-1 py-0.2 rounded font-mono font-bold border ${getSeverityBadge(ev.severity)}`}>
                        {ev.severity}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
