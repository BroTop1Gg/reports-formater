#!/usr/bin/env python3
"""
Self-Healing Simulation Test.

Verifies that the Gateway's validation layer returns clean diagnostic payloads
and that LLM-driven self-correction can recover from validation errors.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

import yaml

from src.sdk.session import ReportSession


class TestSelfHealingSimulation(unittest.TestCase):
    """
    Verify that validation errors are caught, reported cleanly, and that
    the session can recover after correction.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary files."""
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
        
        # Clean up draft_report.yaml if created
        backup = Path("draft_report.yaml")
        if backup.exists():
            backup.unlink()

    def test_validation_error_returns_clean_diagnostic(self):
        """
        Verify that malformed chunks return structured error payloads
        without crashing the session.
        """
        session = ReportSession(metadata={"VERSION": "1.0"})

        # 1. Send valid heading chunk
        valid_chunk = """
- type: heading
  level: 1
  text: "Introduction"
"""
        result1 = session.add_chunk(valid_chunk)
        self.assertEqual(result1["status"], "success")
        self.assertEqual(len(session.nodes), 1)

        # 2. Send malformed chunk (heading missing required 'text' field)
        malformed_chunk = """
- type: heading
  level: 2
"""
        result2 = session.add_chunk(malformed_chunk)

        # 3. Verify error status and clean diagnostic
        self.assertEqual(result2["status"], "error")
        self.assertIn("errors", result2)
        self.assertGreater(len(result2["errors"]), 0)

        # 4. Verify error structure contains expected fields
        error = result2["errors"][0]
        self.assertIn("type", error)
        self.assertIn("message", error)

        # 5. Verify session state remains untouched (no partial corruption)
        self.assertEqual(len(session.nodes), 1, "Session nodes should remain unchanged after error")
        self.assertEqual(session.chunk_index, 1, "Chunk index should not increment on error")

    def test_self_healing_recovery_after_correction(self):
        """
        Verify that after receiving a validation error, the client can
        correct the payload and successfully resubmit.
        """
        session = ReportSession(metadata={"VERSION": "1.0"})

        # 1. Send valid heading
        valid_heading = """
- type: heading
  level: 1
  text: "Chapter 1"
"""
        result1 = session.add_chunk(valid_heading)
        self.assertEqual(result1["status"], "success")

        # 2. Send malformed paragraph (missing 'text' field)
        malformed_paragraph = """
- type: paragraph
"""
        result2 = session.add_chunk(malformed_paragraph)
        self.assertEqual(result2["status"], "error")

        # 3. Verify session state unchanged
        self.assertEqual(len(session.nodes), 1)

        # 4. "Self-heal": correct the payload by adding the missing field
        corrected_paragraph = """
- type: paragraph
  text: "This is the corrected paragraph with the required text field."
"""
        result3 = session.add_chunk(corrected_paragraph)

        # 5. Verify successful acceptance after correction
        self.assertEqual(result3["status"], "success")
        self.assertEqual(len(session.nodes), 2, "Session should now have 2 nodes")

        # 6. Finalize and verify document compiles
        output_path = self.temp_path / "healed_report.docx"
        actual_path = session.finalize(output_path)
        self.assertTrue(actual_path.exists())
        self.assertGreater(actual_path.stat().st_size, 0)

    def test_multiple_errors_in_single_chunk(self):
        """
        Verify that when multiple nodes in a chunk fail validation,
        all errors are reported (not just the first).
        """
        session = ReportSession(metadata={"VERSION": "1.0"})

        # Chunk with multiple invalid nodes
        multi_error_chunk = """
- type: paragraph
  # Missing 'text' field

- type: heading
  # Missing 'text' field

- type: unknown_type
  data: "invalid"
"""
        result = session.add_chunk(multi_error_chunk)

        # Verify error status
        self.assertEqual(result["status"], "error")
        self.assertIn("errors", result)

        # Verify multiple errors reported (all-or-nothing validation)
        self.assertGreaterEqual(len(result["errors"]), 2, "Should report at least 2 errors")

        # Verify session state unchanged
        self.assertEqual(len(session.nodes), 0)

    def test_all_or_nothing_validation_preserves_state(self):
        """
        Verify that if any node in a chunk fails, the entire chunk is
        discarded and no partial state is added.
        """
        session = ReportSession(metadata={"VERSION": "1.0"})

        # 1. Add valid content
        valid_chunk = """
- type: heading
  level: 1
  text: "Valid Section"

- type: paragraph
  text: "Valid paragraph"
"""
        result1 = session.add_chunk(valid_chunk)
        self.assertEqual(result1["status"], "success")
        self.assertEqual(len(session.nodes), 2)

        # 2. Send mixed chunk (one valid, one invalid)
        mixed_chunk = """
- type: heading
  level: 2
  text: "Valid Subsection"

- type: paragraph
  # Missing 'text' field - this should fail
"""
        result2 = session.add_chunk(mixed_chunk)
        self.assertEqual(result2["status"], "error")

        # 3. Verify that the valid node from the mixed chunk was NOT added
        self.assertEqual(len(session.nodes), 2, "All-or-nothing: no nodes from failed chunk should be added")

        # 4. Verify chunk index unchanged
        self.assertEqual(session.chunk_index, 1)

    def test_error_payload_contains_node_context(self):
        """
        Verify that error payloads include context about which node failed.
        """
        session = ReportSession(metadata={"VERSION": "1.0"})

        # Chunk with invalid node at index 1
        chunk = """
