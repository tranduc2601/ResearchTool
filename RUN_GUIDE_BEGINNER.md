# Hướng Dẫn Sử Dụng Dành Cho Người Mới Bắt Đầu (Beginner Run Guide)

Chào mừng bạn đến với **ResearchTool**! Đây là một hệ thống AI tự động hóa (Agent) có khả năng "nhìn" vào màn hình của bạn và tự động di chuyển chuột, gõ phím, hoặc lướt điện thoại Android để tìm kiếm thông tin theo yêu cầu.

Tài liệu này được viết dành riêng cho người mới bắt đầu, không yêu cầu kiến thức lập trình trước đó. Hãy đọc kỹ từng bước để hiểu Agent đang làm gì, cách kiểm soát nó, và tránh việc nó click nhầm vào các dữ liệu quan trọng của bạn.

---

## 1. Mở PowerShell và Truy Cập Dự Án

**Bước này làm gì:** Khởi động dòng lệnh (PowerShell) và di chuyển vào thư mục chứa mã nguồn của dự án trên máy tính của bạn.

**Lệnh PowerShell:**
```powershell
# [SAFE / read-only]
cd "D:\OneDrive\Máy tính\ResearchTool"
```
* **Kỳ vọng (Thành công):** Dòng lệnh của bạn sẽ đổi thành `PS D:\OneDrive\Máy tính\ResearchTool>`.
* **Thất bại:** Báo lỗi "Cannot find path". Hãy kiểm tra lại thư mục có thực sự nằm ở ổ D không.

---

## 2. Kích Hoạt Môi Trường Ảo (.venv)

**Bước này làm gì:** Bật môi trường Python cô lập của dự án để sử dụng đúng các thư viện đã được cài đặt riêng cho công cụ này.

**Lệnh PowerShell:**
```powershell
# [SAFE / read-only]
.\.venv\Scripts\Activate.ps1
```
* **Kỳ vọng:** Bạn sẽ thấy chữ `(.venv)` xuất hiện ở đầu dòng lệnh màu xanh lá cây.
* **Thất bại:** Nếu PowerShell báo lỗi "cannot be loaded because running scripts is disabled", hãy chạy lệnh `Set-ExecutionPolicy Unrestricted -Scope CurrentUser` trước, rồi thử lại.

---

## 3. Kiểm Tra Python, PyTorch, CUDA và Card Đồ Họa (GPU)

**Bước này làm gì:** Đảm bảo hệ thống AI có thể nhận diện được card màn hình NVIDIA RTX 3050 Ti của bạn để chạy mô hình thị giác (Vision) mà không bị treo máy.

**Lệnh PowerShell:**
```powershell
# [SAFE / read-only]
python -c "import torch; print('CUDA Hợp lệ:', torch.cuda.is_available()); print('Card Đồ Họa:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Không tìm thấy')"
```
* **Kỳ vọng:** In ra `CUDA Hợp lệ: True` và `Card Đồ Họa: NVIDIA GeForce RTX 3050 Ti Laptop GPU`.
* **Thất bại:** In ra `CUDA Hợp lệ: False`. *Dừng lại ngay và báo cáo lỗi*, vì Agent sẽ chạy cực kỳ chậm nếu dùng CPU.

---

## 4. Hiểu Cấu Trúc Các Thư Mục Quan Trọng

Trước khi chạy, hãy hiểu các thành phần của ứng dụng (bạn không cần chạy lệnh ở phần này):
* `src/research_tool/`: Bộ não của Agent (chứa mã nguồn logic, cách Agent "suy nghĩ" và "hành động").
* `scripts/`: Chứa các bài kiểm tra an toàn (benchmark) để bạn thử nghiệm trước khi chạy thật.
* `data/`: Nơi Agent lưu trữ *mọi thứ* nó tìm thấy. Gồm:
  * `research.db`: Cơ sở dữ liệu chính (SQLite) lưu danh sách các nơi đã xem, thông tin lấy được.
  * `screenshots/`: Thư mục lưu ảnh chụp màn hình mỗi khi Agent click hoặc cuộn.
* `logs/` (nếu có): Nơi chứa các file ghi chép (nhật ký) để biết Agent bị lỗi ở đâu.

---

## 5. Bài Kiểm Tra Đầu Tiên (Cực Kỳ An Toàn)

