#!/usr/bin/env python3
"""
CLI Markdown Integration Test.

Tests that the CLI can compile Markdown files with YAML Front-Matter directly.
"""

import subprocess
import sys
from pathlib import Path


def test_cli_markdown_compilation():
    """Test that CLI can compile a Markdown file with YAML Front-Matter."""
    project_root = Path(__file__).parent.parent
    input_md = project_root / "tests" / "input" / "test_cli_markdown.md"
    output_docx = project_root / "tests" / "output" / "test_cli_markdown.docx"
    
    # Ensure output directory exists
    output_docx.parent.mkdir(parents=True, exist_ok=True)
    
    # Clean up any existing output
    if output_docx.exists():
        output_docx.unlink()
    
    # Run CLI command
    cmd = [
        sys.executable,
        "-m",
        "src.main",
        str(input_md),
        "--output",
        str(output_docx),
    ]
    
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    
    # Assert success
    assert result.returncode == 0, f"CLI failed with return code {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    
    # Verify output file exists and has content
    assert output_docx.exists(), f"Output file not created: {output_docx}"
    file_size = output_docx.stat().st_size
    assert file_size > 0, "Output file is empty"
    
    # Clean up
    output_docx.unlink()
    
    print(f"✓ CLI Markdown compilation test passed")
    print(f"  Input: {input_md}")
    print(f"  Output: {output_docx} ({file_size} bytes)")


if __name__ == "__main__":
    test_cli_markdown_compilation()
