import React from 'react';
import {
  AlertTriangle, ShieldCheck, Flame, Users,
  CheckCircle2, ArrowUpRight, Clock
} from 'lucide-react';
import { Location, Alert, RiskScore, RiskEvent, AIDecision } from '../types';

interface OverviewViewProps {
  locations: Location[];
  alerts: Alert[];
  riskScores: RiskScore[];
  events: RiskEvent[];
  decisions: AIDecision[];
  onAcknowledgeAlert: (id: string) => void;
  onNavigateToTab: (tab: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  locations,
  alerts,
  riskScores,
  events,
  decisions,
  onAcknowledgeAlert,
  onNavigateToTab
}) => {
  // Compute platform composite risk
  const maxRisk = riskScores.length > 0
    ? Math.max(...riskScores.map(r => r.overall_score))
    : 18.0;

  const topRiskScore = riskScores.find(r => r.overall_score === maxRisk) || riskScores[0];
  const activeAlerts = alerts.filter(a => a.status === 'OPEN');
  const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL' && a.status === 'OPEN');

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

  const getRiskColor = (score: number) => {
    if (score >= 80) return 'text-rose-400';
    if (score >= 60) return 'text-amber-400';
    if (score >= 30) return 'text-yellow-400';
    return 'text-emerald-400';
  };

  return (
    <div className="space-y-4">
      {/* Top Banner Alert Bar (if critical alarms active) */}
      {criticalAlerts.length > 0 && (
        <div className="bg-gradient-to-r from-rose-950/90 via-slate-900 to-rose-950/90 border border-rose-500/50 rounded-xl p-3 flex items-center justify-between shadow-lg shadow-rose-950/40">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-rose-600/20 text-rose-400 border border-rose-500/40">
              <Flame className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <span className="text-xs font-bold font-mono uppercase text-rose-400 tracking-wider">
                CRITICAL THRESHOLD BREACH DETECTED ({criticalAlerts.length})
              </span>
              <p className="text-sm font-semibold text-slate-200">
                {criticalAlerts[0].title}: {criticalAlerts[0].message}
              </p>
            </div>
          </div>
          <button
            onClick={() => onAcknowledgeAlert(criticalAlerts[0].id)}
            className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md transition-colors"
          >
            Acknowledge
          </button>
        </div>
      )}

      {/* Top Row: System Risk Score & Operational Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Overall Risk Meter Card */}
        <div className="glass-premium hover-lift rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-slate-400 tracking-widest uppercase">
              COMPOSITE SYSTEM RISK
            </span>
            <span className={`px-2.5 py-1 rounded-md text-[11px] font-bold shadow-inner ${getSeverityBadge(topRiskScore?.severity || 'LOW')}`}>
              {topRiskScore?.severity || 'LOW'}
            </span>
          </div>

          <div className="my-4 flex items-baseline gap-2">
            <span className={`text-5xl font-extrabold font-mono tracking-tighter drop-shadow-md ${getRiskColor(maxRisk)}`}>
              {maxRisk.toFixed(1)}
            </span>
            <span className="text-slate-500 text-sm font-mono font-bold">/ 100</span>
          </div>

          <div className="space-y-2 mt-auto">
            <div className="w-full bg-slate-900/80 rounded-full h-2.5 shadow-inner overflow-hidden border border-slate-700/50">
              <div
                className={`h-full transition-all duration-1000 ease-out ${
                  maxRisk >= 80 ? 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.8)]' : maxRisk >= 60 ? 'bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.8)]' : maxRisk >= 30 ? 'bg-yellow-400 shadow-[0_0_10px_rgba(250,204,21,0.8)]' : 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)]'
                }`}
                style={{ width: `${Math.min(100, maxRisk)}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] font-mono font-bold text-slate-500">
              <span>0 (Nominal)</span>
              <span>100 (Critical)</span>
            </div>
          </div>
        </div>

        {/* Active Alerts Card */}
        <div className="glass-premium hover-lift rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-slate-400 tracking-widest uppercase">
              ACTIVE ALERTS
            </span>
            <AlertTriangle className={`w-5 h-5 drop-shadow-[0_0_8px_rgba(251,191,36,0.4)] ${activeAlerts.length > 0 ? 'text-amber-400' : 'text-slate-500'}`} />
          </div>
          <div className="my-4">
            <span className="text-4xl font-extrabold font-mono text-slate-100 drop-shadow-sm">
              {activeAlerts.length}
            </span>
            <span className="text-xs font-bold text-slate-500 ml-2 uppercase tracking-wider">unresolved</span>
          </div>
          <button
            onClick={() => onNavigateToTab('alerts')}
            className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-bold tracking-wide transition-colors mt-auto"
          >
            Review all alerts <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Monitored Zones Card */}
        <div className="glass-premium hover-lift rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-slate-400 tracking-widest uppercase">
              MONITORED SECTORS
            </span>
            <ShieldCheck className="w-5 h-5 text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.4)]" />
          </div>
          <div className="my-4">
            <span className="text-4xl font-extrabold font-mono text-slate-100 drop-shadow-sm">
              {locations.length}
            </span>
          </div>
          <div className="text-[10px] text-emerald-400 flex items-center gap-1 font-mono mt-auto">
            <CheckCircle2 className="w-3.5 h-3.5" /> Sensors nominal
          </div>
        </div>

        {/* Autonomous AI Decisions Card */}
        <div className="glass-premium hover-lift rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-slate-400 tracking-widest uppercase">
              AI DECISIONS (24H)
            </span>
            <CheckCircle2 className="w-5 h-5 text-emerald-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
          </div>
          <div className="my-4">
            <span className="text-4xl font-extrabold font-mono text-slate-100 drop-shadow-sm">
              {decisions.length}
            </span>
            <span className="text-xs font-bold text-slate-500 ml-2 uppercase tracking-wider">actions generated</span>
          </div>
          <button
            onClick={() => onNavigateToTab('live-intelligence')}
            className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-bold tracking-wide transition-colors mt-auto"
          >
            View live decision feed <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Grid: Sector Intelligence & Active Alarms */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Monitored Sectors Detailed Grid (2 Cols) */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div>
              <h2 className="text-sm font-bold text-slate-200 tracking-wide">
                PHYSICAL FACILITY SECTORS & THERMAL TELEMETRY
              </h2>
              <span className="text-xs text-slate-400">
                Real-time edge telemetry, baseline divergence, and risk weighting
              </span>
            </div>
            <span className="text-xs font-mono text-slate-400">
              UTC Sync
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {locations.map((loc) => {
              const rScore = riskScores.find(r => r.location_id === loc.id)?.overall_score || loc.current_risk_score;
              const severity = rScore >= 80 ? 'CRITICAL' : rScore >= 60 ? 'HIGH' : rScore >= 30 ? 'MEDIUM' : 'LOW';

              return (
                <div
                  key={loc.id}
                  className="bg-slate-900/80 border border-slate-800 rounded-lg p-3.5 hover:border-slate-700 transition-all flex flex-col justify-between"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-mono text-cyan-400 font-bold tracking-wider">
                        {loc.code}
                      </span>
                      <h3 className="text-xs font-bold text-slate-200 line-clamp-1">
                        {loc.name}
                      </h3>
                    </div>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border ${getSeverityBadge(severity)}`}>
                      {severity}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 my-3 py-2 bg-slate-950/60 rounded-md px-2 border border-slate-800/60">
                    <div>
                      <span className="text-[10px] text-slate-400 block font-mono">Temp</span>
                      <span className="text-xs font-bold text-slate-100 font-mono">
                        {loc.current_temp_c ? `${loc.current_temp_c.toFixed(1)}°C` : `${loc.baseline_temp_c.toFixed(1)}°C`}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-mono">Baseline</span>
                      <span className="text-xs font-semibold text-slate-300 font-mono">
                        {loc.baseline_temp_c.toFixed(1)}°C
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-mono">Risk</span>
                      <span className={`text-xs font-bold font-mono ${getRiskColor(rScore)}`}>
                        {rScore.toFixed(1)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                    <span className="capitalize">{loc.zone_type.toLowerCase()} Sector</span>
                    <span className="font-mono text-[10px]">
                      {loc.metadata?.provider === 'DEMO' ? (
                        <span className="text-amber-400 font-bold px-1 py-0.5 bg-amber-900/40 rounded">DEMO DATA</span>
                      ) : loc.metadata?.provider === 'FORTYGUARD' ? (
                        <span className="text-emerald-400 font-bold px-1 py-0.5 bg-emerald-900/40 rounded">LIVE (FG)</span>
                      ) : (
                        <span className="text-slate-400">Lat: {loc.latitude.toFixed(3)}</span>
                      )}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Operational Ticker & Alarms (1 Col) */}
        <div className="glass-panel rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <h2 className="text-sm font-bold text-slate-200 tracking-wide">
                ACTIVE TRIAGE QUEUE
              </h2>
              <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-800/40">
                {activeAlerts.length} Open
              </span>
            </div>

            <div className="space-y-2 mt-3 max-h-[360px] overflow-y-auto pr-1">
              {activeAlerts.length === 0 ? (
                <div className="text-center py-10 text-slate-400 text-xs">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-60" />
                  No open alarms. All sectors within safety limits.
                </div>
              ) : (
                activeAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold font-mono border ${getSeverityBadge(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                        <Clock className="w-2.5 h-2.5" />
                        {new Date(alert.created_at).toLocaleTimeString()}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-slate-200 line-clamp-1">
                      {alert.title}
                    </h4>
                    <p className="text-[11px] text-slate-300 line-clamp-2 mt-0.5">
                      {alert.message}
                    </p>

                    <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-end">
                      <button
                        onClick={() => onAcknowledgeAlert(alert.id)}
                        className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-cyan-300 text-[10px] font-semibold border border-slate-700 transition-colors"
                      >
                        Acknowledge
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <button
            onClick={() => onNavigateToTab('alerts')}
            className="w-full py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition-colors text-center mt-2"
          >
            Open Complete Alerts Console
          </button>
        </div>
      </div>
    </div>
  );
};
