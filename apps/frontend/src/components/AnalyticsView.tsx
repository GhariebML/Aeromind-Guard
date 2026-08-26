import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { BarChart3, TrendingUp, RefreshCw } from 'lucide-react';
import { Location, TemperatureReading, ForecastPoint } from '../types';
import { api } from '../services/api';

interface AnalyticsViewProps {
  locations: Location[];
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ locations }) => {
  const [selectedLocationId, setSelectedLocationId] = useState<string>(locations[0]?.id || '');
  const [tempHistory, setTempHistory] = useState<TemperatureReading[]>([]);
  const [forecastData, setForecastData] = useState<ForecastPoint[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!selectedLocationId) return;

    setIsLoading(true);
    Promise.all([
      api.getTemperatureHistory(selectedLocationId, 30),
      api.getForecast(selectedLocationId)
    ])
      .then(([history, forecast]) => {
        setTempHistory(history);
        setForecastData(forecast.series);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [selectedLocationId]);

  // Format historical chart data
  const chartHistory = tempHistory.map((item) => ({
    time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    ambient: item.ambient_temp_c,
    surface: item.surface_temp_c || item.ambient_temp_c + 3.0,
    rate_of_change: item.rate_of_change_c_per_hr,
    anomaly_score: (item.anomaly_score * 100).toFixed(0),
    is_anomaly: item.is_anomaly
  }));

  // Format forecast chart data
  const chartForecast = forecastData.map((f) => ({
    hour: `+${f.hour_offset}h`,
    predicted_temp: f.predicted_temp_c,
    temp_lower: f.confidence_interval_lower,
    temp_upper: f.confidence_interval_upper,
    predicted_risk: f.predicted_risk_score
  }));

  return (
    <div className="space-y-4">
      {/* Analytics Header & Sector Selector */}
      <div className="glass-panel rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-cyan-400" />
          <div>
            <h2 className="text-sm font-bold text-slate-200">
              HISTORICAL TELEMETRY, ANOMALY TRENDS & 24H FORECAST
            </h2>
            <span className="text-[11px] text-slate-400">
              Multi-variable statistical baseline correlation and rate-of-change projections
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-300 font-medium">Select Sector:</label>
          <select
            value={selectedLocationId}
            onChange={(e) => setSelectedLocationId(e.target.value)}
            className="bg-slate-900 text-xs font-semibold text-cyan-300 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            {locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Grid: 2 Large Chart Rows */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Chart 1: Ambient vs Surface vs Rate of Change */}
        <div className="glass-panel rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div>
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                Ambient vs Surface Temperature (°C)
              </h3>
              <span className="text-[10px] text-slate-400">
                Rolling historical trend points
              </span>
            </div>
            <span className="text-[10px] font-mono text-cyan-400">
              Live Recharts
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Line type="monotone" dataKey="ambient" name="Ambient Temp (°C)" stroke="#06b6d4" strokeWidth={2.5} dot={{ r: 2 }} />
                <Line type="monotone" dataKey="surface" name="Surface Temp (°C)" stroke="#f59e0b" strokeWidth={2} strokeDasharray="3 3" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Statistical Anomaly Score & Rate of Change */}
        <div className="glass-panel rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div>
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                Statistical Anomaly Score & Volatility
              </h3>
              <span className="text-[10px] text-slate-400">
                Z-Score probability and rate of change
              </span>
            </div>
            <span className="text-[10px] font-mono text-rose-400">
              Anomaly Detector
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Area type="monotone" dataKey="anomaly_score" name="Anomaly Score (%)" stroke="#f43f5e" fill="rgba(244, 63, 94, 0.2)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: 24-Hour Forecast & Confidence Intervals (Full width across 2 cols) */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              <div>
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  24-Hour Predictive Thermal Trajectory & Risk Projection
                </h3>
                <span className="text-[10px] text-slate-400">
                  FortyGuard / Physical extrapolation with ±1.5°C confidence bounds
                </span>
              </div>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
              Predictive Engine Active
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartForecast}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="hour" stroke="#64748b" fontSize={11} />
                <YAxis yAxisId="left" stroke="#64748b" fontSize={11} domain={['auto', 'auto']} />
                <YAxis yAxisId="right" orientation="right" stroke="#f43f5e" fontSize={11} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Line yAxisId="left" type="monotone" dataKey="predicted_temp" name="Predicted Temp (°C)" stroke="#38bdf8" strokeWidth={2.5} />
                <Line yAxisId="left" type="monotone" dataKey="temp_upper" name="Upper Bound (+1.5°C)" stroke="#94a3b8" strokeDasharray="2 2" />
                <Line yAxisId="left" type="monotone" dataKey="temp_lower" name="Lower Bound (-1.5°C)" stroke="#94a3b8" strokeDasharray="2 2" />
                <Line yAxisId="right" type="monotone" dataKey="predicted_risk" name="Predicted Risk Score" stroke="#f43f5e" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
