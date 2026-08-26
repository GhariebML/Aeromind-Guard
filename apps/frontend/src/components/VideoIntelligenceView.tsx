import React, { useState, useEffect, useRef } from 'react';
import {
  Video, Upload, Play, CheckCircle2, AlertTriangle,
  Flame, Users, RefreshCw, Layers, Plus, Trash2, ShieldCheck, ShieldAlert
} from 'lucide-react';
import { Camera, VideoJobStatus } from '../types';
import { api } from '../services/api';

interface VideoIntelligenceViewProps {
  cameras: Camera[];
}

export const VideoIntelligenceView: React.FC<VideoIntelligenceViewProps> = ({ cameras }) => {
  const [selectedCameraId, setSelectedCameraId] = useState<string>(cameras[0]?.id || '');
  const [sampleVideos, setSampleVideos] = useState<Array<{ filename: string; path: string; size_mb: number }>>([]);
  const [selectedSample, setSelectedSample] = useState<string>('demo_physical_hazards.mp4');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.45);
  const [iouThreshold, setIouThreshold] = useState<number>(0.45);
  const [frameSkip, setFrameSkip] = useState<number>(2);

  const [activeJob, setActiveJob] = useState<VideoJobStatus | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [videoEvents, setVideoEvents] = useState<any[]>([]);

  // Safety Zone Editor State
  const [isEditingZones, setIsEditingZones] = useState<boolean>(false);
  const [activeVertices, setActiveVertices] = useState<Array<[number, number]>>([]);
  const [newZoneName, setNewZoneName] = useState<string>('RESTRICTED_ZONE_1');
  const [newZoneSeverity, setNewZoneSeverity] = useState<string>('CRITICAL');
  const [isSavingZone, setIsSavingZone] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Load sample videos & events
  useEffect(() => {
    api.getSampleVideos().then(setSampleVideos).catch(console.error);
    api.getVideoEvents().then(setVideoEvents).catch(console.error);
  }, []);

  // Poll active video job
  useEffect(() => {
    if (!activeJob || activeJob.status === 'COMPLETED' || activeJob.status === 'FAILED') return;

    const interval = setInterval(async () => {
      try {
        const updated = await api.getVideoJobStatus(activeJob.job_id);
        setActiveJob(updated);
        if (updated.status === 'COMPLETED') {
          api.getVideoEvents().then(setVideoEvents).catch(console.error);
        }
      } catch (err) {
        console.error(err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [activeJob]);

  const selectedCam = cameras.find(c => c.id === selectedCameraId) || cameras[0];

  const handleStartAnalysis = async () => {
    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('camera_id', selectedCameraId);
      formData.append('confidence_threshold', confidenceThreshold.toString());
      formData.append('iou_threshold', iouThreshold.toString());
      formData.append('frame_skip', frameSkip.toString());

      if (uploadedFile) {
        formData.append('video_file', uploadedFile);
      } else {
        formData.append('sample_filename', selectedSample);
      }

      const res = await api.startVideoAnalysis(formData);
      setActiveJob({
        job_id: res.job_id,
        video_path: selectedSample,
        status: 'PROCESSING',
        progress_pct: 0.0,
        total_frames: 0,
        processed_frames: 0,
        fps: 0.0,
        detections_count: 0,
        events_count: 0
      });
    } catch (err: any) {
      alert(`Failed to start video analysis: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Canvas Click for Drawing Safety Zone Vertices
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isEditingZones || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.round(((e.clientX - rect.left) / rect.width) * 640);
    const y = Math.round(((e.clientY - rect.top) / rect.height) * 480);
    setActiveVertices(prev => [...prev, [x, y]]);
  };

  const handleSaveZone = async () => {
    if (activeVertices.length < 3) {
      alert('Please click at least 3 points to form a polygon perimeter.');
      return;
    }
    if (!selectedCam) return;

    setIsSavingZone(true);
    try {
      await api.addDangerZone(selectedCam.id, {
        name: newZoneName,
        severity: newZoneSeverity,
        polygon: activeVertices
      });
      // Refresh local camera zones
      selectedCam.danger_zones = [
        ...(selectedCam.danger_zones || []).filter(z => z.name !== newZoneName),
        { name: newZoneName, severity: newZoneSeverity, polygon: activeVertices }
      ];
      setActiveVertices([]);
      setIsEditingZones(false);
    } catch (err: any) {
      alert(`Failed to save zone: ${err.message}`);
    } finally {
      setIsSavingZone(false);
    }
  };

  const handleDeleteZone = async (zoneName: string) => {
    if (!selectedCam) return;
    try {
      await api.deleteDangerZone(selectedCam.id, zoneName);
      selectedCam.danger_zones = (selectedCam.danger_zones || []).filter(z => z.name !== zoneName);
      alert(`Zone '${zoneName}' deleted.`);
    } catch (err: any) {
      alert(`Failed to delete zone: ${err.message}`);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Header & Camera Selection */}
      <div className="glass-panel rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Video className="w-5 h-5 text-cyan-400" />
          <div>
            <h2 className="text-sm font-bold text-slate-200">
              PHYSICAL AI COMPUTER VISION & DANGER ZONE REASONING
            </h2>
            <span className="text-[11px] text-slate-400">
              Live Motion-JPEG Stream, Real-Time BoT-SORT Tracking, and Custom Perimeter Editor
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-300 font-medium">Select Feed:</label>
          <select
            value={selectedCameraId}
            onChange={(e) => {
              setSelectedCameraId(e.target.value);
              setActiveVertices([]);
            }}
            className="bg-slate-900 text-xs font-semibold text-cyan-300 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.camera_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Grid: Live Stream Overlay & Analysis Controller */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left 2 Cols: Live Video Stream & Zone Canvas Editor */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-slate-200 font-mono">
                {selectedCam?.name || 'Optical Feed'} ({selectedCam?.resolution || '1920x1080'})
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  setIsEditingZones(!isEditingZones);
                  setActiveVertices([]);
                }}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-mono font-medium border transition-colors ${
                  isEditingZones
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>{isEditingZones ? 'Cancel Zone Edit' : 'Edit Danger Zones'}</span>
              </button>

              <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                {selectedCam?.fps || 30} FPS | LIVE STREAM
              </span>
            </div>
          </div>

          {/* Live Video Viewport */}
          <div className="relative aspect-video bg-slate-950 rounded-lg border border-slate-800 overflow-hidden flex items-center justify-center">
            {/* Live Motion-JPEG Camera Stream */}
            {selectedCam && (
              <img
                src={api.getLiveStreamUrl(selectedCam.id)}
                alt="Live Camera Feed"
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            )}

            {/* Interactive Polygon Editor Canvas */}
            {isEditingZones && (
              <canvas
                ref={canvasRef}
                onClick={handleCanvasClick}
                width={640}
                height={480}
                className="absolute inset-0 w-full h-full cursor-crosshair z-20"
              />
            )}

            {/* Drawing Preview Overlay */}
            {isEditingZones && activeVertices.length > 0 && (
              <div className="absolute top-3 right-3 bg-slate-900/90 backdrop-blur-md p-2.5 rounded-lg border border-amber-500/40 text-xs font-mono text-amber-300 space-y-1 z-30">
                <div>CLICK TO ADD VERTICES ({activeVertices.length} points)</div>
                <div className="text-[10px] text-slate-400">
                  {activeVertices.map((v, i) => `P${i+1}:(${v[0]},${v[1]})`).join(' ')}
                </div>
              </div>
            )}
          </div>

          {/* Danger Zone Management Panel */}
          {isEditingZones ? (
            <div className="bg-slate-900/80 p-3 rounded-lg border border-amber-500/30 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2">
                <label className="font-semibold text-slate-300">Zone Label:</label>
                <input
                  type="text"
                  value={newZoneName}
                  onChange={(e) => setNewZoneName(e.target.value)}
                  className="bg-slate-950 text-slate-100 border border-slate-700 rounded px-2 py-1 text-xs"
                />
                <select
                  value={newZoneSeverity}
                  onChange={(e) => setNewZoneSeverity(e.target.value)}
                  className="bg-slate-950 text-slate-100 border border-slate-700 rounded px-2 py-1 text-xs"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveVertices([])}
                  className="px-2.5 py-1 rounded bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700"
                >
                  Clear Points
                </button>
                <button
                  onClick={handleSaveZone}
                  disabled={isSavingZone || activeVertices.length < 3}
                  className="px-3 py-1 rounded bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold disabled:opacity-50"
                >
                  {isSavingZone ? 'Saving...' : 'Save Zone Perimeter'}
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800 flex flex-wrap items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                <span className="text-slate-300">
                  CONFIGURED DANGER ZONES ({selectedCam?.danger_zones?.length || 0}):
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {(selectedCam?.danger_zones || []).map((z, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-950 border border-slate-700 text-slate-300 text-[11px]"
                  >
                    <span>{z.name} ({z.severity || 'HIGH'})</span>
                    <button
                      onClick={() => handleDeleteZone(z.name)}
                      className="text-slate-500 hover:text-rose-400 ml-1"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right 1 Col: Video Analysis Pipeline Job Controller */}
        <div className="glass-panel rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h2 className="text-sm font-bold text-slate-200">
                RUN OFFLINE AI ANALYSIS
              </h2>
              <span className="text-xs font-mono text-slate-400">
                MP4 Pipeline
              </span>
            </div>

            {/* Video File / Sample Selector */}
            <div className="space-y-3 mt-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Select Video Source:
                </label>
                <select
                  value={selectedSample}
                  onChange={(e) => {
                    setSelectedSample(e.target.value);
                    setUploadedFile(null);
                  }}
                  className="w-full bg-slate-900 text-xs font-mono text-slate-200 border border-slate-700 rounded-lg p-2 focus:outline-none focus:border-cyan-500"
                >
                  <option value="demo_physical_hazards.mp4">
                    Sample: demo_physical_hazards.mp4 (Industrial Facility)
                  </option>
                  {sampleVideos.filter(s => s.filename !== 'demo_physical_hazards.mp4').map(s => (
                    <option key={s.filename} value={s.filename}>
                      Sample: {s.filename} ({s.size_mb} MB)
                    </option>
                  ))}
                </select>
              </div>

              {/* Upload custom video */}
              <div>
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="video/mp4,video/avi,video/mov"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setUploadedFile(e.target.files[0]);
                      setSelectedSample(e.target.files[0].name);
                    }
                  }}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full py-2 px-3 rounded-lg border border-dashed border-slate-700 hover:border-cyan-500 bg-slate-900/50 hover:bg-slate-900 text-xs text-slate-300 flex items-center justify-center gap-2 transition-colors"
                >
                  <Upload className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{uploadedFile ? `Uploaded: ${uploadedFile.name}` : 'Upload Custom MP4 Video...'}</span>
                </button>
              </div>

              {/* Threshold Sliders */}
              <div className="grid grid-cols-2 gap-2 font-mono text-xs pt-1">
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Conf:</span>
                    <span>{confidenceThreshold}</span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="0.9"
                    step="0.05"
                    value={confidenceThreshold}
                    onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                    className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                  />
                </div>
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Decimation:</span>
                    <span>{frameSkip}x</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="1"
                    value={frameSkip}
                    onChange={(e) => setFrameSkip(parseInt(e.target.value))}
                    className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Action Button & Active Progress */}
          <div className="space-y-3 pt-4 border-t border-slate-800">
            {activeJob && (
              <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 space-y-2 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">STATUS:</span>
                  <span className={`font-bold ${
                    activeJob.status === 'COMPLETED' ? 'text-emerald-400' :
                    activeJob.status === 'FAILED' ? 'text-rose-400' : 'text-amber-400'
                  }`}>
                    {activeJob.status} ({activeJob.progress_pct}%)
                  </span>
                </div>

                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full transition-all duration-300"
                    style={{ width: `${activeJob.progress_pct}%` }}
                  />
                </div>

                <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-300 pt-1">
                  <div>Frames: {activeJob.processed_frames}/{activeJob.total_frames}</div>
                  <div>FPS: {activeJob.fps}</div>
                  <div>Detections: {activeJob.detections_count}</div>
                  <div>Events: {activeJob.events_count}</div>
                </div>
              </div>
            )}

            <button
              onClick={handleStartAnalysis}
              disabled={isSubmitting || (activeJob?.status === 'PROCESSING')}
              className="w-full py-2.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 font-bold text-xs text-white shadow-lg shadow-cyan-500/20 disabled:opacity-50 flex items-center justify-center gap-2 transition-all"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Dispatching Inference Job...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Execute Video AI Pipeline</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
