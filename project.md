```markdown
# BorderVision v2.0: Complete Technical Project Specification

---

## 1. Executive Summary

BorderVision is an AI-powered, single-camera video analytics system designed for intelligent monitoring of pedestrian movement across a user-defined boundary line. The system automatically detects persons and carried items, maintains frame-to-frame identity during a continuous visible session, logs crossing events with movement direction and bag counts, and performs long-term re-identification of individuals who return to the monitored area after an extended absence.

Unlike traditional pedestrian counters, BorderVision utilizes **Identity Fusion**. It combines multiple independent visual signals—appearance embedding, gait signature, physical measurements, and skeletal dynamics—through a dynamically weighted confidence-fusion engine. The system operates probabilistically, yielding a similarity score rather than a definitive identity claim, making it a powerful analytics tool where high-confidence matches serve as candidates for human review.

The system is built entirely on open-source Python 3 technologies, designed to be cross-platform (Windows, Linux, macOS), and fully supports both standard USB webcams and external IP cameras.

---

## 2. Problem Statement

Traditional pedestrian monitoring systems can count line crossings but fail to answer deeper operational questions. BorderVision bridges this gap by automatically answering:

- **Who crossed?** (Probabilistic identity linkage)
- **Did this person cross before, and when?** (Re-identification)
- **What did they carry entering versus exiting?** (Bag detection and counting)
- **What was the direction of travel?** (In/Out classification)
- **How long did the person remain away?** (Session timing)

By automating detection, tracking, event logging, and re-identification, BorderVision eliminates the need for manual CCTV review in environments like campus gates, building entrances, research facilities, and controlled checkpoints.

---

## 3. Hardware Requirements

### Minimum Hardware (Testing & Low-Traffic)

- **Camera:** 1080p, 30 FPS, global shutter preferred. Supports USB or IP (RTSP stream).
- **Processor:** AMD Ryzen 5 5600X or Intel i5-12600K.
- **RAM:** 16 GB DDR4.
- **Storage:** 512 GB NVMe SSD.
- **GPU:** NVIDIA RTX 3060 (12 GB VRAM). _Note: Minimum spec requires all models to be exported to TensorRT FP16 to achieve real-time 30 FPS processing._

### Recommended Hardware (Production Deployment)

- **Camera:** 4K, 30 FPS, Wide Dynamic Range (WDR). Supports USB or IP (RTSP stream).
- **Processor:** AMD Ryzen 7 7700X or Intel i7-13700K.
- **RAM:** 32 GB DDR5.
- **Storage:** 1 TB NVMe SSD (Active Data) + 4 TB HDD (Archive).
- **GPU:** NVIDIA RTX 4070 (12 GB VRAM) or RTX 4070 Ti.

### Camera Placement Guidelines

- **Height:** 3 to 5 meters above ground level.
- **Viewing Angle:** 45° to 90° horizontal angle relative to the primary walking direction. (Frontal 0° views severely degrade gait analysis).
- **Tilt (Depression Angle):** 15° to 35° below horizontal.
- **Environmental Exclusions:** Avoid backlit scenes, heavy shadows directly on the boundary line, and extreme top-down views (>50° depression).

---

## 4. Software Stack & System Architecture

The system utilizes an asynchronous, multi-threaded pipeline to ensure real-time performance without frame dropping.

- **Language:** Python 3.10+ (Strictly cross-platform).
- **Detection & Segmentation:** Ultralytics YOLOv8 (`yolov8x-det`, `yolov8x-seg`, `yolov8x-pose`).
- **Object Tracking:** BoT-SORT.
- **Appearance Re-Identification:** FastReID.
- **Gait Recognition:** OpenGait.
- **Face Recognition (Optional):** InsightFace.
- **Computer Vision:** OpenCV.
- **Databases:** MySQL 15+ (Relational), Qdrant (Vector).
- **Backend Framework:** FastAPI with Uvicorn and SQLAlchemy.
- **Frontend Framework:** React 18 + Vite.

### Interactive User Interface (Web Dashboard)

The system is controlled via a fully interactive, browser-based React dashboard powered by the FastAPI backend, utilizing WebSockets for real-time data streaming. The interface features a clean, minimalistic, modern aesthetic, utilizing glassmorphism and liquid glass effects to present complex analytics in a visually seamless and highly readable format.

**Dashboard Features:**

- **Live Monitoring:** Real-time, low-latency video feed with bounding box overlays, track IDs, and boundary lines.
- **Interactive Calibration UI:** Tools to manually draw the virtual boundary line directly on the video feed and input camera calibration parameters.
- **Real-Time Analytics Pane:** Clean metric cards displaying current occupancy, daily entry/exit counts, and bag statistics.
- **Event Explorer:** Searchable history log (by Person ID, Date, Direction, Match Confidence) with Excel/CSV export capabilities.
- **Profile Management:** View detailed individual identity profiles, complete with aggregated feature metrics and crossing history.

---

## 5. Core AI Pipelines

### A. Detection & Frame-to-Frame Tracking

- **Detection:** YOLOv8x runs on every frame to detect persons and carried items. The system natively supports three COCO classes: `backpack`, `handbag`, and `suitcase`. _(Note: 'Duffel bag' requires a custom fine-tuned model as it is not a standard COCO class)._
- **Tracking:** BoT-SORT is utilized for short-term tracking. It assigns and maintains a stable integer ID for a person while they remain continuously visible in the camera frame.
- **Crossing Detection:** The system uses the **foot position** (the bottom-center of the person's bounding box) mapped to the ground plane to determine crossing events. It employs temporal hysteresis (requiring a person to be established on the new side of the line for a specified number of consecutive frames) to prevent flickering or false triggers from people standing directly on the border.

### B. Asynchronous Feature Extraction

To maintain real-time performance, feature extraction is decoupled from the main detection loop and run asynchronously:

- **Appearance Embedding:** FastReID extracts a 2048-dimensional L2-normalized embedding from a bounding box crop. Extracted once per second per track, and once exactly at the crossing event.
- **Gait Signature:** Requires YOLOv8-seg to generate a binary silhouette of the person. OpenGait accumulates a sequence of 20–30 frames of continuous walking to output a 256-dimensional gait embedding.
- **Body Proportions:** YOLOv8-pose extracts 17 COCO skeletal keypoints. The system computes scale-invariant physical ratios (e.g., shoulder-to-hip ratio, torso-to-leg ratio).
- **Height Estimation:** Utilizes full camera intrinsic calibration (focal length, principal point) combined with manual physical measurements (camera height, tilt) and a ground-plane homography matrix to project pixel height into real-world centimeters.

---

## 6. Long-Term Re-Identification & Identity Fusion

When a person crosses the boundary, the system queries the Qdrant vector database to find existing identity profiles. It does not rely on a single feature or static weights.

- **Dynamic Quality-Weighted Fusion:** The fusion engine assigns weights to features based on the quality of the observation. For example, a 30-frame gait sequence is weighted much higher than a 5-frame sequence; a height estimate from a person far away (small bounding box) is weighted lower than one close to the camera.
- **Temporal Decay:** Because clothing and appearances change, the system applies an exponential decay function (e.g., a 30-day half-life) to the confidence scores of old embeddings.
- **Decision Thresholds:**
  - **Score >= 0.82 and Coverage >= 0.60:** POSITIVE MATCH. The event is automatically linked to the existing profile.
  - **0.65 <= Score < 0.82:** CANDIDATE MATCH. The system links the event but flags it in the dashboard for human operator review.
  - **Score < 0.65:** NO MATCH. A new identity profile is generated.

---

## 7. Data Architecture & API Specification

### Database Schema (MySQL)

- `cameras`: Stores camera configurations, intrinsic matrices, ground homographies, and boundary line pixel coordinates.
- `persons`: Stores long-term profiles, first/last seen timestamps, physical measurements, and Qdrant vector IDs.
- `crossing_events`: Logs the timestamp, camera ID, direction (IN/OUT), match type, fusion scores, and human review status.
- `bag_observations`: Links detected bag counts and types to specific crossing events via foreign keys.
- `analytics_daily`: Materialized views for fast dashboard rendering of daily trends.

### FastAPI Endpoints (Gated by JWT Authentication)

- **Streaming:** `/api/v2/stream/live` (Video stream), `/ws/events` (WebSocket for UI popups).
- **Querying:** `/api/v2/events`, `/api/v2/persons`.
- **Configuration:** `/api/v2/cameras/{camera_id}/calibrate`, `/api/v2/cameras/{camera_id}/boundary`.
- **Export:** `/api/v2/export/events?format=csv`.

---

## 8. Privacy, Security, & Legal Compliance

BorderVision processes biometric data (Special Category Data under GDPR Art. 9). Strict controls are embedded in the architecture:

- **Data Minimization:** Raw video frames are **never** stored in the database. Only mathematical embeddings and metadata are retained.
- **Automated Retention Policies:**
  - Crossing events are automatically purged after 90 days.
  - Person profiles and vector embeddings are purged 30 days after their last sighting.
- **Right to Erasure:** A dedicated API endpoint allows system administrators to completely delete a person's profile and wipe their embeddings from the Qdrant database to comply with GDPR requests.
- **Encryption:** AES-256 encryption at rest is enforced for the MySQL database, and TLS 1.3 is required for all API and web traffic in transit.
- **Access Control:** Role-based access control restricts capabilities across three tiers: `viewer` (read-only), `operator` (human review capabilities), and `admin` (system configuration and data erasure).

---

## 9. Model Optimization

To achieve 25–30 FPS on the recommended hardware, the following optimizations are mandatory:

1. **TensorRT Export:** All YOLO models must be exported to TensorRT (`.engine` format) with FP16 (half-precision) enabled, reducing VRAM usage and inference time by approximately 40%.
2. **ONNX Export:** FastReID models must be exported to ONNX format.
3. **Staggered Inference:** Only the YOLO detection and segmentation models run on every frame. YOLO Pose runs every 3rd frame (10 FPS), FastReID runs once per second per track, and OpenGait runs only when enough frames are accumulated.

---

## 10. Accuracy Expectations & Known Limitations

The system provides probabilistic analytics, not deterministic legal identification.

- **Crossing Detection:** 97–99% accuracy in clear views; drops to 85–93% in heavily crowded environments due to occlusion.
- **Height Estimation:** ±5–10 cm error range when the subject is fully visible and upright.
- **Long-Term Re-Identification (0.82 Threshold):** Achieves a 72–82% True Positive Rate for individuals returning on the same day in the same clothing. This drops to 28–45% if the individual returns on a different day wearing a mask and entirely different clothing.
- **Fundamental Limitations:** The system cannot definitively distinguish between twins or individuals with nearly identical body types and clothing. Dense crowds will cause BoT-SORT ID switching. The system is an analytics aid and high-stakes actions should always rely on human verification.
```
