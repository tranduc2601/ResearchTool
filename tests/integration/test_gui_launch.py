import subprocess
import os
import sys
from pathlib import Path

def test_gui_initialization_from_different_cwd(tmp_path):
    """
    Test that the GUI service can initialize its paths correctly even if launched
    from a completely different working directory (e.g. C:\\Windows\\System32 or a temp dir).
    """
    # Project root
    project_root = Path(__file__).parent.parent.parent.resolve()
    script_path = project_root / "research_tool_gui.py"
    
    # We will run a python one-liner from the tmp_path that imports the service
    # and checks the loaded settings data_dir
    
    python_code = f"""
import sys
sys.path.insert(0, r"{project_root / 'src'}")
from research_tool.gui.service import ApplicationService
s = ApplicationService()
s.settings = __import__("research_tool.config.settings", fromlist=["load_settings"]).load_settings()
print(s.settings.data_dir)
    """
    
    # Write the script to the temp dir
    test_script = tmp_path / "test_init.py"
    test_script.write_text(python_code, encoding="utf-8")
    
    # Run the script with the current python executable (which is in the venv)
    # The CWD is tmp_path
    result = subprocess.run(
        [sys.executable, str(test_script)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed with: {result.stderr}"
    
    # The output should contain the absolute path to the project data directory,
    # NOT the tmp_path/data
    output_path = result.stdout.strip()
    expected_path = str(project_root / "data")
    
    assert expected_path in output_path
