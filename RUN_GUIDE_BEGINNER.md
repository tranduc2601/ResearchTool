# Sổ Tay Hướng Dẫn Sử Dụng (End-to-End User Manual)

Chào mừng bạn đến với **ResearchTool**. Đây là tài liệu hướng dẫn cực kỳ chi tiết, được viết dành riêng cho người mới bắt đầu (không yêu cầu kiến thức lập trình). 

Tài liệu này sẽ dẫn dắt bạn từ con số 0: từ lúc mở máy, thiết lập công cụ, hiểu cách AI hoạt động, cho đến khi AI có thể tự động lướt web trên máy tính hoặc điện thoại Android của bạn để thu thập dữ liệu.

---

## PHẦN 1 — CÀI ĐẶT LẦN ĐẦU (FIRST-TIME SETUP)

### 1. Mở PowerShell và Vào Thư Mục Dự Án
PowerShell là "Giao diện dòng lệnh" (CLI) của Windows, nơi bạn gõ các dòng chữ để ra lệnh cho máy tính.
1. Bấm nút **Start** trên Windows, gõ `PowerShell` và nhấn Enter.
2. Bạn cần di chuyển vào thư mục chứa phần mềm này. Gõ lệnh sau và nhấn Enter:

```powershell
# [SAFE / READ ONLY]
cd "D:\OneDrive\Máy tính\ResearchTool"
```

### 2. Kích Hoạt Môi Trường Ảo (.venv)
Môi trường ảo (Virtual Environment) là một chiếc "hộp cách ly", chứa toàn bộ các công cụ cần thiết cho phần mềm này mà không làm ảnh hưởng đến các phần mềm khác trên máy tính của bạn.

```powershell
# [SAFE / READ ONLY]
.\.venv\Scripts\Activate.ps1
```
*(Thành công: Bạn sẽ thấy chữ `(.venv)` màu xanh lá xuất hiện ở đầu dòng lệnh).*

### 3. Kiểm Tra Python và Card Đồ Họa (GPU)
Ứng dụng cần **Python** (ngôn ngữ lập trình) và **CUDA** (công nghệ giúp AI chạy mượt trên Card đồ họa NVIDIA RTX 3050 Ti của bạn).

Kiểm tra Python:
```powershell
# [SAFE / READ ONLY]
python --version
```

Kiểm tra Card Đồ Họa (CUDA):
```powershell
# [SAFE / READ ONLY]
python -c "import torch; print('CUDA Hợp lệ:', torch.cuda.is_available())"
```
*(Thành công: Hệ thống in ra `CUDA Hợp lệ: True`).*

### 4. Kiểm Tra Các Phần Mềm Phụ Trợ (Bên Ngoài)
* **Tesseract OCR:** Công cụ giúp AI "đọc" các dòng chữ nhỏ li ti trên màn hình.
* **ADB (Android Debug Bridge):** Công cụ "cầu nối" giúp máy tính gửi lệnh điều khiển tới điện thoại Android qua cáp USB.
* **scrcpy:** Phần mềm giúp truyền hình ảnh màn hình điện thoại lên máy tính siêu tốc.

```powershell
# [SAFE / READ ONLY]
tesseract --version
adb version
scrcpy --version
```
*(Nếu một trong các lệnh trên báo lỗi màu đỏ "is not recognized", phần mềm đó chưa được cài hoặc chưa được thêm vào Windows PATH. Bạn vẫn có thể chạy trên Windows bình thường, nhưng sẽ không dùng được Android hoặc OCR cho đến khi cài chúng).*

---

## PHẦN 2 — HIỂU CÁC THUẬT NGỮ CỦA ỨNG DỤNG

* **ResearchTool:** Là tên phần mềm này. Khác với ChatGPT (chỉ biết nói chuyện), ResearchTool là một "Đặc vụ" (Agent) có tay và mắt để tự dùng máy tính của bạn tìm thông tin.
* **VLM (Vision-Language Model):** "Đôi mắt và Bộ não" của AI (ở đây dùng mô hình `Qwen2-VL`). Nó nhìn vào ảnh chụp màn hình và phân tích xem nút bấm đang nằm ở tọa độ nào.
* **Controller (Người điều khiển):** "Đôi tay" của AI. Giúp AI bấm chuột, gõ phím trên Windows, hoặc vuốt chạm trên Android.
* **SQLite:** "Sổ ghi chép". Đây là một hệ cơ sở dữ liệu siêu nhẹ được lưu thành 1 file duy nhất (`research.db`). Mọi thứ AI tìm được đều ghi vào đây.
* **Frontier / Seed:** 
  * `Seed` (Hạt giống): Từ khóa ban đầu bạn giao cho AI (VD: "Ghế công thái học").
  * `Frontier` (Tiền tuyến): Khi AI lướt web và thấy thông tin mới (VD: thấy link "Ghế Hòa Phát"), nó sẽ cho link đó vào danh sách `Frontier` để lát nữa tự động truy cập.
