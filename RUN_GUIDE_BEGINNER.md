# Sổ Tay Hướng Dẫn Sử Dụng (End-to-End User Manual)

Chào mừng bạn đến với **ResearchTool**. Đây là tài liệu hướng dẫn cực kỳ chi tiết, được viết dành riêng cho người dùng phổ thông (không yêu cầu kiến thức lập trình). 

Tài liệu này sẽ dẫn dắt bạn từ con số 0: từ lúc mở máy, khởi động ứng dụng giao diện trực quan (GUI), cho đến khi AI có thể tự động lướt web trên máy tính hoặc điện thoại Android của bạn để thu thập dữ liệu.

---

## PHẦN 1 — HIỂU CÁC THUẬT NGỮ CỦA ỨNG DỤNG

Trước khi bắt đầu, hãy làm quen với một số khái niệm cơ bản:

* **ResearchTool:** Là tên phần mềm này. Nó là một "Đặc vụ" (Agent) có tay và mắt để tự dùng máy tính của bạn tìm thông tin tự động.
* **VLM (Vision-Language Model):** "Đôi mắt và Bộ não" của AI (VD: mô hình `qwen2-vl`). Nó nhìn vào ảnh chụp màn hình và phân tích nút bấm đang nằm ở đâu.
* **Controller (Người điều khiển):** "Đôi tay" của AI. Giúp AI bấm chuột, gõ phím trên Windows, hoặc vuốt chạm trên màn hình điện thoại.
* **SQLite / Database:** "Sổ ghi chép". Nơi AI lưu mọi dữ liệu tìm được.
* **Frontier / Seed:** 
  * `Seed` (Hạt giống): Từ khóa ban đầu bạn giao cho AI (VD: "Ghế công thái học").
  * `Frontier` (Tiền tuyến): Khi AI lướt web và thấy thông tin mới, nó sẽ cho link đó vào danh sách `Frontier` để lát nữa tự động truy cập.
* **GUI (Graphical User Interface):** Giao diện phần mềm thông thường có nút bấm bằng chuột (chính là cách bạn sẽ sử dụng phần mềm này).
* **Checkpoint:** "Điểm lưu", giống như save game, để lỡ tắt máy thì AI vẫn nhớ nó đang làm gì.

---

## PHẦN 2 — CÀI ĐẶT VÀ KHỞI ĐỘNG LẦN ĐẦU (FIRST-TIME SETUP)

Để mở phần mềm, bạn có 2 cách tùy thuộc vào việc bạn đang dùng bản mã nguồn (chạy bằng Python) hay bản phần mềm đóng gói (File `.exe`).

### Cách A: Khởi động qua PowerShell (Bản mã nguồn - Setup lần đầu)
1. Bấm nút **Start**, gõ `PowerShell` và nhấn Enter.
2. Di chuyển vào thư mục dự án và bật môi trường ảo (nơi chứa các công cụ Python):
```powershell
# [SAFE / READ ONLY]
cd "D:\OneDrive\Máy tính\ResearchTool"
.\.venv\Scripts\Activate.ps1
```
3. Mở phần mềm GUI:
```powershell
# [SAFE / READ ONLY]
python research_tool_gui.py
```

### Cách B: Khởi động bản đóng gói
Nếu bạn đã chạy công cụ tạo gói (Packaging), bạn chỉ cần nhấp đúp (Double-click) vào file **ResearchTool.exe**. Không cần gõ lệnh.

*(Khi cửa sổ phần mềm "Autonomous Research Tool" hiện lên, bạn đã thành công!)*

---

## PHẦN 3 — BÍ KÍP AN TOÀN (CẦN ĐỌC TRƯỚC KHI CHẠY)

Vì phần mềm này sẽ TỰ ĐỘNG ĐIỀU KHIỂN CHUỘT VÀ BÀN PHÍM của bạn, bạn cần biết cách dừng nó lại.

1. **DỪNG KHẨN CẤP (EMERGENCY STOP) BẰNG CHUỘT VẬT LÝ:**
   Bất cứ khi nào bạn thấy AI click nhầm chỗ, hãy cầm con chuột vật lý của bạn, **đẩy thật mạnh và hất con trỏ chuột bay về góc trên cùng bên trái màn hình** (Tọa độ X:0, Y:0). Hệ thống "Failsafe" sẽ giật cầu dao ngắt điện lập tức.

