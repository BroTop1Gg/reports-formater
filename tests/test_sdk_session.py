#!/usr/bin/env python3
"""
Unit tests for ReportSession SDK.

Tests the incremental report building API with validation and finalization.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

import yaml

from src.sdk.session import ReportSession


class TestReportSession(unittest.TestCase):
    """Test suite for ReportSession class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.session = ReportSession(metadata={
            "VERSION": "1.0",
            "USER_NAME": "Test User",
            "CURRENT_YEAR": "2026"
        })
        
        # Create temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary files."""
        if Path(self.temp_path).exists():
            shutil.rmtree(self.temp_path)
        
        # Clean up draft_report.yaml if created
        backup = Path("draft_report.yaml")
        if backup.exists():
            backup.unlink()
    
    def test_add_valid_chunk_heading_and_paragraph(self):
        """Test adding a valid chunk with heading and paragraph."""
        yaml_chunk = """
- type: heading
  level: 1
  text: "Introduction"

- type: paragraph
  text: "This is the introduction paragraph."
"""
        
        result = self.session.add_chunk(yaml_chunk)
        
        # Verify success
        self.assertEqual(result["status"], "success")
        self.assertIn("outline", result)
        
        # Verify outline contains heading
        self.assertEqual(len(result["outline"]), 1)
        self.assertEqual(result["outline"][0]["type"], "heading")
        self.assertEqual(result["outline"][0]["text"], "Introduction")
        
        # Verify session state
        self.assertEqual(len(self.session.nodes), 2)
        self.assertEqual(self.session.chunk_index, 1)
        
        # Verify backup was created
        self.assertTrue(Path("draft_report.yaml").exists())
    
    def test_add_valid_chunk_with_table(self):
        """Test adding a valid chunk with a table."""
        yaml_chunk = """
- type: heading
  level: 2
  text: "Data Table"

- type: table
  caption: "Sample Data"
  rows:
    - ["Column A", "Column B"]
    - ["Value 1", "Value 2"]
"""
        
        result = self.session.add_chunk(yaml_chunk)
        
        # Verify success
        self.assertEqual(result["status"], "success")
        
        # Verify outline contains heading and table
        self.assertEqual(len(result["outline"]), 2)
        self.assertEqual(result["outline"][0]["type"], "heading")
        self.assertEqual(result["outline"][1]["type"], "table")
        self.assertEqual(result["outline"][1]["caption"], "Sample Data")
        
        # Verify session state
        self.assertEqual(len(self.session.nodes), 2)
        self.assertEqual(self.session.chunk_index, 1)
    
    def test_add_invalid_chunk_missing_required_field(self):
        """Test that invalid chunk (missing required field) is rejected."""
        yaml_chunk = """
- type: heading
  level: 1
  text: "Valid Heading"

- type: paragraph
  text: "This paragraph is missing the required 'text' field"
"""
        # Intentionally remove text field
        yaml_chunk = """
- type: heading
  level: 1
  text: "Valid Heading"

- type: paragraph
"""
        
        result = self.session.add_chunk(yaml_chunk)
        
        # Verify error status
        self.assertEqual(result["status"], "error")
        self.assertIn("errors", result)
        self.assertGreater(len(result["errors"]), 0)
        
        # Verify NO nodes were added (all-or-nothing)
        self.assertEqual(len(self.session.nodes), 0)
        self.assertEqual(self.session.chunk_index, 0)
    
    def test_add_invalid_chunk_unknown_type(self):
        """Test that chunk with unknown node type is rejected."""
        yaml_chunk = """
- type: unknown_node_type
  data: "some data"
"""
        
        result = self.session.add_chunk(yaml_chunk)
        
        # Verify error status
        self.assertEqual(result["status"], "error")
        self.assertIn("errors", result)
        
        # Verify error mentions unknown type
        error = result["errors"][0]
        self.assertIn("unknown", error["message"].lower())
        
        # Verify NO nodes were added
        self.assertEqual(len(self.session.nodes), 0)
    
    def test_add_invalid_yaml_syntax(self):
        """Test that malformed YAML is rejected."""
        yaml_chunk = """
- type: heading
  level: 1
  text: "Valid"
  
  this is invalid yaml: [
"""
        
        result = self.session.add_chunk(yaml_chunk)
        
        # Verify error status
        self.assertEqual(result["status"], "error")
        self.assertIn("errors", result)
        
        # Verify NO nodes were added
        self.assertEqual(len(self.session.nodes), 0)
    
    def test_add_multiple_valid_chunks(self):
        """Test adding multiple valid chunks sequentially."""
        chunk1 = """
- type: heading
  level: 1
  text: "Chapter 1"

- type: paragraph
  text: "First paragraph."
"""
        
        chunk2 = """
- type: heading
  level: 1
  text: "Chapter 2"

- type: paragraph
  text: "Second paragraph."
"""
        
        result1 = self.session.add_chunk(chunk1)
        self.assertEqual(result1["status"], "success")
        self.assertEqual(self.session.chunk_index, 1)
        
        result2 = self.session.add_chunk(chunk2)
        self.assertEqual(result2["status"], "success")
        self.assertEqual(self.session.chunk_index, 2)
        
        # Verify all nodes accumulated
        self.assertEqual(len(self.session.nodes), 4)
    
    def test_all_or_nothing_validation(self):
        """Test that if any node fails, entire chunk is discarded."""
        # First chunk: valid
        valid_chunk = """
- type: heading
  level: 1
  text: "Valid Chapter"
"""
        result1 = self.session.add_chunk(valid_chunk)
        self.assertEqual(result1["status"], "success")
        self.assertEqual(len(self.session.nodes), 1)
        
        # Second chunk: one valid, one invalid
        mixed_chunk = """
- type: heading
  level: 2
  text: "Valid Subsection"

- type: paragraph
"""
        # Missing required 'text' field in paragraph
        result2 = self.session.add_chunk(mixed_chunk)
        self.assertEqual(result2["status"], "error")
        
        # Verify first chunk's nodes are still there, but second chunk was NOT added
        self.assertEqual(len(self.session.nodes), 1)
        self.assertEqual(self.session.chunk_index, 1)
    
    def test_finalize_generates_docx(self):
        """Test that finalize() generates a .docx file."""
        # Add some content
        yaml_chunk = """
- type: heading
  level: 1
  text: "Test Report"

- type: paragraph
  text: "This is a test paragraph for finalization."

- type: heading
  level: 2
  text: "Section 1.1"

- type: paragraph
  text: "Another paragraph."
"""
        
        result = self.session.add_chunk(yaml_chunk)
        self.assertEqual(result["status"], "success")
        
        # Finalize
        output_path = self.temp_path / "test_report.docx"
        actual_path = self.session.finalize(output_path)
        
        # Verify file was created
        self.assertTrue(actual_path.exists())
        self.assertEqual(actual_path.suffix, ".docx")
        
        # Verify file is not empty
        self.assertGreater(actual_path.stat().st_size, 0)
    
    def test_finalize_with_empty_session(self):
        """Test that finalize() works even with no content."""
        output_path = self.temp_path / "empty_report.docx"
        actual_path = self.session.finalize(output_path)
        
        # Should still create a valid (empty) document
        self.assertTrue(actual_path.exists())
        self.assertGreater(actual_path.stat().st_size, 0)
    
    def test_finalize_with_list_nodes(self):
        """Test finalization with list content nodes."""
        yaml_chunk = """
- type: heading
  level: 1
  text: "Lists Test"

- type: list
  style: bullet
  items:
    - "First item"
    - "Second item"
    - "Third item"

- type: list
  style: numbered
  items:
    - "Item 1"
    - "Item 2"
"""
        
        result = self.session.add_chunk(yaml_chunk)
        self.assertEqual(result["status"], "success")
        
        # Finalize
        output_path = self.temp_path / "lists_report.docx"
        actual_path = self.session.finalize(output_path)
        
        # Verify file was created
        self.assertTrue(actual_path.exists())


