import React, { useState, useEffect, useCallback } from 'react';
import { Navigation } from './components/Navigation';
import { OverviewView } from './components/OverviewView';
import { LiveIntelligenceView } from './components/LiveIntelligenceView';
import { VideoIntelligenceView } from './components/VideoIntelligenceView';
import { SpatialMapView } from './components/SpatialMapView';
import { DigitalTwinView } from './components/DigitalTwinView';
import { AnalyticsView } from './components/AnalyticsView';
import { AlertsView } from './components/AlertsView';
import { CopilotView } from './components/CopilotView';
import { SystemHealthView } from './components/SystemHealthView';

import {
  Location, Alert, RiskScore, RiskEvent, AIDecision, Camera, SystemStatus
} from './types';
import { api } from './services/api';
import { audioAlarms } from './services/audioAlarms';
import { useAuth } from './services/authContext';
import { LoginView } from './components/LoginView';

export const App: React.FC = () => {
  const { isAuthenticated, loading, token, logout, user } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('overview');

  // Operational State
  const [locations, setLocations] = useState<Location[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [riskScores, setRiskScores] = useState<RiskScore[]>([]);
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [decisions, setDecisions] = useState<AIDecision[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  const [liveMessages, setLiveMessages] = useState<any[]>([]);
  const [isDemoLoading, setIsDemoLoading] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Fetch all state
  const refreshAllState = useCallback(async () => {
    try {
      const [locs, alts, risks, evts, decs, cams, sys] = await Promise.all([
        api.getLocations(),
        api.getAlerts(),
        api.getCurrentRiskScores(),
        api.getEvents(),
        api.getDecisions(),
        api.getCameras(),
        api.getSystemStatus()
      ]);

      setLocations(locs);
      setAlerts(alts);
      setRiskScores(risks);
      setEvents(evts);
      setDecisions(decs);
      setCameras(cams);
      setSystemStatus(sys);
    } catch (err) {
      console.error('Failed to load system state:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated || !token) return;

    refreshAllState();

    // WebSocket Live Updates Connection with Standard Event Taxonomy & Heartbeat
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws?token=${token}`;
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;
    let heartbeatInterval: any = null;

    const connectWebSocket = () => {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[WebSocket] Connected to AeroMind operations event bus.');
        // Start 15s heartbeat
        heartbeatInterval = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ event_type: 'ping', timestamp: new Date().toISOString() }));
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        try {
          const envelope = JSON.parse(event.data);
          const evType = envelope.event_type || envelope.type;
          const data = envelope.data || envelope.payload;

          if (evType === 'telemetry.updated' || evType === 'temperature.updated' || evType === 'TELEMETRY_UPDATE') {
            setLiveMessages((prev) => [data, ...prev.slice(0, 30)]);
            if (data?.location_id) {
              setLocations((prev) =>
                prev.map((loc) =>
                  loc.id === data.location_id
                    ? {
                        ...loc,
                        current_temp_c: data.ambient_temp_c ?? loc.current_temp_c,
                        current_risk_score: data.risk_score ?? loc.current_risk_score,
                        current_severity: data.severity ?? loc.current_severity,
                        metadata: {
                          ...loc.metadata,
                          provider: data.provider ?? loc.metadata?.provider
                        }
                      }
                    : loc
                )
              );
            }
          } else if (evType === 'risk.updated') {
            if (data?.location_id) {
              setRiskScores((prev) =>
                prev.map((r) =>
                  r.location_id === data.location_id
                    ? { ...r, overall_score: data.risk_score, severity: data.severity }
                    : r
                )
              );
            }
          } else if (evType === 'alert.created' || evType === 'alert.updated' || evType === 'ALERT_CREATED') {
            if (data?.severity === 'CRITICAL') {
              audioAlarms.playCriticalAlarm();
            } else {
              audioAlarms.playWarningChime();
            }
            api.getAlerts().then(setAlerts).catch(console.error);
            api.getEvents().then(setEvents).catch(console.error);
            api.getDecisions().then(setDecisions).catch(console.error);
          }
        } catch (e) {
          // ignore non-json
        }
      };

      ws.onclose = (event) => {
        clearInterval(heartbeatInterval);
        if (event.code === 1008) {
          console.error('[WebSocket] Authentication failure (1008). Logging out.');
          logout();
          return;
        }
        console.warn('[WebSocket] Disconnected. Reconnecting in 3s...');
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (err) => {
        console.error('[WebSocket] Error:', err);
        ws?.close();
      };
    };

    connectWebSocket();

    return () => {
      clearInterval(heartbeatInterval);
      clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, [refreshAllState, isAuthenticated, token, logout]);

  if (loading) {
    return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-cyan-500 font-mono text-sm animate-pulse">INITIALIZING SECURITY MODULE...</div>;
  }

  if (!isAuthenticated) {
    return <LoginView />;
  }

  const handleToggleDemo = async () => {
    setIsDemoLoading(true);
    try {
      const res = await api.toggleDemoMode();
      setSystemStatus((prev) => (prev ? { ...prev, demo_mode_active: res.demo_mode_active } : null));
    } catch (err: any) {
      alert(`Could not toggle demo: ${err.message}`);
    } finally {
      setIsDemoLoading(false);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string, operatorName = 'Lead Safety Officer') => {
    try {
      await api.acknowledgeAlert(alertId, operatorName);
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId
            ? { ...a, status: 'ACKNOWLEDGED', acknowledged_by: operatorName, acknowledged_at: new Date().toISOString() }
            : a
        )
      );
    } catch (err: any) {
      alert(`Failed to acknowledge alert: ${err.message}`);
    }
  };

  const handleResolveAlert = async (alertId: string, operatorName = 'Lead Safety Officer') => {
    try {
      await api.resolveAlert(alertId, operatorName);
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId
            ? { ...a, status: 'RESOLVED', resolved_by: operatorName, resolved_at: new Date().toISOString() }
            : a
        )
      );
    } catch (err: any) {
      alert(`Failed to resolve alert: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Operations Center Navigation Header */}
      <Navigation
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemStatus={systemStatus}
        onToggleDemo={handleToggleDemo}
        onRefresh={refreshAllState}
        isDemoLoading={isDemoLoading}
      />

      {/* Main View Area */}
      <main className="flex-1 p-4 max-w-7xl w-full mx-auto">
        {isLoading ? (
          <div className="py-24 text-center text-slate-400 text-xs">
            Connecting to AeroMind Physical AI Operations Bus...
          </div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <OverviewView
                locations={locations}
                alerts={alerts}
                riskScores={riskScores}
                events={events}
                decisions={decisions}
                onAcknowledgeAlert={handleAcknowledgeAlert}
                onNavigateToTab={setActiveTab}
              />
            )}

            {activeTab === 'live-intelligence' && user?.role !== 'analyst' && (
              <LiveIntelligenceView
                locations={locations}
                riskScores={riskScores}
                events={events}
                decisions={decisions}
                liveMessages={liveMessages}
              />
            )}

            {activeTab === 'video' && user?.role !== 'analyst' && (
              <VideoIntelligenceView cameras={cameras} />
            )}

            {activeTab === 'map' && user?.role !== 'analyst' && (
              <SpatialMapView locations={locations} cameras={cameras} />
            )}

            {activeTab === 'digital-twin' && user?.role !== 'analyst' && (
              <DigitalTwinView locations={locations} riskScores={riskScores} />
            )}

            {activeTab === 'analytics' && user?.role !== 'operator' && (
              <AnalyticsView locations={locations} />
            )}

            {activeTab === 'alerts' && (
              <AlertsView
                alerts={alerts}
                onAcknowledgeAlert={handleAcknowledgeAlert}
                onResolveAlert={handleResolveAlert}
              />
            )}

            {activeTab === 'copilot' && (
              <CopilotView />
            )}

            {activeTab === 'system-health' && user?.role === 'admin' && (
              <SystemHealthView systemStatus={systemStatus} />
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default App;