* **Screenshots / Logs / Evidence:** Hình ảnh màn hình, Sổ nhật ký lỗi, và Bằng chứng thông tin cắn rứt được từ web.
* **CLI / TUI / GUI:**
  * **CLI:** Dòng lệnh toàn chữ đen trắng.
  * **TUI (Text User Interface):** Dòng lệnh nhưng có đóng khung màu sắc, thanh tiến trình đẹp mắt.
  * **GUI (Graphical User Interface):** Cửa sổ phần mềm bình thường có nút bấm chuột (giống Word hay Excel).

---

## PHẦN 3 — CÁC BÀI KIỂM TRA AN TOÀN (SAFE TESTS)

Trước khi cho phép AI cướp chuột của bạn, chúng ta phải thử nghiệm độ an toàn.

**BÍ KÍP DỪNG KHẨN CẤP (FAILSAFE):**
Nếu AI đang tự di chuyển chuột mà bạn muốn dừng nó ngay lập tức: **Hãy cầm chuột vật lý của bạn và đẩy thật mạnh, hất con trỏ chuột bay về góc trên cùng bên trái màn hình (Tọa độ X:0, Y:0).** Hệ thống (PyAutoGUI) sẽ kích hoạt công tắc ngắt điện khẩn cấp và dừng ngay lập tức!
Cách thứ 2 là bấm `Ctrl + C` ở cửa sổ PowerShell.

**Bài test 1: Kiểm tra "Mắt" AI (Không đụng chuột)**
Lệnh này chỉ đọc 1 bức ảnh giả và yêu cầu VLM phân tích xem VRAM có bị đầy không.
```powershell
# [SAFE / READ ONLY]
python scripts\validation\benchmark_stability.py --model qwen2-vl --iters 1
```

**Bài test 2: Kiểm tra Đọc Chữ OCR (Không đụng chuột)**
```powershell
# [SAFE / READ ONLY]
python scripts\validation\benchmark_ocr.py
```

---

## PHẦN 4 — CHẠY THỬ LẦN ĐẦU TRÊN WINDOWS

Chúng ta sẽ chạy một đoạn kịch bản ngắn để AI thử click chuột.

**Chuẩn bị:** 
1. Mở một trình duyệt web (Google Chrome hoặc Edge), vào trang chủ Google.
2. Để trình duyệt phóng to toàn màn hình. Thu nhỏ mọi thứ khác chứa thông tin cá nhân.
3. Rời tay khỏi chuột.

**Lệnh chạy:**
```powershell
# [MOVES MOUSE] [CLICKS/TYPES]
python scripts\run_acceptance.py
```

* **AI sẽ làm gì?** Con trỏ chuột của bạn sẽ tự động bay quanh màn hình. Nó sẽ cố chụp ảnh, tìm nút bấm, và click. 
* **Thành công:** Sau 1-2 hành động, AI nhận ra đã hoàn thành hoặc hết lệnh và tự thoát.
* **Thất bại:** Chuột click điên cuồng vào góc màn hình hoặc văng lỗi màu đỏ. (Nhớ dùng tuyệt chiêu hất chuột lên góc trái nếu cần).

---

## PHẦN 5 — ĐIỀU KHIỂN ANDROID BẰNG ĐIỆN THOẠI THẬT

Ứng dụng hỗ trợ cực tốt cho điện thoại thật của bạn (**iQOO Z10 Turbo+**, màn hình 1260x2800). Bạn phải thiết lập điện thoại trước:

