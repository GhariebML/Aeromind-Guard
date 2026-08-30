import {
  Location, TemperatureReading, RiskScore, Alert,
  AIDecision, RiskEvent, Camera, SystemStatus,
  ForecastPoint, VideoJobStatus
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('access_token');
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  const response = await fetch(url, { ...options, headers });
  
  if (response.status === 401 || response.status === 403) {
    // If we get an auth error, clear token and reload to force login screen
    if (token) {
      localStorage.removeItem('access_token');
      window.location.href = '/';
    }
    throw new Error('Authentication required or session expired');
  }
  
  return response;
}

export const api = {
  // System & Health
  async getSystemStatus(): Promise<SystemStatus> {
    const res = await fetchWithAuth(`${BASE_URL}/system/status`);
    if (!res.ok) throw new Error('Failed to fetch system status');
    return res.json();
  },

  async toggleDemoMode(): Promise<{ demo_mode_active: boolean }> {
    const res = await fetchWithAuth(`${BASE_URL}/system/demo-mode/toggle`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to toggle demo mode');
    return res.json();
  },

  // Locations & Telemetry
  async getLocations(): Promise<Location[]> {
    const res = await fetchWithAuth(`${BASE_URL}/locations`);
    if (!res.ok) throw new Error('Failed to fetch locations');
    return res.json();
  },

  async getCurrentTemperatures(): Promise<TemperatureReading[]> {
    const res = await fetchWithAuth(`${BASE_URL}/temperature/current`);
    if (!res.ok) throw new Error('Failed to fetch temperature readings');
    return res.json();
  },

  async getTemperatureHistory(locationId?: string, limit = 40): Promise<TemperatureReading[]> {
    const query = locationId ? `?location_id=${locationId}&limit=${limit}` : `?limit=${limit}`;
    const res = await fetchWithAuth(`${BASE_URL}/temperature/history${query}`);
    if (!res.ok) throw new Error('Failed to fetch temperature history');
    return res.json();
  },

  async getForecast(locationId?: string): Promise<{ location_id: string; location_name: string; series: ForecastPoint[] }> {
    const query = locationId ? `?location_id=${locationId}` : '';
    const res = await fetchWithAuth(`${BASE_URL}/forecast${query}`);
    if (!res.ok) throw new Error('Failed to fetch forecast');
    return res.json();
  },

  // Risk Scores & Intelligence
  async getCurrentRiskScores(): Promise<RiskScore[]> {
    const res = await fetchWithAuth(`${BASE_URL}/risk/current`);
    if (!res.ok) throw new Error('Failed to fetch risk scores');
    return res.json();
  },

  async getRiskHistory(locationId?: string, limit = 40): Promise<any[]> {
    const query = locationId ? `?location_id=${locationId}&limit=${limit}` : `?limit=${limit}`;
    const res = await fetchWithAuth(`${BASE_URL}/risk/history${query}`);
    if (!res.ok) throw new Error('Failed to fetch risk history');
    return res.json();
  },

  async getEvents(limit = 40): Promise<RiskEvent[]> {
    const res = await fetchWithAuth(`${BASE_URL}/events?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch risk events');
    return res.json();
  },

  async getDecisions(limit = 20): Promise<AIDecision[]> {
    const res = await fetchWithAuth(`${BASE_URL}/decisions?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch AI decisions');
    return res.json();
  },

  // Alerts Management
  async getAlerts(status?: string, severity?: string): Promise<Alert[]> {
    const params = new URLSearchParams();
    if (status && status !== 'ALL') params.append('status', status);
    if (severity && severity !== 'ALL') params.append('severity', severity);
    const res = await fetchWithAuth(`${BASE_URL}/alerts?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch alerts');
    return res.json();
  },

  async acknowledgeAlert(alertId: string, operatorName = 'Lead Operator'): Promise<void> {
    const res = await fetchWithAuth(`${BASE_URL}/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_name: operatorName })
    });
    if (!res.ok) throw new Error('Failed to acknowledge alert');
  },

  async resolveAlert(alertId: string, operatorName = 'Lead Operator'): Promise<void> {
    const res = await fetchWithAuth(`${BASE_URL}/alerts/${alertId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_name: operatorName })
    });
    if (!res.ok) throw new Error('Failed to resolve alert');
  },

  // Cameras & Video Analytics
  async getCameras(): Promise<Camera[]> {
    const res = await fetchWithAuth(`${BASE_URL}/cameras`);
    if (!res.ok) throw new Error('Failed to fetch cameras');
    return res.json();
  },

  async getSampleVideos(): Promise<Array<{ filename: string; path: string; size_mb: number }>> {
    const res = await fetchWithAuth(`${BASE_URL}/video/samples`);
    if (!res.ok) throw new Error('Failed to fetch sample videos');
    return res.json();
  },

  async startVideoAnalysis(formData: FormData): Promise<{ job_id: string; message: string }> {
    const res = await fetchWithAuth(`${BASE_URL}/video/analyze`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Failed to initiate video analysis');
    return res.json();
  },

  async getVideoJobStatus(jobId: string): Promise<VideoJobStatus> {
    const res = await fetchWithAuth(`${BASE_URL}/video/jobs/${jobId}`);
    if (!res.ok) throw new Error('Failed to fetch job status');
    return res.json();
  },

  async getVideoEvents(): Promise<any[]> {
    const res = await fetchWithAuth(`${BASE_URL}/video/events`);
    if (!res.ok) throw new Error('Failed to fetch video events');
    return res.json();
  },

  // AI Copilot
  async queryCopilot(query: string): Promise<{
    query: string;
    answer: string;
    grounded_data: any;
    sources_used: string[];
    is_llm_active: boolean;
    model_name: string;
  }> {
    const res = await fetchWithAuth(`${BASE_URL}/copilot/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    if (!res.ok) throw new Error('Failed to execute Copilot query');
    return res.json();
  },

  // Reports
  exportReportUrl(format: 'json' | 'csv' = 'json'): string {
    const token = localStorage.getItem('access_token');
    return `${BASE_URL}/reports/export?format=${format}&token=${token || ''}`;
  },

  getComplianceReportUrl(): string {
    const token = localStorage.getItem('access_token');
    return `${BASE_URL}/reports/compliance-report?token=${token || ''}`;
  },

  // Live Streaming & Safety Zones
  getLiveStreamUrl(cameraId: string): string {
    const token = localStorage.getItem('access_token');
    return `${BASE_URL}/video/stream/${cameraId}?token=${token || ''}`;
  },

  async getLiveStreamHealth(cameraId: string): Promise<{
    camera_id: string;
    status: string;
    fps: number;
    active_tracks: number;
    hazard_detected: boolean;
  }> {
    const res = await fetchWithAuth(`${BASE_URL}/video/stream/${cameraId}/health`);
    if (!res.ok) throw new Error('Failed to fetch stream health');
    return res.json();
  },

  async addDangerZone(cameraId: string, zoneData: any): Promise<any> {
    const res = await fetchWithAuth(`${BASE_URL}/video/cameras/${cameraId}/zones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(zoneData)
    });
    if (!res.ok) throw new Error('Failed to add danger zone');
    return res.json();
  },

  async deleteDangerZone(cameraId: string, zoneName: string): Promise<any> {
    const res = await fetchWithAuth(`${BASE_URL}/video/cameras/${cameraId}/zones/${encodeURIComponent(zoneName)}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Failed to delete danger zone');
    return res.json();
  }
};
