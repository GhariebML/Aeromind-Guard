import React, { useState } from 'react';
import {
  Map, ShieldAlert, Video, Info
} from 'lucide-react';
import { Location, Camera } from '../types';

interface SpatialMapViewProps {
  locations: Location[];
  cameras: Camera[];
}

export const SpatialMapView: React.FC<SpatialMapViewProps> = ({ locations, cameras }) => {
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(locations[0] || null);

  const getRiskFill = (score: number) => {
    if (score >= 80) return 'rgba(244, 63, 94, 0.35)';
    if (score >= 60) return 'rgba(245, 158, 11, 0.30)';
    if (score >= 30) return 'rgba(234, 179, 8, 0.22)';
    return 'rgba(16, 185, 129, 0.18)';
  };

  const getRiskStroke = (score: number) => {
    if (score >= 80) return '#f43f5e';
    if (score >= 60) return '#f59e0b';
    if (score >= 30) return '#eab308';
    return '#10b981';
  };

  return (
    <div className="space-y-4">
      {/* Map Header */}
      <div className="glass-panel rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Map className="w-5 h-5 text-cyan-400" />
          <div>
            <h2 className="text-sm font-bold text-slate-200">
              SPATIAL FACILITY TOPOGRAPHY & THERMAL RISK ZONES
            </h2>
            <span className="text-[11px] text-slate-400">
              Multi-sensor spatial coordinates, camera frustums, and restricted hazard zones
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Nominal (&lt;30)</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-yellow-500" /> Moderate (30-59)</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Elevated (60-79)</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Critical (80+)</span>
        </div>
      </div>

      {/* Map Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* SVG Interactive Canvas (2 Cols) */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-4">
          <div className="relative aspect-[16/10] bg-slate-950 rounded-lg border border-slate-800 overflow-hidden">
            {/* Grid pattern */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:32px_32px] opacity-30" />

            <svg className="w-full h-full" viewBox="0 0 900 560">
              {/* Monitored Sector 1: BESS (Top-Left) */}
              <g
                className="cursor-pointer transition-transform hover:opacity-90"
                onClick={() => setSelectedLocation(locations[0] || null)}
              >
                <rect
                  x="60" y="60" width="340" height="200" rx="10"
                  fill={getRiskFill(locations[0]?.current_risk_score || 20)}
                  stroke={getRiskStroke(locations[0]?.current_risk_score || 20)}
                  strokeWidth="2"
                  strokeDasharray="4 2"
                />
                <text x="80" y="95" className="fill-slate-200 text-sm font-bold font-sans">
                  {locations[0]?.name || 'ZONE-BESS-01'}
                </text>
                <text x="80" y="115" className="fill-slate-400 text-xs font-mono">
                  Temp: {locations[0]?.current_temp_c?.toFixed(1) || 26.5}°C | Risk: {locations[0]?.current_risk_score?.toFixed(1) || 18.0}
                </text>
                {/* Danger Zone Sub-Perimeter */}
                <rect x="90" y="135" width="220" height="100" rx="6" fill="rgba(244,63,94,0.15)" stroke="#f43f5e" strokeWidth="1.5" />
                <text x="100" y="160" className="fill-rose-300 text-[11px] font-mono font-bold">
                  BESS LITHIUM RACK RESTRICTED
                </text>
              </g>

              {/* Monitored Sector 2: Solar Inverter Field (Top-Right) */}
              <g
                className="cursor-pointer transition-transform hover:opacity-90"
                onClick={() => setSelectedLocation(locations[1] || null)}
              >
                <rect
                  x="480" y="60" width="360" height="200" rx="10"
                  fill={getRiskFill(locations[1]?.current_risk_score || 22)}
                  stroke={getRiskStroke(locations[1]?.current_risk_score || 22)}
                  strokeWidth="2"
                />
                <text x="500" y="95" className="fill-slate-200 text-sm font-bold font-sans">
                  {locations[1]?.name || 'ZONE-SOLAR-04'}
                </text>
                <text x="500" y="115" className="fill-slate-400 text-xs font-mono">
                  Temp: {locations[1]?.current_temp_c?.toFixed(1) || 32.0}°C | Risk: {locations[1]?.current_risk_score?.toFixed(1) || 20.0}
                </text>
                {/* Inverter Arrays */}
                <circle cx="560" cy="180" r="28" fill="rgba(14,165,233,0.2)" stroke="#0ea5e9" strokeWidth="1.5" />
                <circle cx="660" cy="180" r="28" fill="rgba(14,165,233,0.2)" stroke="#0ea5e9" strokeWidth="1.5" />
                <circle cx="760" cy="180" r="28" fill="rgba(14,165,233,0.2)" stroke="#0ea5e9" strokeWidth="1.5" />
              </g>

              {/* Monitored Sector 3: Refining & Cracker Yard (Bottom-Left) */}
              <g
                className="cursor-pointer transition-transform hover:opacity-90"
                onClick={() => setSelectedLocation(locations[2] || null)}
              >
                <rect
                  x="60" y="300" width="340" height="200" rx="10"
                  fill={getRiskFill(locations[2]?.current_risk_score || 45)}
                  stroke={getRiskStroke(locations[2]?.current_risk_score || 45)}
                  strokeWidth="2"
                />
                <text x="80" y="335" className="fill-slate-200 text-sm font-bold font-sans">
                  {locations[2]?.name || 'ZONE-REFINERY-02'}
                </text>
                <text x="80" y="355" className="fill-slate-400 text-xs font-mono">
                  Temp: {locations[2]?.current_temp_c?.toFixed(1) || 34.0}°C | Risk: {locations[2]?.current_risk_score?.toFixed(1) || 35.0}
                </text>
                {/* Flange Flaring Perimeter */}
                <polygon points="120,380 280,380 320,470 80,470" fill="rgba(245,158,11,0.2)" stroke="#f59e0b" strokeWidth="1.5" />
                <text x="130" y="430" className="fill-amber-300 text-[11px] font-mono font-bold">
                  HIGH PRESSURE MANIFOLD
                </text>
              </g>

              {/* Monitored Sector 4: Rooftop Complex (Bottom-Right) */}
              <g
                className="cursor-pointer transition-transform hover:opacity-90"
                onClick={() => setSelectedLocation(locations[3] || null)}
              >
                <rect
                  x="480" y="300" width="360" height="200" rx="10"
                  fill={getRiskFill(locations[3]?.current_risk_score || 18)}
                  stroke={getRiskStroke(locations[3]?.current_risk_score || 18)}
                  strokeWidth="2"
                />
                <text x="500" y="335" className="fill-slate-200 text-sm font-bold font-sans">
                  {locations[3]?.name || 'ZONE-ROOFTOP-09'}
                </text>
                <text x="500" y="355" className="fill-slate-400 text-xs font-mono">
                  Temp: {locations[3]?.current_temp_c?.toFixed(1) || 28.0}°C | Risk: {locations[3]?.current_risk_score?.toFixed(1) || 16.0}
                </text>
                {/* Cooling Tower icons */}
                <rect x="520" y="380" width="90" height="80" rx="4" fill="rgba(6,182,212,0.2)" stroke="#06b6d4" />
                <rect x="630" y="380" width="90" height="80" rx="4" fill="rgba(6,182,212,0.2)" stroke="#06b6d4" />
                <rect x="740" y="380" width="80" height="80" rx="4" fill="rgba(6,182,212,0.2)" stroke="#06b6d4" />
              </g>

              {/* Optical Camera Cones / Frustums */}
              {/* Cam 1 in BESS */}
              <path d="M 60 60 L 160 140 L 220 70 Z" fill="rgba(14,165,233,0.25)" stroke="#0ea5e9" strokeWidth="1" />
              <circle cx="60" cy="60" r="7" fill="#0ea5e9" />

              {/* Cam 2 in Solar */}
              <path d="M 480 60 L 600 130 L 660 70 Z" fill="rgba(14,165,233,0.25)" stroke="#0ea5e9" strokeWidth="1" />
              <circle cx="480" cy="60" r="7" fill="#0ea5e9" />

              {/* Cam 3 in Refinery */}
              <path d="M 60 300 L 180 390 L 240 310 Z" fill="rgba(14,165,233,0.25)" stroke="#0ea5e9" strokeWidth="1" />
              <circle cx="60" cy="300" r="7" fill="#0ea5e9" />
            </svg>
          </div>
        </div>

        {/* Selected Sector Telemetry Inspector (1 Col) */}
        <div className="glass-panel rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h2 className="text-sm font-bold text-slate-200">
                SECTOR INSPECTOR
              </h2>
              <span className="text-xs font-mono text-cyan-400">
                {selectedLocation?.code || 'ZONE-BESS-01'}
              </span>
            </div>

            {selectedLocation ? (
              <div className="space-y-3 mt-3">
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase">Sector Name</span>
                  <h3 className="text-sm font-bold text-slate-100">{selectedLocation.name}</h3>
                </div>

                <div className="grid grid-cols-2 gap-2 bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                  <div>
                    <span className="text-[10px] text-slate-400 font-mono block">Latitude</span>
                    <span className="text-xs font-mono font-bold text-slate-200">{selectedLocation.latitude.toFixed(4)}° N</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-mono block">Longitude</span>
                    <span className="text-xs font-mono font-bold text-slate-200">{selectedLocation.longitude.toFixed(4)}° E</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-mono block">Elevation</span>
                    <span className="text-xs font-mono font-bold text-slate-200">{selectedLocation.elevation_m} meters</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-mono block">Threshold</span>
                    <span className="text-xs font-mono font-bold text-rose-400">{selectedLocation.risk_threshold} Score</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Current Ambient Temp:</span>
                    <strong className="text-slate-100 font-mono">{selectedLocation.current_temp_c?.toFixed(1) || 26.5}°C</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Baseline Temp:</span>
                    <strong className="text-slate-300 font-mono">{selectedLocation.baseline_temp_c.toFixed(1)}°C</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Composite Risk Score:</span>
                    <strong className="text-cyan-400 font-mono">{selectedLocation.current_risk_score.toFixed(1)} / 100</strong>
                  </div>
                </div>

                {/* Associated Cameras */}
                <div>
                  <span className="text-xs font-bold text-slate-300 block mb-1.5">
                    Assigned Optical Sensors & Cameras:
                  </span>
                  <div className="space-y-1.5">
                    {cameras.filter(c => c.location_id === selectedLocation.id).map(cam => (
                      <div key={cam.id} className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between text-xs font-mono">
                        <span className="flex items-center gap-1.5 text-slate-300">
                          <Video className="w-3.5 h-3.5 text-cyan-400" />
                          {cam.name}
                        </span>
                        <span className="text-emerald-400 font-bold text-[10px]">{cam.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-400 py-10 text-center">
                Select a facility zone on the map to inspect telemetry.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
