# Hướng Dẫn Bắt Đầu Nhanh (Quick Start)

Dành cho máy đã cài đặt xong hoàn toàn (Môi trường, CUDA, Thư viện).

**1. Mở thư mục và Kích hoạt môi trường (PowerShell):**
```powershell
# [SAFE / READ ONLY]
cd "D:\OneDrive\Máy tính\ResearchTool"
.\.venv\Scripts\Activate.ps1
```

**2. Tùy chọn A: Chạy trên Windows (Dùng Chuột Màn Hình)**
Hãy mở trình duyệt sẵn và thả tay khỏi chuột trước khi nhấn Enter.
```powershell
# [MOVES MOUSE] [CLICKS/TYPES] [LONG RUNNING]
research-tool run "Mục tiêu tìm kiếm của bạn" --platform windows
```
*(Cấp cứu: Hất mạnh chuột lên góc trên cùng bên trái màn hình).*

**2. Tùy chọn B: Chạy trên Điện thoại Android (Cáp USB)**
Đảm bảo đã cắm cáp, bật Gỡ lỗi USB và điện thoại đã sáng màn hình.
```powershell
# [CONTROLS ANDROID] [LONG RUNNING]
research-tool run "Mục tiêu tìm kiếm của bạn" --platform android
```
*(Cấp cứu: Rút cáp USB hoặc bấm Ctrl + C).*

**3. Khôi Phục Phiên Đang Chạy Dở (Resume)**
```powershell
# [MOVES MOUSE / CONTROLS ANDROID]
research-tool run "Tiếp tục" --resume "MÃ_RUN_ID"
```

**4. Xuất Dữ Liệu Ra File Excel (CSV)**
```powershell
# [SAFE / READ ONLY]
research-tool export "MÃ_RUN_ID" --format csv --out ./ket_qua
```
Mở thư mục `ket_qua` để xem file.