2. **Dừng bằng nút bấm:** 
   Trong giao diện phần mềm (GUI) có nút **STOP** (Dừng an toàn) và **EMERGENCY STOP** (Ngắt lập tức).

3. **HUMAN_REQUIRED (Cần con người hỗ trợ):** 
   Nếu AI gặp CAPTCHA xác minh, trang bắt đăng nhập, nó sẽ tự dừng và nhường chuột lại cho bạn.

---

## PHẦN 4 — CHẠY NHIỆM VỤ TRÊN WINDOWS (WINDOWS MODE)

Đây là cách sử dụng chính: Để AI tự tìm thông tin trên máy tính.

**Chuẩn bị:** 
1. Mở sẵn một cửa sổ trình duyệt (Google Chrome, Edge...) an toàn, phóng to toàn màn hình. Thu nhỏ mọi tài liệu chứa thông tin cá nhân.
2. Để cửa sổ ResearchTool GUI lên trên cùng.

**Các bước trên Giao diện GUI:**
1. **Goal / Query:** Nhập mục tiêu (VD: *"Tìm giá ghế công thái học quanh mức 2 triệu"*).
2. **Platform:** Chọn `windows`.
3. **Vision Model:** Chọn `qwen2-vl`.
4. **TimeEnd (mins):** Giới hạn thời gian (VD: nhập `10` để AI tự dừng sau 10 phút. Nhập `0` là chạy vô tận).
5. Bấm nút **START**.
6. Ứng dụng sẽ hiện bảng cảnh báo: *"The Agent will take control of your mouse..."*. Bấm **OK**.
7. **Cửa sổ phần mềm sẽ TỰ ĐỘNG THU NHỎ (Minimize)** để nhường màn hình cho AI làm việc.

**[MOVES MOUSE] [CLICKS/TYPES] [LONG RUNNING]**
*(Đừng chạm tay vào chuột nữa. Hãy quan sát AI chụp ảnh, suy nghĩ và tự lướt web).*

---

## PHẦN 5 — ĐIỀU KHIỂN ĐIỆN THOẠI ANDROID (ANDROID MODE)

Bạn có thể cắm cáp nối điện thoại Android (như iQOO Z10 Turbo+) vào máy tính và để AI điều khiển điện thoại thay vì dùng chuột máy tính.

**Chuẩn bị (Trên điện thoại):**
1. Bật **Developer Options (Tùy chọn nhà phát triển)**.
2. Bật **USB Debugging (Gỡ lỗi USB)** và cho phép "Giả lập vuốt/chạm".
3. Cắm cáp USB nối điện thoại vào laptop. Xác nhận "Cho phép máy tính này" trên điện thoại.

**Các bước trên Giao diện GUI:**
1. Mở ResearchTool GUI.
2. Mục **Platform**, chọn `android`. (Khung cài đặt Android sẽ hiện ra).
3. Bấm nút **Refresh** kế bên ô "ADB Device". Mã số thiết bị của bạn sẽ hiện ra.
4. Tích chọn ô **"Use scrcpy stream"** để dùng phần mềm chia sẻ màn hình siêu tốc (giúp AI nhìn màn hình điện thoại nét và nhanh hơn).
5. Nhập mục tiêu (Goal) và bấm **START**.

**[CONTROLS ANDROID] [LONG RUNNING]**
*(Chuột máy tính của bạn vẫn dùng bình thường. Màn hình điện thoại của bạn sẽ tự động vuốt và mở ứng dụng).*

---

## PHẦN 6 — THEO DÕI, TẠM DỪNG VÀ TIẾP TỤC (DASHBOARD & RESUME)

Khi AI đang chạy, bạn có thể mở lại cửa sổ ResearchTool GUI (đang thu nhỏ dưới thanh Taskbar) để xem **Tab Dashboard**.