1. **Bật Developer Options (Tùy chọn nhà phát triển):** Vào Cài đặt điện thoại -> Giới thiệu điện thoại -> Bấm 7 lần vào "Số phiên bản" (Build Number).
2. **Bật USB Debugging (Gỡ lỗi USB):** Quay ra Cài đặt -> Hệ thống -> Tùy chọn nhà phát triển -> Bật "Gỡ lỗi USB" & Bật "Gỡ lỗi USB (Cài đặt bảo mật - cho phép giả lập vuốt/chạm)".
3. **Kết nối:** Cắm cáp USB nối điện thoại vào laptop. Trên điện thoại sẽ hiện bảng hỏi "Cho phép máy tính này?", hãy bấm **Đồng ý / OK**.

**Kiểm tra kết nối:**
```powershell
# [SAFE / READ ONLY]
adb devices
```
*(Kỳ vọng: Hiện ra 1 dòng mã số kèm chữ `device`. Nếu hiện `unauthorized`, bạn phải mở khóa màn hình điện thoại và bấm Đồng ý).*

**Bắt đầu chạy AI trên Android:**
*(Hãy mở sẵn ứng dụng Shopee hoặc Chrome trên điện thoại).*
```powershell
# [CONTROLS ANDROID] [LONG RUNNING]
research-tool run "Đọc thông tin giá các sản phẩm trên màn hình" --platform android
```
AI sẽ KHÔNG lấy chuột máy tính của bạn. Nó sẽ chụp màn hình điện thoại qua cáp USB, phân tích, và gửi lệnh vuốt/chạm ngược lại điện thoại. 

---

## PHẦN 6 — CHẠY NHIỆM VỤ NGHIÊN CỨU THỰC SỰ

Bây giờ bạn sẽ chạy ứng dụng chính thức để tìm kiếm thực sự trên Windows.
*Hãy mở sẵn Wikipedia, Amazon hoặc trang bạn muốn trên màn hình Windows.*

```powershell
# [MOVES MOUSE] [CLICKS/TYPES] [LONG RUNNING]
research-tool run "Tìm giá ghế ergonomic quanh mức 2 triệu" --platform windows --model qwen2-vl
```

* **Model Selection (`--model`):** Chọn não bộ AI. Mặc định là `qwen2-vl` vì nó chạy cục bộ tốt nhất trên máy bạn.
* **Platform Selection (`--platform`):** Chọn `windows` (chuột máy tính) hoặc `android` (cáp USB).
* **Quá trình AI chạy:**
  1. Chụp màn hình (SEE).
  2. Gửi ảnh vào não bộ Qwen2-VL để suy nghĩ mất 6-8 giây (THINK).
  3. Quyết định di chuyển chuột/cuộn trang (ACT).
  4. Lưu thông tin cắn rứt được vào SQLite.
  5. Lặp lại cho đến khi tìm đủ thông tin.
* **HUMAN_REQUIRED:** Nếu AI gặp CAPTCHA hoặc trang bắt đăng nhập, nó sẽ báo `HUMAN_REQUIRED` và dừng lại nhường chuột cho bạn giải quyết.

---

## PHẦN 7 — DÙNG TUI VÀ GUI (GIAO DIỆN)

Nếu bạn không thích dòng lệnh khô khan, hãy mở Giao Diện (GUI).

```powershell
# [SAFE / READ ONLY]
python src\research_tool\gui\app.py
```

* **Ô Goal/Query:** Nhập mục tiêu (VD: "Tìm giá laptop").
* **Platform:** Chọn nền tảng (Windows / Android).
* **Model:** Chọn mô hình.
* **Start Exploration:** Nút bắt đầu. Vừa bấm xong hãy bỏ tay khỏi chuột ngay nhé!
* **Log Output:** Khung trắng dưới cùng sẽ hiển thị những gì AI đang làm.

---

## PHẦN 8 — DỪNG / TẠM DỪNG / CHẠY TIẾP

* **Dừng bình thường:** Để AI chạy đến khi đạt mục tiêu (`GOAL_MET`).
* **Dừng khẩn cấp:** Bấm `Ctrl + C` hoặc hất chuột lên góc trái 0,0.
* **Checkpoint:** Cứ sau vài lần click, hệ thống tự lưu quá trình làm việc. Nếu tắt máy ngang, dữ liệu KHÔNG bị mất.
* **Resume (Khôi phục):** Mỗi lần chạy sẽ có một `RUN_ID` hiện ra trên màn hình (VD: `01HQF...`). Để làm tiếp công việc đang dang dở:
```powershell
# [MOVES MOUSE] [CLICKS/TYPES] [LONG RUNNING]
research-tool run "Mục tiêu" --resume "MÃ_RUN_ID_CỦA_BẠN"
```

