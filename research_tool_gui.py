import sys
from pathlib import Path

# Thêm thư mục 'src' vào sys.path để Python có thể tìm thấy module 'research_tool'
# ngay cả khi chạy script từ một thư mục khác mà chưa cài đặt qua pip.
project_root = Path(__file__).parent.resolve()
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from research_tool.gui.app import launch_gui

if __name__ == "__main__":
    launch_gui()