**Bước này làm gì:** Agent sẽ tải mô hình thị giác (Qwen2-VL) vào Card đồ họa (VRAM) của bạn và nhìn vào một bức ảnh giả (dummy) để tập phân tích. Lệnh này KHÔNG di chuyển chuột, KHÔNG click, và KHÔNG ảnh hưởng gì đến máy bạn.

**Lệnh PowerShell:**
```powershell
# [SAFE / read-only]
python scripts\validation\benchmark_stability.py --model qwen2-vl --iters 1
```
* **Kỳ vọng:** Nó sẽ tải các "cục tạ" (weights) của AI từ 0% đến 100%. Sau khoảng 10-20 giây, nó sẽ in ra thời gian phản hồi (Latency) khoảng 6-8 giây và VRAM Usage khoảng ~1.55 GB.
* **Thất bại:** Báo lỗi "Out of Memory" (Hết VRAM) hoặc văng chương trình. *Nếu lỗi, hãy dừng lại và báo cáo.*

---

## 6. Chạy Ứng Dụng Qua Giao Diện Hình Ảnh (Tkinter GUI)

**Bước này làm gì:** Thay vì gõ lệnh dài dòng, bạn có thể dùng một cửa sổ giao diện nhỏ cực kỳ dễ dùng mà tôi đã tạo sẵn.

**Lệnh PowerShell:**
```powershell
# [SAFE / read-only]
python src\research_tool\gui\app.py
```
* **Kỳ vọng:** Một cửa sổ phần mềm nhỏ tên "Autonomous Research Tool" hiện lên. Bạn có thể nhập mục tiêu (Goal), chọn nền tảng (`windows` hoặc `android`), và chọn mô hình (`qwen2-vl`). Bạn có thể tắt nó đi sau khi xem thử.

---

## 7. Bài Kiểm Tra Đóng Vòng Trên Windows (Dùng Chuột/Phím Thật)

**Bước này làm gì:** Agent sẽ được trao quyền ĐIỀU KHIỂN CHUỘT VÀ BÀN PHÍM. 
**LƯU Ý:** Hãy mở một cửa sổ trình duyệt (ví dụ: Google hoặc Shopee) an toàn và để nó toàn màn hình. Thu nhỏ mọi tài liệu cá nhân. *Không chạm vào chuột khi nó đang chạy.*

**Lệnh PowerShell:**
```powershell
# [MAY MOVE MOUSE] [MAY CLICK/TYPE]
python scripts\run_acceptance.py
```
* **Kỳ vọng:** Chuột của bạn sẽ *tự động* di chuyển. Agent chụp màn hình, phân tích, rồi click vào các nút hoặc thanh tìm kiếm, và có thể cuộn trang (scroll). Sau vài bước, nó sẽ tự báo `GOAL_MET` (Đạt mục tiêu) hoặc `HUMAN_REQUIRED` (Cần con người giúp) và tự dừng lại.
* **Thất bại:** Agent click lung tung vào các nút nguy hiểm.
* **CÁCH DỪNG KHẨN CẤP:** Di chuyển chuột thật mạnh về **Góc trên cùng bên trái của màn hình (Tọa độ 0,0)**. Chức năng Failsafe của Windows sẽ lập tức ngắt Agent. Hoặc bấm `Ctrl + C` ở cửa sổ PowerShell.

---

## 8. Chuẩn Bị & Kiểm Tra Android (Điện thoại iQOO Z10 Turbo+)

**Bước này làm gì:** Kiểm tra xem máy tính có nhận diện được điện thoại của bạn qua cáp USB không.

**Thao tác chuẩn bị (Không cần PowerShell):**
1. Cắm cáp USB nối điện thoại với máy tính.
2. Trên điện thoại, vào Cài đặt -> Tùy chọn nhà phát triển -> Bật **"Gỡ lỗi USB" (USB Debugging)**.
3. Khi điện thoại hiện bảng hỏi "Cho phép gỡ lỗi USB từ máy tính này?", chọn **Đồng ý / OK**.

**Lệnh PowerShell kiểm tra:**
```powershell
# [SAFE / read-only]
adb devices
```
* **Kỳ vọng:** Bạn sẽ thấy danh sách thiết bị có 1 dòng chứa mã số thiết bị kèm chữ `device` (VD: `12345abcd device`).
* **Thất bại:** Hiện chữ `unauthorized` (chưa bấm Đồng ý trên điện thoại) hoặc trống trơn (lỗi cáp/chưa bật gỡ lỗi). *Chỉ đi tiếp khi đã hiện chữ `device`.*

---

