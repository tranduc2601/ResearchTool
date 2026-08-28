"""Minimal Desktop GUI for Autonomous Visual Information Explorer."""
import tkinter as tk
from tkinter import ttk
import threading
import asyncio
from pathlib import Path

# Note: In a production app, we would import the CLI/Core orchestrator here and run it.
# We keep it decoupled here so it can launch the Typer app in a subprocess or a separate thread.

class ResearchToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Autonomous Research Tool")
        self.root.geometry("600x400")
        
        # Query Frame
        q_frame = ttk.Frame(root, padding="10")
        q_frame.pack(fill=tk.X)
        
        ttk.Label(q_frame, text="Goal/Query:").pack(side=tk.LEFT)
        self.query_var = tk.StringVar()
        self.query_entry = ttk.Entry(q_frame, textvariable=self.query_var, width=50)
        self.query_entry.pack(side=tk.LEFT, padx=5)
        
        # Options Frame
        opt_frame = ttk.Frame(root, padding="10")
        opt_frame.pack(fill=tk.X)
        
        ttk.Label(opt_frame, text="Platform:").pack(side=tk.LEFT)
        self.platform_var = tk.StringVar(value="windows")
        ttk.Combobox(opt_frame, textvariable=self.platform_var, values=["windows", "android"], state="readonly", width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(opt_frame, text="Model:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value="qwen2-vl")
        ttk.Combobox(opt_frame, textvariable=self.model_var, values=["qwen2-vl", "moondream2"], state="readonly", width=10).pack(side=tk.LEFT, padx=5)
        
        # Start Button
        self.start_btn = ttk.Button(root, text="Start Exploration", command=self.start_run)
        self.start_btn.pack(pady=10)
        
        # Log Output
        self.log_text = tk.Text(root, height=15, width=70, state=tk.DISABLED)
        self.log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def log(self, message: str):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_run(self):
        query = self.query_var.get().strip()
        if not query:
            self.log("Error: Query cannot be empty.")
            return
            
        self.start_btn.config(state=tk.DISABLED)
        self.log(f"Starting run for: {query} on {self.platform_var.get()}")
        
        # Launch in background thread to not block GUI
        threading.Thread(target=self._run_async, args=(query, self.platform_var.get(), self.model_var.get()), daemon=True).start()

    def _run_async(self, query: str, platform: str, model: str):
        import subprocess
        import sys
        
        # We invoke the CLI so we don't have to duplicate the asyncio event loop logic
        base_dir = Path(__file__).parent.parent.parent.parent
        cli_path = base_dir / "src" / "research_tool" / "cli" / "main.py"
        
        cmd = [sys.executable, str(cli_path), "run", query, "--platform", platform, "--model", model]
        
        self.log(f"Executing: {' '.join(cmd)}")
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                self.root.after(0, self.log, line.strip())
                
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.log("Run finished."))

def launch_gui():
    root = tk.Tk()
    app = ResearchToolGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
