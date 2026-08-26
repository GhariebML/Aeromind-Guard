import React from 'react';
import {
  Cpu, Server, Activity, ShieldCheck, Database,
  Wifi, HardDrive, Zap, CheckCircle2, AlertTriangle, XCircle
} from 'lucide-react';
import { SystemStatus } from '../types';

interface SystemHealthViewProps {
  systemStatus: SystemStatus | null;
}

export const SystemHealthView: React.FC<SystemHealthViewProps> = ({ systemStatus }) => {
  if (!systemStatus) {
    return (
      <div className="glass-panel rounded-xl p-8 text-center text-slate-400 text-xs">
        Loading system telemetry...
      </div>
    );
  }

  const hw = systemStatus.hardware;
  const fgProvider = systemStatus.providers.find(p => p.provider_name.includes('FortyGuard'));

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'CONNECTED':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'ERROR':
        return <XCircle className="w-4 h-4 text-rose-400" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="glass-premium rounded-2xl p-5 flex flex-wrap items-center justify-between gap-4 animate-float" style={{ animationDuration: '8s' }}>
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-cyan-950 border border-cyan-800 shadow-[0_0_15px_rgba(34,211,238,0.15)]">
            <Cpu className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 tracking-wide text-gradient-cyan">
              SYSTEM HEALTH & HARDWARE TELEMETRY
            </h2>
            <span className="text-xs text-slate-400 font-mono mt-1 block">
              Live CPU, GPU, CUDA, Memory, API Provider connectivity and streaming throughput
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="px-3 py-1.5 rounded-lg bg-emerald-950 text-emerald-400 border border-emerald-800/80 font-bold shadow-[0_0_10px_rgba(16,185,129,0.2)]">
            SYSTEM STATUS: {systemStatus.status}
          </span>
          <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 font-bold shadow-inner">
            UPTIME: {Math.floor(systemStatus.uptime_seconds / 60)}m {Math.floor(systemStatus.uptime_seconds % 60)}s
          </span>
        </div>
      </div>

      {/* Grid: 3 Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* Hardware: CPU & Memory */}
        <div className="glass-premium hover-lift rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-extrabold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <Server className="w-5 h-5 text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.5)]" />
              HOST CPU & MEMORY
            </h3>
            <span className="text-[10px] font-mono text-slate-400 font-bold px-2 py-0.5 bg-slate-900 rounded border border-slate-700">{hw.platform}</span>
          </div>

          <div className="space-y-4 pt-2">
            <div>
              <div className="flex justify-between text-xs font-bold text-slate-300 mb-2">
                <span>CPU: {hw.cpu_model} ({hw.cpu_cores} Cores)</span>
                <span className="font-mono text-cyan-400 drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]">{hw.cpu_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-900/80 rounded-full h-2 shadow-inner border border-slate-700/50 overflow-hidden">
                <div className="bg-gradient-to-r from-cyan-600 to-cyan-400 h-full transition-all duration-1000 ease-out shadow-[0_0_8px_rgba(34,211,238,0.8)]" style={{ width: `${hw.cpu_percent}%` }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-bold text-slate-300 mb-2">
                <span>System RAM: {hw.ram_used_gb} GB / {hw.ram_total_gb} GB</span>
                <span className="font-mono text-cyan-400 drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]">{hw.ram_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-900/80 rounded-full h-2 shadow-inner border border-slate-700/50 overflow-hidden">
                <div className="bg-gradient-to-r from-blue-600 to-blue-400 h-full transition-all duration-1000 ease-out shadow-[0_0_8px_rgba(59,130,246,0.8)]" style={{ width: `${hw.ram_percent}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Hardware: GPU & AI Accelerator */}
        <div className="glass-premium hover-lift rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-extrabold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <Zap className="w-5 h-5 text-indigo-400 drop-shadow-[0_0_8px_rgba(129,140,248,0.5)]" />
              ACCELERATOR & INFERENCE
            </h3>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold shadow-inner ${
              hw.cuda_available ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-slate-800 text-slate-400'
            }`}>
              {hw.cuda_available ? 'CUDA ACTIVE' : 'CPU INFERENCE'}
            </span>
          </div>

          <div className="space-y-3 text-xs font-mono font-bold pt-2">
            <div className="flex justify-between items-center bg-slate-900/50 p-2 rounded-lg border border-slate-800/50">
              <span className="text-slate-400">Accelerator Device:</span>
              <strong className="text-slate-100">{hw.gpu_name}</strong>
            </div>
            <div className="flex justify-between items-center bg-slate-900/50 p-2 rounded-lg border border-slate-800/50">
              <span className="text-slate-400">CUDA Version:</span>
              <strong className="text-slate-100">{hw.cuda_version}</strong>
            </div>
            <div className="flex justify-between items-center bg-slate-900/50 p-2 rounded-lg border border-slate-800/50">
              <span className="text-slate-400">Inference Pipeline:</span>
              <strong className="text-indigo-400 drop-shadow-[0_0_5px_rgba(129,140,248,0.5)]">{systemStatus.inference_fps} FPS</strong>
            </div>
            <div className="flex justify-between items-center bg-slate-900/50 p-2 rounded-lg border border-slate-800/50">
              <span className="text-slate-400">Active Camera Feeds:</span>
              <strong className="text-slate-100">{systemStatus.active_camera_streams} Streams</strong>
            </div>
          </div>
        </div>

        {/* Ingestion Providers Connectivity */}
        <div className="glass-premium hover-lift rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-extrabold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <Wifi className="w-5 h-5 text-fuchsia-400 drop-shadow-[0_0_8px_rgba(232,121,249,0.5)]" />
              DATA PROVIDER GATEWAYS
            </h3>
            <span className="text-[10px] font-mono text-fuchsia-400 font-bold px-2 py-0.5 bg-fuchsia-950/30 rounded border border-fuchsia-900/50">
              {systemStatus.providers.length} Registered
            </span>
          </div>

          <div className="space-y-3 pt-2">
            {systemStatus.providers.map((p, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-900/60 border border-slate-700/60 space-y-1.5 shadow-inner transition-colors hover:bg-slate-800/60">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-extrabold text-slate-200 flex items-center gap-2 tracking-wide">
                    {getStatusIcon(p.status)}
                    {p.provider_name}
                  </span>
                  <span className="font-mono text-[10px] font-bold text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    {p.latency_ms ? `${p.latency_ms} ms` : 'N/A'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-1 font-medium pl-6">{p.message}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
