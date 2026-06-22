#!/usr/bin/env python3
"""
Markdown Visual Compilation Tests.

Tests that all Markdown test files can be compiled to .docx format
for visual inspection. This ensures Markdown transpiler works correctly
and produces valid output that can be manually verified.
"""

import subprocess
import sys
from pathlib import Path
import pytest


def compile_markdown_to_docx(input_md: Path, output_docx: Path, project_root: Path) -> tuple[int, str, str]:
    """
    Compile a Markdown file to DOCX using CLI.
    
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
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
    
    return result.returncode, result.stdout, result.stderr


def test_markdown_with_title_compilation():
    """Test compilation of test_with_title.md (WITH title page, WITH numbering)."""
    project_root = Path(__file__).parent.parent
    input_md = project_root / "tests" / "input" / "test_with_title.md"
    output_docx = project_root / "tests" / "output" / "test_with_title.docx"
    
    output_docx.parent.mkdir(parents=True, exist_ok=True)
    
    if output_docx.exists():
        output_docx.unlink()
    
    returncode, stdout, stderr = compile_markdown_to_docx(input_md, output_docx, project_root)
    
    assert returncode == 0, f"CLI failed with return code {returncode}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
    assert output_docx.exists(), f"Output file not created: {output_docx}"
    file_size = output_docx.stat().st_size
    assert file_size > 0, "Output file is empty"
    
    print(f"✓ test_with_title.md -> {output_docx} ({file_size} bytes)")


def test_markdown_without_title_compilation():
    """Test compilation of test_without_title.md (NO title page, WITH numbering)."""
    project_root = Path(__file__).parent.parent
    input_md = project_root / "tests" / "input" / "test_without_title.md"
    output_docx = project_root / "tests" / "output" / "test_without_title.docx"
    
    output_docx.parent.mkdir(parents=True, exist_ok=True)
    
    if output_docx.exists():
        output_docx.unlink()
    
    returncode, stdout, stderr = compile_markdown_to_docx(input_md, output_docx, project_root)
    
    assert returncode == 0, f"CLI failed with return code {returncode}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
    assert output_docx.exists(), f"Output file not created: {output_docx}"
    file_size = output_docx.stat().st_size
    assert file_size > 0, "Output file is empty"
    
    print(f"✓ test_without_title.md -> {output_docx} ({file_size} bytes)")


def test_markdown_title_and_numbering_compilation():
    """Test compilation of test_title_and_numbering.md (WITH title page, WITH numbering skip first)."""
    project_root = Path(__file__).parent.parent
    input_md = project_root / "tests" / "input" / "test_title_and_numbering.md"
    output_docx = project_root / "tests" / "output" / "test_title_and_numbering.docx"
    
    output_docx.parent.mkdir(parents=True, exist_ok=True)
    
    if output_docx.exists():
        output_docx.unlink()
    
    returncode, stdout, stderr = compile_markdown_to_docx(input_md, output_docx, project_root)
    
    assert returncode == 0, f"CLI failed with return code {returncode}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
    assert output_docx.exists(), f"Output file not created: {output_docx}"
    file_size = output_docx.stat().st_size
    assert file_size > 0, "Output file is empty"
    
    print(f"✓ test_title_and_numbering.md -> {output_docx} ({file_size} bytes)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
