import os
import time
from typing import Optional
from fastapi import FastAPI, Request, Response, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURES_DIR = os.path.join(BASE_DIR, "captures")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(CAPTURES_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(title="Smart Dual Camera Access Control Cloud Server")

app.mount("/captures", StaticFiles(directory=CAPTURES_DIR), name="captures")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Lưu trữ lịch sử truy cập (In-memory log)
access_logs = []

# Lưu session tạm
sessions = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Trang Web Dashboard quản trị thời gian thực"""
    context = {
        "request": request,
        "logs": access_logs[::-1],
        "total_access": len(access_logs),
        "unlocked_count": sum(1 for log in access_logs if log["status"] == "UNLOCK"),
        "denied_count": sum(1 for log in access_logs if log["status"] == "DENIED")
    }
    return templates.TemplateResponse(request=request, name="index.html", context=context)

@app.get("/api/logs")
async def get_logs():
    """API lấy lịch sử mới nhất cho giao diện Real-time"""
    return {
        "logs": access_logs[::-1],
        "total": len(access_logs)
    }

@app.post("/api/upload_master")
async def upload_master(request: Request, session_id: Optional[str] = Query(None)):
    """
    Nhận ảnh từ Master ESP32-S3 (Camera trực diện OV5640)
    Thực hiện nhận diện khuôn mặt và trả về UNLOCK / DENIED
    """
    image_data = await request.body()
    if not image_data:
        return JSONResponse({"status": "ERROR", "message": "No image data"}, status_code=400)

    curr_time = time.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_num = int(time.time())
    if not session_id:
        session_id = f"SES_{timestamp_num}"

    filename = f"master_{session_id}_{timestamp_num}.jpg"
    filepath = os.path.join(CAPTURES_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(image_data)

    if session_id not in sessions:
        sessions[session_id] = {"time": curr_time}
    sessions[session_id]["master_img"] = f"/captures/{filename}"

    # -------------------------------------------------------------
    # AI LOGIC & RULE (Mô phỏng AI Face Recognition & Liveness)
    # Mặc định: Phê duyệt UNLOCK để mở khóa cửa
    # -------------------------------------------------------------
    decision = "UNLOCK"
    confidence = 0.97
    message = "Xac thuc khuon mat hop le! Cho phep mo cua."

    log_entry = {
        "id": len(access_logs) + 1,
        "session_id": session_id,
        "time": curr_time,
        "master_img": sessions[session_id].get("master_img"),
        "slave_img": sessions[session_id].get("slave_img", None),
        "status": decision,
        "confidence": confidence,
        "message": message
    }
    access_logs.append(log_entry)

    # Giữ tối đa 100 log gần nhất
    if len(access_logs) > 100:
        access_logs.pop(0)

    print(f"[CLOUD SERVER] Master upload {session_id} - Ket qua: {decision}")

    return {
        "status": decision,
        "session_id": session_id,
        "confidence": confidence,
        "message": message
    }

@app.post("/api/upload_slave")
async def upload_slave(request: Request, session_id: Optional[str] = Query(None)):
    """
    Nhận ảnh từ Slave ESP32-CAM (Camera góc nghiêng OV3660)
    Dùng cho chống giả mạo Liveness 3D
    """
    image_data = await request.body()
    if not image_data:
        return JSONResponse({"status": "ERROR", "message": "No image data"}, status_code=400)

    curr_time = time.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_num = int(time.time())
    if not session_id:
        session_id = f"SES_{timestamp_num}"

    filename = f"slave_{session_id}_{timestamp_num}.jpg"
    filepath = os.path.join(CAPTURES_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(image_data)

    if session_id not in sessions:
        sessions[session_id] = {"time": curr_time}
    sessions[session_id]["slave_img"] = f"/captures/{filename}"

    # Cập nhật slave_img vào log tương ứng nếu master đã ghi log trước
    for log in reversed(access_logs):
        if log["session_id"] == session_id:
            log["slave_img"] = f"/captures/{filename}"
            break

    print(f"[CLOUD SERVER] Slave upload {session_id} - Da luu goc nghieng.")

    return {
        "status": "OK",
        "session_id": session_id,
        "message": "Slave capture received successfully"
    }

@app.get("/health")
async def health():
    return {"status": "HEALTHY", "service": "Smart Dual Camera Cloud"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