## 9. Chạy Thử Trên Android (ADB / Scrcpy)

**Bước này làm gì:** Agent sẽ không đụng vào chuột máy tính nữa, mà sẽ "nhìn" vào màn hình điện thoại của bạn và tự động vuốt/chạm trên điện thoại để tìm thông tin.

**Lệnh PowerShell:**
```powershell
# [MAY CONTROL ANDROID] [LONG-RUNNING]
research-tool run "Tìm giá điện thoại rẻ nhất trên màn hình" --platform android
```
* **Kỳ vọng:** Màn hình điện thoại của bạn sẽ tự động cuộn (vuốt) hoặc tự động mở các nút bấm. Trên PowerShell (TUI), bạn sẽ thấy Agent đang suy luận.
* **Cách dừng khẩn cấp:** Bấm `Ctrl + C` trên bàn phím máy tính ở cửa sổ PowerShell. Hoặc đơn giản là rút cáp USB điện thoại ra.

---

## 10. Cách Quản Lý Quá Trình Chạy (CLI & TUI)

Khi bạn chạy lệnh `research-tool run ...`, màn hình (TUI - Terminal User Interface) sẽ hiện ra một bảng điều khiển động.
* **Agent đang làm gì?** Bạn sẽ thấy trạng thái: `THINKING` (Đang phân tích ảnh), `ACTING` (Đang click chuột/cuộn trang), hoặc `WAITING` (Chờ tải trang).
* **Dừng an toàn:** Bấm phím `Ctrl + C` trên bàn phím. Cấu trúc lưu trữ SQLite rất an toàn nên bạn không lo mất dữ liệu giữa chừng.
* **Khôi phục phiên chạy cũ (Resume):** Khi chạy, Agent tạo ra một mã `RUN_ID` (VD: `01HGF...`). Nếu bạn lỡ tắt máy, hãy chạy lệnh sau để làm tiếp:
```powershell
# [MAY MOVE MOUSE]
research-tool run "tiếp tục việc cũ" --resume "MÃ_RUN_ID_CỦA_BẠN"
```

---

## 11. Trích Xuất (Export) Kết Quả Để Xem Dữ Liệu

**Bước này làm gì:** Lấy toàn bộ thông tin mà Agent thu thập được (Tên sản phẩm, giá cả, cấu hình) và xuất ra file Excel (CSV) để bạn dễ đọc. Lệnh này tuyệt đối an toàn.

**Lệnh PowerShell:**
```powershell
# [SAFE / read-only]
research-tool export "MÃ_RUN_ID_CỦA_BẠN" --format csv --out "D:\OneDrive\Máy tính\ResearchTool\results"
```
* **Kỳ vọng:** Báo "Exported 4 tables...". Bạn vào thư mục `results` vừa tạo và mở các file `.csv` bằng Excel để xem thành quả.

---

## 12. Trình Tự Chạy Khuyến Nghị Dành Riêng Cho Máy Bạn
**(Ryzen 5, 3050 Ti 4GB, 16GB RAM, Windows + iQOO Z10)**

Tôi khuyên bạn làm theo đúng thứ tự sau trong lần đầu trải nghiệm:

1. Mở PowerShell, vào thư mục và gõ `.\.venv\Scripts\Activate.ps1`.
2. Gõ `python scripts\validation\benchmark_stability.py --model qwen2-vl --iters 1` để đo thử VRAM. *Hãy tự tin vì máy bạn có 4GB VRAM, mô hình Qwen2-VL chỉ tốn khoảng 1.55 GB!*
3. Gõ `python src\research_tool\gui\app.py` để mở giao diện cửa sổ nhỏ. 
4. Tại giao diện cửa sổ nhỏ (GUI), nhập "Tìm tin tức công nghệ mới", chọn `windows`, và bấm **Start Exploration**.
5. Bỏ tay ra khỏi chuột và nhìn nó tự hoạt động khoảng 1-2 phút, sau đó bấm `Ctrl + C` ở cửa sổ CMD phía sau để dừng nó lại.
6. (Tùy chọn) Cắm iQOO Z10 vào, mở khóa màn hình, xác nhận `adb devices` thành công, rồi gõ lệnh ở Bước 9 để xem nó điều khiển điện thoại.
7. Khi đã quen, bạn có thể treo máy (LONG-RUNNING) qua đêm để Agent tự đi săn dữ liệu! 

**Chúc bạn thành công với Autonomous Visual Information Explorer!**
