import React, { useState } from 'react';
import {
  ShieldAlert, Activity, Video, Map, Box,
  BarChart3, Bell, Bot, Cpu, Download, Play, Square, RefreshCw,
  Volume2, VolumeX, FileText
} from 'lucide-react';
import { SystemStatus } from '../types';
import { audioAlarms } from '../services/audioAlarms';

interface NavigationProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  systemStatus: SystemStatus | null;
  onToggleDemo: () => void;
  onRefresh: () => void;
  isDemoLoading: boolean;
}

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  setActiveTab,
  systemStatus,
  onToggleDemo,
  onRefresh,
  isDemoLoading
}) => {
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(audioAlarms.getMuted());

  const toggleMute = () => {
    const nextState = !isAudioMuted;
    audioAlarms.setMuted(nextState);
    setIsAudioMuted(nextState);
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'live-intelligence', label: 'Live Intel', icon: ShieldAlert },
    { id: 'video', label: 'Video AI', icon: Video },
    { id: 'map', label: 'Spatial Map', icon: Map },
    { id: 'digital-twin', label: 'Digital Twin 3D', icon: Box },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'alerts', label: 'Alerts', icon: Bell },
    { id: 'copilot', label: 'AI Copilot', icon: Bot },
    { id: 'system-health', label: 'System Health', icon: Cpu },
  ];

  const fgProvider = systemStatus?.providers.find(p => p.provider_name.includes('FortyGuard'));
  const fgStatus = fgProvider?.status || 'NOT_CONFIGURED';

  return (
    <div className="sticky top-4 z-50 px-4 mb-6">
      <header className="glass-premium rounded-2xl px-5 py-3 mx-auto max-w-7xl animate-float" style={{ animationDuration: '6s' }}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Brand & Status Indicators */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-[0_0_20px_rgba(34,211,238,0.3)] border border-cyan-400/30">
                <ShieldAlert className="w-6 h-6 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-lg tracking-wider text-gradient-cyan">
                    AEROMIND
                  </span>
                  <span className="text-xs font-bold text-slate-300 px-2 py-0.5 rounded bg-slate-800/80 border border-slate-600/60 shadow-inner">
                    CLIMEGUARD
                  </span>
              </div>
              <span className="text-[10px] text-slate-400 tracking-wider uppercase font-mono">
                PHYSICAL AI OPERATIONS CENTER
              </span>
            </div>
          </div>

          <div className="h-5 w-px bg-slate-800 hidden sm:block mx-1" />

          {/* Provider status chip */}
          <div className="flex items-center gap-1.5 text-xs font-mono px-2 py-1 rounded bg-slate-950/60 border border-slate-800">
            <span className="text-slate-400">FortyGuard:</span>
            <span className={`px-1.5 py-0.2 rounded font-bold text-[10px] ${
              fgStatus === 'CONNECTED'
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                : fgStatus === 'ERROR'
                ? 'bg-rose-950 text-rose-400 border border-rose-800'
                : 'bg-amber-950/60 text-amber-400 border border-amber-800/60'
            }`}>
              {fgStatus}
            </span>
          </div>

          {/* Live WS indicator */}
          <div className="flex items-center gap-1.5 text-xs font-mono px-2 py-1 rounded bg-slate-950/60 border border-slate-800">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
            </span>
            <span className="text-slate-300 font-mono text-[11px]">LIVE STREAM</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 overflow-x-auto no-scrollbar py-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Global Action Controls */}
        <div className="flex items-center gap-2">
          {/* Audio Alarm Mute Toggle */}
          <button
            onClick={toggleMute}
            className={`p-1.5 rounded border transition-colors ${
              isAudioMuted
                ? 'bg-slate-800 text-slate-500 border-slate-700 hover:bg-slate-700'
                : 'bg-rose-500/15 text-rose-400 border-rose-500/40 hover:bg-rose-500/25 shadow-sm shadow-rose-500/20'
            }`}
            title={isAudioMuted ? 'Acoustic Alarms Muted (Click to Enable)' : 'Acoustic Alarms Active (Click to Mute)'}
          >
            {isAudioMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
          </button>

          {/* Demo Mode Toggle */}
          <button
            onClick={onToggleDemo}
            disabled={isDemoLoading}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-mono font-medium border transition-colors ${
              systemStatus?.demo_mode_active
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
                : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-700'
            }`}
            title="Toggle deterministic synthetic telemetry stream"
          >
            {systemStatus?.demo_mode_active ? (
              <>
                <Square className="w-3 h-3 text-emerald-400" />
                <span>SIMULATOR ON</span>
              </>
            ) : (
              <>
                <Play className="w-3 h-3 text-slate-400" />
                <span>START DEMO</span>
              </>
            )}
          </button>

          {/* HSE Compliance Audit Report */}
          <a
            href="/api/v1/reports/compliance-report"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-medium bg-emerald-600/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-600/30 transition-colors"
            title="Download Official HSE / OSHA Compliance Audit Document"
          >
            <FileText className="w-3 h-3 text-emerald-400" />
            <span className="hidden sm:inline">HSE Report</span>
          </a>

          {/* Export JSON Report */}
          <a
            href="/api/v1/reports/export?format=json"
            target="_blank"
            rel="noreferrer"
            download
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-medium bg-cyan-600/20 text-cyan-300 border border-cyan-500/40 hover:bg-cyan-600/30 transition-colors"
          >
            <Download className="w-3 h-3 text-cyan-400" />
            <span className="hidden sm:inline">Export</span>
          </a>

          {/* Manual Refresh */}
          <button
            onClick={onRefresh}
            className="p-1.5 rounded bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700 border border-slate-700"
            title="Refresh active state"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
    </div>
  );
};