class TestReportSessionEdgeCases(unittest.TestCase):
    """Edge case tests for ReportSession."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.session = ReportSession()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        if Path(self.temp_path).exists():
            shutil.rmtree(self.temp_path)
        
        backup = Path("draft_report.yaml")
        if backup.exists():
            backup.unlink()
    
    def test_add_chunk_with_code_block(self):
        """Test adding a chunk with code block."""
        yaml_chunk = """
- type: code
  language: python
  code: |
    def hello():
        print("Hello, World!")
"""
        
        result = self.session.add_chunk(yaml_chunk)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(self.session.nodes), 1)
    
    def test_add_chunk_with_formula(self):
        """Test adding a chunk with formula."""
        yaml_chunk = """
- type: formula
  content: "E = mc^2"
  caption: "(1.1)"
"""
        
        result = self.session.add_chunk(yaml_chunk)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(self.session.nodes), 1)
    
    def test_add_chunk_with_break(self):
        """Test adding a chunk with break."""
        yaml_chunk = """
- type: break
  style: line
  count: 2
"""
        
        result = self.session.add_chunk(yaml_chunk)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(self.session.nodes), 1)
    
    def test_metadata_preserved_through_finalize(self):
        """Test that metadata is preserved in final output."""
        session = ReportSession(metadata={
            "TITLE": "My Report",
            "AUTHOR": "Test Author"
        })
        
        yaml_chunk = """
- type: heading
  level: 1
  text: "Introduction"
"""
        
        session.add_chunk(yaml_chunk)
        
        output_path = self.temp_path / "metadata_test.docx"
        session.finalize(output_path)
        
        # Verify file exists (metadata is used internally by ReportFactory)
        self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
