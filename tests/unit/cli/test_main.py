import pytest
from typer.testing import CliRunner
from unittest.mock import patch
from research_tool.cli.main import app

runner = CliRunner()

@patch("research_tool.cli.main._async_run")
def test_run_command_invokes_async_run(mock_async_run):
    """Test that the 'run' command calls _async_run with the query."""
    result = runner.invoke(app, ["test query"])
    
    assert result.exit_code == 0
    assert "Starting session with query" in result.stdout
    assert "test query" in result.stdout
    
    mock_async_run.assert_called_once_with("test query", None)

@patch("research_tool.cli.main._async_run")
def test_run_command_with_config(mock_async_run):
    """Test that the 'run' command handles a config path."""
    from pathlib import Path
    
    result = runner.invoke(app, ["test query", "--config", "custom.yaml"])
    
    assert result.exit_code == 0
    mock_async_run.assert_called_once_with("test query", Path("custom.yaml"))