---

## PHẦN 9 — ĐẦU RA VÀ XUẤT DỮ LIỆU (OUTPUT)

Dữ liệu của bạn được lưu an toàn trên ổ cứng, không gửi đi đâu cả.
Cấu trúc thư mục:
```text
D:\OneDrive\Máy tính\ResearchTool\
└── data\
    ├── research.db          (File SQLite chứa chữ, giá, lịch sử click)
    └── screenshots\         (Ảnh chụp màn hình AI đã nhìn)
```

**Cách xuất dữ liệu ra file Excel (.csv):**
```powershell
# [SAFE / READ ONLY]
research-tool export "MÃ_RUN_ID_CỦA_BẠN" --format csv --out "D:\OneDrive\Máy tính\ResearchTool\results"
```
Mở thư mục `results`, bạn sẽ thấy các file `entities.csv` (Thực thể/Sản phẩm), `evidence.csv` (Bằng chứng), v.v.

---

## PHẦN 10 — SỬA LỖI (TROUBLESHOOTING)

| Vấn đề | Ý nghĩa | Cách xử lý |
| :--- | :--- | :--- |
| **CUDA unavailable** | Python không thấy Card RTX 3050 Ti. | Cài lại Driver NVIDIA hoặc thư viện PyTorch bản CUDA. |
| **Model fails to load** | Tải mô hình Qwen2-VL thất bại do lỗi mạng. | Kiểm tra Internet. Chạy lại để nó tải tiếp. |
| **VRAM OOM** | Tràn bộ nhớ Card đồ họa. | Tắt bớt các ứng dụng game, chrome đang mở nặng. |
| **PyAutoGUI cannot move**| Chuột bị kẹt ở góc 0,0 do Failsafe. | Di chuyển chuột ra giữa màn hình và chạy lại. |
| **ADB device unauthorized**| Cắm cáp nhưng chưa cho phép trên đt. | Mở khóa đt, tick vào ô "Luôn cho phép máy tính này". |
| **CAPTCHA / Login**| Web yêu cầu xác minh con người. | AI sẽ dừng. Bạn tự dùng tay giải CAPTCHA rồi chạy Resume. |
| **UNKNOWN state / Loops**| AI bị ngáo, cứ cuộn lên cuộn xuống mãi. | Dừng AI (`Ctrl+C`). Thay đổi từ khóa tìm kiếm rõ ràng hơn. |

*Khi nào nên dừng và nhờ lập trình viên?* Nếu báo lỗi code màu đỏ dài loằng ngoằng (Traceback Exception) liên tục mà bạn đã thử mọi cách.

---

## PHẦN 11 — QUY TRÌNH CHUẨN: TỪ LÚC MỞ MÁY ĐẾN KHI CÓ KẾT QUẢ

Đây là Checklist chính xác cho công việc thực tế hàng ngày:

1. **Mở máy:** Bật Windows, mở ứng dụng Chrome/Edge.
2. **Khởi động:** Mở PowerShell. Gõ:
   ```powershell
   # [SAFE / READ ONLY]
   cd "D:\OneDrive\Máy tính\ResearchTool"
   .\.venv\Scripts\Activate.ps1
   ```
3. **Mở sẵn màn hình:** Mở sẵn trang web (VD: shopee.vn) trên Chrome.
4. **Bắt đầu AI:**
   ```powershell
   # [MOVES MOUSE] [CLICKS/TYPES] [LONG RUNNING]
   research-tool run "So sánh giá bàn phím cơ không dây" --platform windows
   ```
5. **Quan sát (Observe):** Bỏ tay khỏi chuột. Ngồi xem AI di chuyển chuột, đọc ảnh, cuộn trang.
6. **Kết thúc (Stop):** AI in ra `Session completed!`. (Hoặc bạn tự ngắt bằng `Ctrl + C` nếu thấy đủ).
7. **Lấy thành quả (Collect):**
   ```powershell
   # [SAFE / READ ONLY]
   research-tool export "<COPY_RUN_ID_Ở_MÀN_HÌNH>" --format csv --out ./ket_qua
   ```
8. **Kiểm tra:** Vào thư mục `ket_qua`, mở file CSV bằng Excel và đọc bảng dữ liệu thông minh mà AI đã lấy về.
