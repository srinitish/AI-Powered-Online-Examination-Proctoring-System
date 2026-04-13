import cv2
import time
import cvzone
from ultralytics import YOLO
 
# YOLO class IDs we care about
PERSON       = 0
CELL_PHONE   = 67
LAPTOP       = 63
BOOK         = 73
REMOTE       = 65   # sometimes confused with phones
 
MALPRACTICE_CLASSES = {67: "Phone", 63: "Laptop", 73: "Book", 65: "Remote"}
 
class ExamDetector:
    def __init__(self, model_path="yolov8n.pt", conf=0.4, cooldown=10, max_captures=10):
        self.model           = YOLO(model_path)
        self.conf            = conf
        self.cooldown        = cooldown
        self.max_captures    = max_captures
 
        self.mal_count       = 0
        self.last_capture    = 0
        self.status          = "Waiting"
        self.violation_log   = []   # list of {"time": ..., "reason": ..., "file": ...}
 
    # ------------------------------------------------------------------ #
    def process(self, frame):
        """Run detection on one frame; returns annotated frame + status."""
        classes_to_detect = [PERSON] + list(MALPRACTICE_CLASSES.keys())
        results = self.model(frame, conf=self.conf, classes=classes_to_detect, verbose=False)
 
        person_count  = 0
        mal_reasons   = []
 
        for r in results:
            for box in r.boxes:
                cls  = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = self.model.names[cls]
                conf_val = float(box.conf[0])
 
                color = (0, 255, 0) if cls == PERSON else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cvzone.putTextRect(
                    frame, f"{label} {conf_val:.0%}",
                    (x1, y1 - 5), scale=0.8, thickness=1,
                    colorR=color, offset=4
                )
 
                if cls == PERSON:
                    person_count += 1
                elif cls in MALPRACTICE_CLASSES:
                    mal_reasons.append(MALPRACTICE_CLASSES[cls])
 
        # --- Rules ---
        if person_count == 0:
            mal_reasons.append("No person detected")
        elif person_count > 1:
            mal_reasons.append(f"Multiple persons ({person_count})")
 
        malpractice = bool(mal_reasons)
 
        if malpractice:
            self.status = "Malpractice Detected"
            reason_text = ", ".join(mal_reasons)
            cvzone.putTextRect(frame, f"MALPRACTICE: {reason_text}",
                               (20, 50), scale=1.2, thickness=2,
                               colorR=(0, 0, 220), offset=8)
            self._maybe_capture(frame, reason_text)
        else:
            self.status = "Fair"
            cvzone.putTextRect(frame, "Fair — Exam in Progress",
                               (20, 50), scale=1.2, thickness=2,
                               colorR=(0, 180, 0), offset=8)
 
        return frame
 
    # ------------------------------------------------------------------ #
    def _maybe_capture(self, frame, reason):
        now = time.time()
        if now - self.last_capture > self.cooldown and self.mal_count < self.max_captures:
            filename = f"violation_{self.mal_count + 1:02d}.jpg"
            cv2.imwrite(filename, frame)
            self.violation_log.append({
                "id":     self.mal_count + 1,
                "time":   time.strftime("%H:%M:%S"),
                "reason": reason,
                "file":   filename
            })
            self.mal_count      += 1
            self.last_capture    = now
 
    # ------------------------------------------------------------------ #
    def get_summary(self):
        return {
            "status":         self.status,
            "mal_count":      self.mal_count,
            "violation_log":  self.violation_log,
        }
 
    def reset(self):
        self.mal_count     = 0
        self.last_capture  = 0
        self.status        = "Waiting"
        self.violation_log = []
 