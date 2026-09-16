# Hướng Dẫn Đưa Cloud Web Server Lên Render.com

Thư mục: `smart_dual_camera_access_idf/cloud_server/`

---

## BƯỚC 1: Đẩy thư mục `cloud_server` lên GitHub

1. Tạo một repository mới trên GitHub (ví dụ đặt tên: `smart-dual-camera-server`).
2. Mở Terminal trong máy tính và push thư mục `cloud_server` lên:
   ```bash
   cd c:\Users\ACER\.gemini\antigravity-ide\scratch\smart_dual_camera_access_idf\cloud_server
   git init
   git add .
   git commit -m "Init cloud server"
   git branch -M main
   git remote add origin https://github.com/<USERNAME>/smart-dual-camera-server.git
   git push -u origin main
   ```

---

## BƯỚC 2: Tạo Web Service trên Render.com (Hoàn toàn Miễn phí)

1. Đăng nhập vào [https://render.com](https://render.com) (bằng tài khoản GitHub).
2. Bấm nút **New +** $\rightarrow$ chọn **Web Service**.
3. Chọn repository GitHub vừa tạo (`smart-dual-camera-server`).
4. Điền các thông số:
   - **Name**: `smart-dual-camera` (hoặc tên tùy thích)
   - **Region**: Singapore (gần Việt Nam nhất, độ trễ thấp)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. Bấm **Create Web Service**.
6. Chờ Render build khoảng 1-2 phút. Khi hoàn tất, Render sẽ cấp cho bạn một đường dẫn công khai (URL) có dạng:
   👉 **`https://smart-dual-camera-xxxx.onrender.com`**

---

## BƯỚC 3: Cập nhật URL vào ESP32 Master & Slave

Sau khi có URL Render, bạn chỉ cần mở 2 file:
1. `master_esp32s3/main/main.c` dòng 20:
   ```c
   #define SERVER_URL    "https://smart-dual-camera-xxxx.onrender.com/api/upload_master"
   ```
2. `slave_esp32cam/main/main.c` dòng 20:
   ```c
   #define SERVER_URL    "https://smart-dual-camera-xxxx.onrender.com/api/upload_slave"
   ```
3. Nạp lại firmware cho cả 2 bo bằng lệnh:
   ```powershell
   idf.py -p COMx flash monitor
   ```

---

## BƯỚC 4: Trải nghiệm thực tế
- Bạn mở trình duyệt điện thoại hoặc máy tính truy cập vào: `https://smart-dual-camera-xxxx.onrender.com`
- Khi có người đứng trước cửa $\rightarrow$ Giao diện Web lập tức nhảy thông báo, hiện ảnh 2 góc của người đó và báo kết quả mở cửa!
