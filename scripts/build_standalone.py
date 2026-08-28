"""PyInstaller build script."""
import PyInstaller.__main__
from pathlib import Path

def build():
    # Base directory
    base_dir = Path(__file__).parent.parent.absolute()
    main_script = base_dir / "research_tool_gui.py"
    
    # Run PyInstaller
    PyInstaller.__main__.run([
        str(main_script),
        '--name=ResearchTool',
        '--windowed',
        '--onefile',
        '--clean',
        '--paths=' + str(base_dir / "src"),
        '--hidden-import=pydantic',
        '--hidden-import=structlog',
        '--hidden-import=rich',
        '--hidden-import=sqlite3',
        # Optionally omit heavy local ML dependencies from onefile if we intend to load them externally
        '--exclude-module=torch',
        '--exclude-module=transformers',
        '--exclude-module=paddleocr',
    ])

if __name__ == "__main__":
    build()
