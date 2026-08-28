# Hướng Dẫn Bắt Đầu Nhanh (Quick Start)

Dành cho máy tính đã cài đặt xong hoàn toàn (Môi trường, CUDA, Thư viện).

**1. Khởi động Giao diện phần mềm (GUI)**
*Cách 1 (Nếu dùng mã nguồn):*
```powershell
cd "D:\OneDrive\Máy tính\ResearchTool"
.\.venv\Scripts\Activate.ps1
python research_tool_gui.py
```
*Cách 2 (Nếu dùng bản đóng gói):* Nhấp đúp vào file `ResearchTool.exe`.

**2. Chạy trên Windows (Điều khiển chuột máy tính)**
1. Mở sẵn trình duyệt web an toàn và phóng to toàn màn hình.
2. Trên phần mềm GUI:
   - Nhập **Goal** (Ví dụ: "Tìm giá chuột máy tính").
   - Platform: **windows**.
   - Bấm **START** và xác nhận cảnh báo.
3. Phần mềm sẽ tự thu nhỏ. Bỏ tay khỏi chuột vật lý và để AI làm việc.
*(Cấp cứu: Hất mạnh chuột lên góc trên cùng bên trái màn hình).*

**3. Chạy trên Điện thoại Android (Cáp USB)**
1. Cắm cáp USB nối điện thoại vào máy, mở khóa màn hình, đã bật "Gỡ lỗi USB".
2. Trên phần mềm GUI:
   - Platform: **android**.
   - Bấm **Refresh** cạnh ô ADB Device và chọn thiết bị của bạn.
   - Nhập **Goal** và bấm **START**.
*(Cấp cứu: Rút cáp USB hoặc bấm EMERGENCY STOP trên GUI).*

**4. Dừng và Xuất Kết quả**
- Trên tab **Dashboard**, bấm nút **STOP**.
- Bấm nút **Export CSV**.
- Mở thư mục dự án để lấy file Excel kết quả.
