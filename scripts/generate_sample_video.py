import os
import cv2
import numpy as np

def generate_synthetic_video(output_path: str = "data/samples/demo_physical_hazards.mp4", duration_seconds: int = 6, fps: int = 24):
    """
    Generates a realistic synthetic test video representing an industrial facility:
    Simulates a facility background, personnel walking, progressive thermal/smoke haze,
    and a localized combustion flare.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = duration_seconds * fps

    for frame_idx in range(total_frames):
        # Industrial facility dark background with grid floor
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (35, 38, 42)  # Dark slate background

        # Floor grid lines
        for y in range(250, height, 40):
            cv2.line(frame, (0, y), (width, y), (55, 60, 68), 1)
        for x in range(0, width, 60):
            cv2.line(frame, (x, 250), (x, height), (55, 60, 68), 1)

        # Danger zone polygon border (BESS / High Voltage Zone)
        pts = np.array([[100, 100], [400, 100], [400, 350], [100, 350]], np.int32)
        cv2.polylines(frame, [pts], isClosed=True, color=(0, 140, 255), thickness=2)
        cv2.putText(frame, "RESTRICTED HAZARD SECTOR", (110, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1)

        # Draw machinery box
        cv2.rectangle(frame, (140, 160), (360, 320), (70, 75, 85), -1)
        cv2.putText(frame, "BATTERY RACK B-01", (150, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Moving person entering danger zone
        t_frac = frame_idx / total_frames
        person_x = int(60 + (t_frac * 320))
        person_y = int(280 + np.sin(frame_idx * 0.3) * 5)
        # Person torso & head
        cv2.circle(frame, (person_x, person_y - 30), 10, (180, 180, 190), -1)
        cv2.rectangle(frame, (person_x - 12, person_y - 20), (person_x + 12, person_y + 20), (60, 110, 190), -1)

        # In second half of video, introduce thermal smoke plume and fire flare
        if frame_idx > (total_frames // 3):
            # Smoke plume (gray diffuse circles)
            smoke_y = int(220 - (frame_idx * 1.2) % 150)
            smoke_x = 250 + int(np.sin(frame_idx * 0.2) * 20)
            cv2.circle(frame, (smoke_x, smoke_y), 35 + int(frame_idx * 0.2), (150, 150, 150), -1)
            cv2.circle(frame, (smoke_x + 20, smoke_y - 20), 45 + int(frame_idx * 0.2), (130, 130, 130), -1)

        if frame_idx > (total_frames // 2):
            # Fire flame (bright orange/yellow contours in HSV range)
            flare_pts = np.array([
                [230, 240],
                [270, 240],
                [280, 190 + int(np.sin(frame_idx * 0.8) * 15)],
                [250, 150 + int(np.sin(frame_idx * 1.2) * 20)],
                [220, 190 + int(np.cos(frame_idx * 0.9) * 15)]
            ], np.int32)
            cv2.fillPoly(frame, [flare_pts], color=(0, 200, 255))
            cv2.circle(frame, (250, 210), 18, (0, 255, 255), -1)

        # Add timestamp & camera header
        cv2.putText(frame, f"CAM-BESS-01 | FRAME: {frame_idx:04d} | FPS: {fps}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 120), 1)

        out.write(frame)

    out.release()
    print(f"[Synthetic Video] Successfully generated sample video at: {output_path}")

if __name__ == "__main__":
    generate_synthetic_video()
