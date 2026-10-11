"""Full Desktop GUI for Autonomous Visual Information Explorer."""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import psutil
from pathlib import Path
import subprocess

from research_tool.gui.service import ApplicationService

class ResearchToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Autonomous Research Tool")
        self.root.geometry("800x600")
        
        self.service = ApplicationService()
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- Config Tab ---
        self.config_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.config_frame, text="Cài đặt")
        
        ttk.Label(self.config_frame, text="Mục tiêu (Goal):").grid(row=0, column=0, sticky="w", pady=5)
        self.query_var = tk.StringVar()
        ttk.Entry(self.config_frame, textvariable=self.query_var, width=60).grid(row=0, column=1, columnspan=2, sticky="w", pady=5)
        
        ttk.Label(self.config_frame, text="Nền tảng:").grid(row=1, column=0, sticky="w", pady=5)
        self.platform_var = tk.StringVar(value="windows")
        plat_combo = ttk.Combobox(self.config_frame, textvariable=self.platform_var, values=["windows", "android"], state="readonly", width=15)
        plat_combo.grid(row=1, column=1, sticky="w", pady=5)
        plat_combo.bind("<<ComboboxSelected>>", self._on_platform_change)
        
        ttk.Label(self.config_frame, text="Mô hình (Model):").grid(row=2, column=0, sticky="w", pady=5)
        self.model_var = tk.StringVar(value="qwen2-vl")
        ttk.Combobox(self.config_frame, textvariable=self.model_var, values=["qwen2-vl", "moondream2"], state="readonly", width=15).grid(row=2, column=1, sticky="w", pady=5)
        
        ttk.Label(self.config_frame, text="Thời gian kết thúc (phút, 0=vô hạn):").grid(row=3, column=0, sticky="w", pady=5)
        self.time_var = tk.DoubleVar(value=0.0)
        ttk.Entry(self.config_frame, textvariable=self.time_var, width=10).grid(row=3, column=1, sticky="w", pady=5)
        
        ttk.Label(self.config_frame, text="Thư mục dữ liệu:").grid(row=4, column=0, sticky="w", pady=5)
        self.out_var = tk.StringVar(value="data")
        ttk.Entry(self.config_frame, textvariable=self.out_var, width=40).grid(row=4, column=1, sticky="w", pady=5)
        
        # Android specific
        self.android_frame = ttk.LabelFrame(self.config_frame, text="Tùy chọn Android", padding=5)
        self.android_frame.grid(row=5, column=0, columnspan=3, sticky="we", pady=10)
        
        ttk.Label(self.android_frame, text="ADB Device:").grid(row=0, column=0, sticky="w", pady=2)
        self.adb_var = tk.StringVar()
        self.adb_combo = ttk.Combobox(self.android_frame, textvariable=self.adb_var, state="readonly", width=20)
        self.adb_combo.grid(row=0, column=1, sticky="w", pady=2)
        ttk.Button(self.android_frame, text="Làm mới (Refresh)", command=self._refresh_adb).grid(row=0, column=2, padx=5)
        
        self.scrcpy_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.android_frame, text="Dùng scrcpy stream", variable=self.scrcpy_var).grid(row=1, column=0, columnspan=2, sticky="w")
        
        # Hide Android frame by default
        self.android_frame.grid_remove()
        
        # --- Dashboard Tab ---
        self.dash_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.dash_frame, text="Bảng điều khiển (Dashboard)")
        
        # Controls
        ctrl_frame = ttk.Frame(self.dash_frame)
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.btn_start = ttk.Button(ctrl_frame, text="Bắt đầu", command=self.start_run)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        self.btn_stop = ttk.Button(ctrl_frame, text="Dừng", command=self.stop_run, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        self.btn_emg = ttk.Button(ctrl_frame, text="Dừng khẩn cấp", command=self.emergency_stop, state=tk.DISABLED)
        self.btn_emg.pack(side=tk.LEFT, padx=5)
        self.btn_export = ttk.Button(ctrl_frame, text="Xuất CSV (Export)", command=self.export_csv)
        self.btn_export.pack(side=tk.RIGHT, padx=5)
        
        # Status
        stat_frame = ttk.Frame(self.dash_frame)
        stat_frame.pack(fill=tk.X, pady=10)
        
        self.lbl_status = ttk.Label(stat_frame, text="Trạng thái: CHƯA BẮT ĐẦU", font=("Arial", 12, "bold"))
        self.lbl_status.grid(row=0, column=0, sticky="w", padx=10)
        self.lbl_run = ttk.Label(stat_frame, text="Run ID: N/A")
        self.lbl_run.grid(row=0, column=1, sticky="w", padx=10)
        self.lbl_app = ttk.Label(stat_frame, text="Ứng dụng hiện tại: N/A")
        self.lbl_app.grid(row=1, column=0, columnspan=2, sticky="w", padx=10)
        
        # Metrics
        metric_frame = ttk.Frame(self.dash_frame)
        metric_frame.pack(fill=tk.X, pady=10)
        
        self.lbl_seeds = ttk.Label(metric_frame, text="Seed hiện tại: 0")
        self.lbl_seeds.grid(row=0, column=0, padx=10)
        self.lbl_frontier = ttk.Label(metric_frame, text="Danh sách khám phá: 0")
        self.lbl_frontier.grid(row=0, column=1, padx=10)
        self.lbl_entities = ttk.Label(metric_frame, text="Đối tượng hiện tại: 0")
        self.lbl_entities.grid(row=0, column=2, padx=10)
        self.lbl_evidence = ttk.Label(metric_frame, text="Bằng chứng: 0")
        self.lbl_evidence.grid(row=0, column=3, padx=10)
        
        # Hardware
        hw_frame = ttk.Frame(self.dash_frame)
        hw_frame.pack(fill=tk.X, pady=10)
        self.lbl_hw = ttk.Label(hw_frame, text="CPU: 0% | RAM: 0MB | VRAM: 0MB")
        self.lbl_hw.pack(side=tk.LEFT, padx=10)
        
        # Logs
        ttk.Label(self.dash_frame, text="Logs:").pack(anchor="w")
        self.log_text = tk.Text(self.dash_frame, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.root.after(1000, self._poll_update)

    def _on_platform_change(self, event=None):
        if self.platform_var.get() == "android":
            self.android_frame.grid()
            self._refresh_adb()
        else:
            self.android_frame.grid_remove()

    def _refresh_adb(self):
        try:
            res = subprocess.check_output(["adb", "devices"], text=True)
            devices = []
            for line in res.splitlines()[1:]:
                if "device" in line and "unauthorized" not in line:
                    devices.append(line.split()[0])
            self.adb_combo['values'] = devices
            if devices:
                self.adb_combo.current(0)
        except Exception as e:
            self.log(f"ADB Error: {e}")

    def log(self, msg: str):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_run(self):
        q = self.query_var.get().strip()
        if not q:
            messagebox.showerror("Lỗi", "Vui lòng nhập Mục tiêu.")
            return
            
        p = self.platform_var.get()
        if p == "windows":
            # WARNING
            res = messagebox.askokcancel(
                "CẢNH BÁO: ĐIỀU KHIỂN CHUỘT", 
                "Hệ thống sẽ tự động điều khiển chuột và bàn phím của bạn.\n\n"
                "DỪNG KHẨN CẤP: Hất mạnh con chuột vật lý lên góc trên cùng bên trái (0,0) của màn hình.\n\n"
                "Giao diện sẽ tự động thu nhỏ. Bấm OK để tiếp tục."
            )
            if not res:
                return
            self.root.iconify() # Minimize
            
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_emg.config(state=tk.NORMAL)
        self.notebook.select(self.dash_frame)
        
        self.service.start_run(
            query=q,
            platform=p,
            model=self.model_var.get(),
            time_end_mins=self.time_var.get(),
            out_dir=self.out_var.get(),
            adb_device=self.adb_var.get(),
            use_scrcpy=self.scrcpy_var.get()
        )

    def stop_run(self):
        self.service.stop_run()
        self.log("Đã gửi lệnh Dừng an toàn...")
        self._reset_buttons()

    def emergency_stop(self):
        self.service.emergency_stop()
        self.log("DỪNG KHẨN CẤP ĐÃ KÍCH HOẠT!")
        self._reset_buttons()

    def _reset_buttons(self):
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_emg.config(state=tk.DISABLED)

    def export_csv(self):
        if not self.service.run_id:
            messagebox.showerror("Lỗi", "Chưa có dữ liệu để xuất.")
            return
            
        import sys
        base_dir = Path(__file__).parent.parent.parent.parent
        cli_path = base_dir / "src" / "research_tool" / "cli" / "main.py"
        subprocess.Popen([sys.executable, str(cli_path), "export", self.service.run_id, "--format", "csv"])
        self.log(f"Đã xuất dữ liệu của lần chạy {self.service.run_id} ra file CSV.")

    def _poll_update(self):
        # Update logs
        while not self.service.state_queue.empty():
            msg = self.service.state_queue.get_nowait()
            if "log" in msg:
                self.log(msg["log"])
            if "error" in msg:
                self.log("ERROR: " + msg["error"])
                self._reset_buttons()
                
        # Update UI state
        state = self.service.get_latest_state()
        status = state.get('status', 'CHƯA BẮT ĐẦU')
        if status == 'PAUSED':
            status = 'TẠM DỪNG (HUMAN INTERVENTION REQUIRED)'
            
        self.lbl_status.config(text=f"Trạng thái: {status}")
        self.lbl_run.config(text=f"Run ID: {state.get('run_id', 'N/A')}")
        self.lbl_app.config(text=f"Ứng dụng hiện tại: {state.get('active_app', 'N/A')}")
        
        if state.get('status') in ['DONE', 'FAILED', 'PAUSED'] and self.btn_stop['state'] == tk.NORMAL:
            self._reset_buttons()
            
        if 'seeds' in state:
            self.lbl_seeds.config(text=f"Seed hiện tại: {state['seeds']}")
            self.lbl_frontier.config(text=f"Danh sách khám phá: {state['frontier']}")
            self.lbl_entities.config(text=f"Đối tượng hiện tại: {state['entities']}")
            self.lbl_evidence.config(text=f"Bằng chứng: {state['evidence']}")
            
        # Hardware
        cpu = psutil.cpu_percent()
        ram = psutil.Process().memory_info().rss / (1024*1024)
        vram_str = "0MB"
        try:
            import torch
            if torch.cuda.is_available():
                vram = torch.cuda.memory_allocated() / (1024*1024)
                vram_str = f"{vram:.0f}MB"
        except:
            pass
            
        self.lbl_hw.config(text=f"CPU: {cpu}% | RAM: {ram:.0f}MB | VRAM: {vram_str}")
        
        self.root.after(1000, self._poll_update)

import re
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

class TextRedirector:
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str_data):
        self.widget.after(0, self._insert, str_data)

    def _insert(self, str_data):
        clean_str = ANSI_ESCAPE.sub('', str_data)
        self.widget.config(state=tk.NORMAL)
        self.widget.insert(tk.END, clean_str)
        self.widget.see(tk.END)
        self.widget.config(state=tk.DISABLED)

    def flush(self):
        pass

def launch_gui():
    root = tk.Tk()
    app = ResearchToolGUI(root)
    import sys
    sys.stdout = TextRedirector(app.log_text, "stdout")
    sys.stderr = TextRedirector(app.log_text, "stderr")
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
