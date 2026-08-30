import os
import uuid
import threading
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from apps.backend.src.auth import get_current_user
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db, SessionLocal
from database.models import Camera, Location, VideoEvent, VideoJob
from database.schemas import VideoJobStatusResponse
from apps.ai_engine.video_analytics import VideoAnalyticsEngine
from apps.ai_engine.video_sources import FileVideoSource, RTSPVideoSource
from apps.backend.src.websocket_hub import ws_hub

logger = logging.getLogger("aeromind.routes.video")

router = APIRouter(prefix="/api/v1/video", tags=["Computer Vision & Video Analytics"], dependencies=[Depends(get_current_user)])

video_engine = VideoAnalyticsEngine()

SAMPLE_VIDEOS_DIR = "data/samples"
UPLOAD_VIDEOS_DIR = "data/raw/uploads"
os.makedirs(SAMPLE_VIDEOS_DIR, exist_ok=True)
os.makedirs(UPLOAD_VIDEOS_DIR, exist_ok=True)

def _sanitize_filename(filename: str) -> str:
    """Strip dangerous path characters to prevent directory traversal."""
    base = os.path.basename(filename)
    return "".join(c for c in base if c.isalnum() or c in "._-")

def _run_video_job_worker(job_id: str, video_path: str, camera_id: str, location_id: str, conf_threshold: float, iou_threshold: float, frame_skip: int, is_rtsp: bool = False):
    db: Session = SessionLocal()
    try:
        job = db.query(VideoJob).filter_by(id=job_id).first()
        if not job:
            return

        job.status = "PROCESSING"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        camera = db.query(Camera).filter_by(id=camera_id).first()
        danger_zones = camera.danger_zones if camera else []

        def on_progress(pct: float, current_frame: int, total_frames: int):
            # Update DB progress every 15%
            try:
                job.progress_pct = round(pct, 1)
                job.processed_frames = current_frame
                job.total_frames = total_frames
                db.commit()
            except Exception:
                pass

        # Select appropriate VideoSource
        source = RTSPVideoSource(video_path, camera_id=camera_id) if is_rtsp else FileVideoSource(video_path)

        results = video_engine.analyze_source(
            source=source,
            job_id=job_id,
            camera_id=camera_id,
            location_id=location_id,
            confidence_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            frame_skip=frame_skip,
            max_frames=150 if is_rtsp else None,
            danger_zones=danger_zones,
            progress_callback=on_progress
        )

        job.status = "COMPLETED"
        job.progress_pct = 100.0
        job.completed_at = datetime.now(timezone.utc)
        job.fps = results["effective_fps"]
        job.detections_count = results["total_detections"]
        job.events_count = results["total_events"]
        job.summary_report = results

        # Persist video events
        for ev in results["events"]:
            db.add(VideoEvent(
                id=ev["id"],
                camera_id=camera_id,
                location_id=location_id,
                timestamp=datetime.fromisoformat(ev["timestamp"]),
                event_type=ev["event_type"],
                confidence=ev["confidence"],
                severity=ev["severity"],
                description=ev["description"],
                snapshot_path=ev.get("snapshot_path"),
                video_job_id=job_id,
                metadata_json=ev.get("metadata", {})
            ))

        db.commit()

    except Exception as exc:
        logger.error(f"[VideoWorker] Job {job_id} failed: {exc}")
        try:
            job = db.query(VideoJob).filter_by(id=job_id).first()
            if job:
                job.status = "FAILED"
                job.error_message = str(exc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()

@router.get("/samples")
async def list_sample_videos():
    samples = []
    if os.path.exists(SAMPLE_VIDEOS_DIR):
        for f in os.listdir(SAMPLE_VIDEOS_DIR):
            if f.endswith((".mp4", ".avi", ".mov", ".mkv")):
                full_path = os.path.join(SAMPLE_VIDEOS_DIR, f)
                samples.append({
                    "filename": f,
                    "path": full_path,
                    "size_mb": round(os.path.getsize(full_path) / (1024 * 1024), 2)
                })
    return samples

@router.post("/analyze")
async def start_video_analysis(
    video_file: Optional[UploadFile] = File(None),
    sample_filename: Optional[str] = Form(None),
    rtsp_url: Optional[str] = Form(None),
    camera_id: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None),
    confidence_threshold: float = Form(0.45),
    iou_threshold: float = Form(0.45),
    frame_skip: int = Form(2),
    db: Session = Depends(get_db)
):
    if not camera_id:
        cam = db.query(Camera).first()
        if not cam:
            raise HTTPException(status_code=400, detail="No cameras registered in system.")
        camera_id = cam.id
        location_id = cam.location_id
    elif not location_id:
        cam = db.query(Camera).filter_by(id=camera_id).first()
        location_id = cam.location_id if cam else None

    job_id = str(uuid.uuid4())
    video_path = None
    is_rtsp = False

    if rtsp_url:
        is_rtsp = True
        video_path = rtsp_url
    elif video_file:
        safe_name = f"{job_id}_{_sanitize_filename(video_file.filename)}"
        video_path = os.path.join(UPLOAD_VIDEOS_DIR, safe_name)
        contents = await video_file.read()
        if len(contents) > 200 * 1024 * 1024:  # 200 MB limit
            raise HTTPException(status_code=413, detail="Uploaded video exceeds 200 MB maximum size.")
        with open(video_path, "wb") as f:
            f.write(contents)
    elif sample_filename:
        safe_sample = _sanitize_filename(sample_filename)
        candidate = os.path.join(SAMPLE_VIDEOS_DIR, safe_sample)
        if os.path.exists(candidate):
            video_path = candidate
        else:
            raise HTTPException(status_code=404, detail=f"Sample video '{sample_filename}' not found.")
    else:
        samples = [f for f in os.listdir(SAMPLE_VIDEOS_DIR) if f.endswith(".mp4")] if os.path.exists(SAMPLE_VIDEOS_DIR) else []
        if samples:
            video_path = os.path.join(SAMPLE_VIDEOS_DIR, samples[0])
        else:
            from scripts.generate_sample_video import generate_synthetic_video
            video_path = os.path.join(SAMPLE_VIDEOS_DIR, "demo_physical_hazards.mp4")
            generate_synthetic_video(video_path, duration_seconds=6, fps=24)

    # Persist job record in database
    db_job = VideoJob(
        id=job_id,
        video_path=video_path,
        camera_id=camera_id,
        location_id=location_id,
        status="QUEUED",
        progress_pct=0.0,
        total_frames=0,
        processed_frames=0,
        fps=0.0,
        detections_count=0,
        events_count=0
    )
    db.add(db_job)
    db.commit()

    # Launch background processing thread
    threading.Thread(
        target=_run_video_job_worker,
        args=(job_id, video_path, camera_id, location_id, confidence_threshold, iou_threshold, frame_skip, is_rtsp),
        daemon=True
    ).start()

    return {
        "job_id": job_id,
        "status": "QUEUED",
        "video_path": video_path,
        "message": "Video analysis job dispatched."
    }