- type: heading
  level: 1
  text: "Valid"

- type: paragraph
  # Missing 'text' field
"""
        result = session.add_chunk(chunk)

        self.assertEqual(result["status"], "error")
        self.assertIn("errors", result)

        # Verify error contains node index
        error = result["errors"][0]
        self.assertIn("node_index", error)
        self.assertEqual(error["node_index"], 1, "Error should reference index 1")

    def test_recovery_after_yaml_parse_error(self):
        """
        Verify that the session can recover after a YAML syntax error.
        """
        session = ReportSession(metadata={"VERSION": "1.0"})

        # 1. Send invalid YAML syntax
        invalid_yaml = """
- type: heading
  level: 1
  text: "Valid"
  
  this is invalid yaml: [
"""
        result1 = session.add_chunk(invalid_yaml)
        self.assertEqual(result1["status"], "error")
        self.assertIn("yaml_parse_error", str(result1["errors"]))

        # 2. Send valid YAML after the error
        valid_yaml = """
- type: paragraph
  text: "Recovery successful"
"""
        result2 = session.add_chunk(valid_yaml)
        self.assertEqual(result2["status"], "success")
        self.assertEqual(len(session.nodes), 1)

    def test_full_self_healing_workflow(self):
        """
        End-to-end test: simulate a complete LLM self-correction loop.
        
        Workflow:
        1. Submit valid content
        2. Submit malformed content (receive error)
        3. Analyze error and correct
        4. Resubmit corrected content
        5. Finalize document
        """
        session = ReportSession(metadata={"VERSION": "1.0", "TITLE": "Self-Healing Test"})

        # Step 1: Submit valid introduction
        intro = """
- type: heading
  level: 1
  text: "Introduction"

- type: paragraph
  text: "This is a test of the self-healing capabilities."
"""
        result1 = session.add_chunk(intro)
        self.assertEqual(result1["status"], "success")

        # Step 2: Submit malformed heading (missing required 'text' field)
        bad_heading = """
- type: heading
  level: 2
"""
        result2 = session.add_chunk(bad_heading)
        self.assertEqual(result2["status"], "error")

        # Step 3: "LLM analyzes error and corrects"
        # In reality, the LLM would parse result2["errors"] and fix the payload
        # Here we simulate that by providing the corrected version
        corrected_heading = """
- type: heading
  level: 2
  text: "Data Table Section"
"""
        result3 = session.add_chunk(corrected_heading)
        self.assertEqual(result3["status"], "success")

        # Step 4: Submit a table with proper data
        table_chunk = """
- type: table
  caption: "Data Table"
  rows:
    - ["Column A", "Column B"]
    - ["Value 1", "Value 2"]
"""
        result4 = session.add_chunk(table_chunk)
        self.assertEqual(result4["status"], "success")

        # Step 5: Submit conclusion
        conclusion = """
- type: heading
  level: 1
  text: "Conclusion"

- type: paragraph
  text: "The self-healing workflow completed successfully."
"""
        result5 = session.add_chunk(conclusion)
        self.assertEqual(result5["status"], "success")

        # Step 6: Finalize and verify
        output_path = self.temp_path / "self_healing_complete.docx"
        actual_path = session.finalize(output_path)
        
        self.assertTrue(actual_path.exists())
        self.assertGreater(actual_path.stat().st_size, 0)

        # Verify session state
        # Nodes: heading(1) + paragraph(1) + heading(1) + table(1) + heading(1) + paragraph(1) = 6
        self.assertEqual(len(session.nodes), 6)
        # Successful chunks: intro, corrected_heading, table_chunk, conclusion = 4
        self.assertEqual(session.chunk_index, 4, "Should have processed 4 successful chunks")

    def test_markdown_self_healing_recovery(self):
        """
        Verify that the Markdown transpiler can recover from malformed Markdown
        and successfully process corrected content.
        """
        session = ReportSession(metadata={"VERSION": "1.0"})

        # 1. Send valid Markdown heading
        valid_heading = "# Introduction"
        result1 = session.add_markdown_chunk(valid_heading)
        self.assertEqual(result1["status"], "success")
        self.assertEqual(len(session.nodes), 1)

        # 2. Send malformed Markdown (code block with broken syntax)
        # This should fail during Pydantic validation because code field will be empty
        malformed_code = """```python
```"""
        result2 = session.add_markdown_chunk(malformed_code)
        
        # Should return error status
        self.assertEqual(result2["status"], "error")
        self.assertIn("errors", result2)
        
        # 3. Verify session state unchanged
        self.assertEqual(len(session.nodes), 1, "Session should still have only 1 node")
        self.assertEqual(session.chunk_index, 1, "Chunk index should not increment")

        # 4. Send corrected Markdown with actual code content
        corrected_code = """```python
def hello():
    print("Hello, World!")
```"""
        result3 = session.add_markdown_chunk(corrected_code)
        
        # 5. Verify successful acceptance after correction
        self.assertEqual(result3["status"], "success")
        self.assertEqual(len(session.nodes), 2, "Session should now have 2 nodes")

        # 6. Finalize and verify document compiles
        output_path = self.temp_path / "markdown_healed.docx"
        actual_path = session.finalize(output_path)
        self.assertTrue(actual_path.exists())
        self.assertGreater(actual_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
