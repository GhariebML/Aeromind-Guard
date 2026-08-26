import os
import time
import psutil
from apps.ai_engine.video_analytics import VideoAnalyticsEngine
from apps.ai_engine.video_sources import FileVideoSource

def run_real_video_validation():
    video_path = "data/samples/demo_physical_hazards.mp4"
    if not os.path.exists(video_path):
        from scripts.generate_sample_video import generate_synthetic_video
        generate_synthetic_video(video_path, duration_seconds=6, fps=24)

    engine = VideoAnalyticsEngine(snapshot_dir="data/processed/snapshots")
    source = FileVideoSource(video_path)

    process = psutil.Process()
    mem_before_mb = process.memory_info().rss / (1024 * 1024)

    t0 = time.perf_counter()
    danger_zones = [{"name": "Hazard Core", "polygon": [[100, 100], [500, 100], [500, 400], [100, 400]]}]

    results = engine.analyze_source(
        source=source,
        job_id="VAL-TEST-001",
        camera_id="CAM-BESS-01",
        location_id="LOC-BESS-01",
        confidence_threshold=0.35,
        frame_skip=1,
        danger_zones=danger_zones
    )

    t1 = time.perf_counter()
    mem_after_mb = process.memory_info().rss / (1024 * 1024)

    print("=== REAL VIDEO VALIDATION REPORT ===")
    print(f"Video File: {video_path}")
    print(f"Total Frames: {results['total_frames']}")
    print(f"Processed Frames: {results['processed_frames']}")
    print(f"Total Elapsed Time: {t1 - t0:.2f} s")
    print(f"Effective Processing FPS: {results['effective_fps']}")
    print(f"Native Source FPS: {results['native_fps']}")
    print(f"Total Detections Extracted: {results['total_detections']}")
    print(f"Total Unique Tracks: {results['total_tracks']}")
    print(f"Events Emitted: {results['total_events']}")
    print(f"Memory Baseline: {mem_before_mb:.1f} MB -> Peak: {mem_after_mb:.1f} MB (Delta: +{mem_after_mb - mem_before_mb:.1f} MB)")
    print("Events Detail:")
    for ev in results["events"]:
        print(f"  - [{ev['event_type']}] (Conf: {ev['confidence']:.2f}, Severity: {ev['severity']}) -> {ev['description']}")

if __name__ == "__main__":
    run_real_video_validation()