@router.get("/jobs/{job_id}", response_model=VideoJobStatusResponse)
async def get_video_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(VideoJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Video analysis job not found.")
    return VideoJobStatusResponse(
        job_id=job.id,
        video_path=job.video_path,
        camera_id=job.camera_id,
        location_id=job.location_id,
        status=job.status,
        progress_pct=job.progress_pct,
        total_frames=job.total_frames,
        processed_frames=job.processed_frames,
        fps=job.fps,
        detections_count=job.detections_count,
        events_count=job.events_count,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        summary_report=job.summary_report
    )

from fastapi.responses import StreamingResponse
from services.video_stream_manager import stream_manager

@router.get("/stream/{camera_id}")
async def live_camera_mjpeg_stream(camera_id: str, db: Session = Depends(get_db)):
    """Provides a live Motion-JPEG video stream with real-time bounding box overlays."""
    cam = db.query(Camera).filter_by(id=camera_id).first()
    stream_url = cam.stream_url if cam else None
    danger_zones = cam.danger_zones if cam else []

    # Initialize / update worker with current DB danger zones
    stream_manager.get_or_create_stream(camera_id, stream_url=stream_url, danger_zones=danger_zones)

    return StreamingResponse(
        stream_manager.generate_mjpeg_stream(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/stream/{camera_id}/health")
async def get_live_stream_health(camera_id: str):
    return stream_manager.get_stream_health(camera_id)

@router.post("/cameras/{camera_id}/zones")
async def add_camera_danger_zone(
    camera_id: str,
    zone_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Add or update an interactive polygon safety zone on a camera."""
    cam = db.query(Camera).filter_by(id=camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found.")

    current_zones = list(cam.danger_zones or [])
    # Remove existing zone with same name if exists
    name = zone_data.get("name", "RESTRICTED_ZONE")
    current_zones = [z for z in current_zones if z.get("name") != name]
    current_zones.append(zone_data)

    cam.danger_zones = current_zones
    db.commit()

    # Update active stream worker
    stream_manager.get_or_create_stream(camera_id, stream_url=cam.stream_url, danger_zones=current_zones)

    return {"message": f"Danger zone '{name}' saved successfully.", "danger_zones": current_zones}

@router.delete("/cameras/{camera_id}/zones/{zone_name}")
async def delete_camera_danger_zone(
    camera_id: str,
    zone_name: str,
    db: Session = Depends(get_db)
):
    """Delete a custom safety zone from camera."""
    cam = db.query(Camera).filter_by(id=camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found.")

    current_zones = [z for z in (cam.danger_zones or []) if z.get("name") != zone_name]
    cam.danger_zones = current_zones
    db.commit()

    stream_manager.get_or_create_stream(camera_id, stream_url=cam.stream_url, danger_zones=current_zones)
    return {"message": f"Danger zone '{zone_name}' removed.", "danger_zones": current_zones}

