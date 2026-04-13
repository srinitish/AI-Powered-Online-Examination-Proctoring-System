import cv2
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from detector import ExamDetector

app = FastAPI()

# Templates folder
templates = Jinja2Templates(directory="templates")

# Globals
camera = cv2.VideoCapture(0)

detector = ExamDetector(
    model_path="yolov8n.pt",
    conf=0.40,
    cooldown=10,
    max_captures=10
)

tab_switch_count = 0

if not camera.isOpened():
    raise RuntimeError("Could not open camera. Check your device index.")


# ── Frame generator ─────────────────────────────
def generate_frames():
    while True:
        ok, frame = camera.read()
        if not ok:
            break

        frame = detector.process(frame)

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


# ── Routes ─────────────────────────────────────

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/video")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/status")
def get_status():
    summary = detector.get_summary()
    summary["tab_switches"] = tab_switch_count
    return summary


@app.post("/tab_violation")
def tab_violation():
    global tab_switch_count
    tab_switch_count += 1
    print(f"[TAB SWITCH] count = {tab_switch_count}")
    return {"tab_switches": tab_switch_count}


@app.post("/reset")
def reset_session():
    global tab_switch_count
    detector.reset()
    tab_switch_count = 0
    return {"message": "Session reset."}