* **Status:** Hiện chữ `RUNNING` (Đang chạy), `THINKING` (Đang phân tích ảnh), hoặc `DONE` (Hoàn thành).
* **Metrics (Số liệu):** Hiển thị AI đã nhặt được bao nhiêu thông tin (Entities/Evidence).
* **Hardware:** Xem AI đang ngốn bao nhiêu RAM và VRAM (Card đồ họa).
* **Nút STOP:** Bấm để bảo AI hoàn thành việc dở dang rồi dừng một cách an toàn.
* **Resume (Khôi phục):** Trên GUI hiện chữ `Run ID: 01H...`. Hãy copy mã này. Lần sau nếu bạn muốn AI làm tiếp việc cũ, chỉ cần mở CLI (xem Phần Tương Tác Nâng Cao) hoặc tích hợp tính năng Resume trên GUI trong các phiên bản tới.

---

## PHẦN 7 — XUẤT KẾT QUẢ DỮ LIỆU (OUTPUT)

Dữ liệu của bạn không lưu trên mạng, mà lưu thẳng vào ổ cứng máy bạn.
Cấu trúc thư mục (nằm ở ô *Output Directory* trên GUI, mặc định là mục `data`):
```text
D:\OneDrive\Máy tính\ResearchTool\
└── data\
    ├── research.db          (File lưu toàn bộ quá trình)
    └── screenshots\         (Ảnh chụp màn hình AI đã nhìn)
```

**Cách xuất ra Excel (.csv):**
Ngay trên **Tab Dashboard** của giao diện GUI, bấm nút **"Export CSV"**. 
Mở thư mục cài đặt dự án, bạn sẽ thấy các file `entities.csv` (Thực thể), `evidence.csv` (Bằng chứng) đã sẵn sàng để mở bằng Excel.

---

## PHẦN 8 — GỠ RỐI (TROUBLESHOOTING)

| Vấn đề | Ý nghĩa | Cách xử lý |
| :--- | :--- | :--- |
| **CUDA unavailable** | Khung hiển thị Hardware báo VRAM 0MB hoặc báo lỗi CUDA. | Máy thiếu thư viện đồ họa hoặc driver card NVIDIA 3050 Ti. |
| **PyAutoGUI cannot move**| Chuột bị kẹt ở góc 0,0 do hệ thống an toàn (Failsafe) kích hoạt. | Kéo chuột ra giữa màn hình, nhấn STOP và START lại. |
| **Bấm Refresh không thấy ADB Device**| Máy tính chưa nhận điện thoại. | Kiểm tra cáp USB, mở khóa màn hình đt, tick vào "Luôn cho phép kết nối USB". |
| **UNKNOWN state / Vòng lặp**| AI liên tục cuộn trang lên xuống mãi ở 1 web. | Hất chuột góc trái, bấm STOP. Đổi lại câu lệnh (Goal) cho cụ thể hơn. |
| **VRAM OOM** | Hết bộ nhớ 4GB của Card Đồ Họa 3050 Ti. | Tắt bớt các ứng dụng đang mở, Chrome Tabs đang xem phim/chơi game. |

---

## PHẦN 9 — [DÀNH CHO LẬP TRÌNH VIÊN] TƯƠNG TÁC NÂNG CAO QUA DÒNG LỆNH (CLI)

Giao diện đồ họa (GUI) đã làm hết 95% công việc. Nếu bạn muốn dùng dòng lệnh chuyên sâu (CLI / TUI) để gỡ lỗi:

Mở PowerShell:
```powershell
cd "D:\OneDrive\Máy tính\ResearchTool"
.\.venv\Scripts\Activate.ps1
```

**Chạy CLI trực tiếp:**
```powershell
research-tool run "Mục tiêu" --platform windows --model qwen2-vl
```
**Chạy tiếp (Resume) qua CLI:**
```powershell
research-tool run "Tiếp tục" --resume "MÃ_RUN_ID"
```
**Xuất file bằng tay:**
```powershell
research-tool export "MÃ_RUN_ID" --format csv
```

**ĐÓNG GÓI PHẦN MỀM THÀNH .EXE:**
```powershell
python scripts\build_standalone.py
```
*(File .exe sẽ nằm trong thư mục `dist/`).*
