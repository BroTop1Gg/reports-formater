#!/usr/bin/env python3
"""
Tests for MCP Server registration and tool/resource schemas.

Verifies that the MCP server correctly registers:
- 3 tools: init_report, submit_chunk, finalize_report
- 1 resource: dstu://guidelines
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_server_yaml import mcp, init_report, submit_chunk, finalize_report, get_dstu_guidelines


class TestMCPServerRegistration(unittest.TestCase):
    """Test suite for MCP server tool and resource registration."""

    def test_server_has_tools_registered(self):
        """Verify that all 3 tools are registered."""
        # Access the tool manager
        tools = mcp._tool_manager._tools
        
        # Verify all 3 tools exist
        self.assertIn("init_report", tools)
        self.assertIn("submit_chunk", tools)
        self.assertIn("finalize_report", tools)
        
        # Verify count
        self.assertEqual(len(tools), 3)

    def test_server_has_resource_registered(self):
        """Verify that the dstu://guidelines resource is registered."""
        resources = mcp._resource_manager._resources
        
        # Verify resource exists
        self.assertIn("dstu://guidelines", resources)

    def test_init_report_tool_schema(self):
        """Verify init_report tool has correct parameters."""
        tools = mcp._tool_manager._tools
        tool = tools["init_report"]
        
        # Check tool name
        self.assertEqual(tool.name, "init_report")
        
        # Check parameters exist (JSON schema has 'properties' key)
        params = tool.parameters
        self.assertIn("properties", params)
        self.assertIn("working_dir", params["properties"])
        self.assertIn("metadata", params["properties"])

    def test_submit_chunk_tool_schema(self):
        """Verify submit_chunk tool has correct parameters."""
        tools = mcp._tool_manager._tools
        tool = tools["submit_chunk"]
        
        # Check tool name
        self.assertEqual(tool.name, "submit_chunk")
        
        # Check parameters exist (JSON schema has 'properties' key)
        params = tool.parameters
        self.assertIn("properties", params)
        self.assertIn("yaml_content", params["properties"])

    def test_finalize_report_tool_schema(self):
        """Verify finalize_report tool has correct parameters."""
        tools = mcp._tool_manager._tools
        tool = tools["finalize_report"]
        
        # Check tool name
        self.assertEqual(tool.name, "finalize_report")
        
        # Check parameters exist (JSON schema has 'properties' key)
        params = tool.parameters
        self.assertIn("properties", params)
        self.assertIn("output_filename", params["properties"])

    def test_resource_metadata(self):
        """Verify resource has correct metadata."""
        resources = mcp._resource_manager._resources
        resource = resources["dstu://guidelines"]
        
        # Check URI
        self.assertEqual(str(resource.uri), "dstu://guidelines")
        
        # Check name (updated for dual-protocol architecture)
        self.assertEqual(resource.name, "Ukrainian DSTU 3008-2015 Formatting Guidelines (YAML)")
        
        # Check description contains key terms
        self.assertIsNotNone(resource.description)
        self.assertIn("guidelines", resource.description.lower())


class TestMCPToolFunctions(unittest.TestCase):
    """Test suite for MCP tool function behavior."""

    def setUp(self):
        """Reset global state before each test."""
        import src.mcp_server_yaml as server_module
        server_module._active_session = None
        server_module._working_dir = None

    def test_submit_chunk_without_init_returns_error(self):
        """Verify submit_chunk returns error when session not initialized."""
        result = submit_chunk("- type: heading\n  level: 1\n  text: Test")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("errors", result)
        self.assertEqual(result["errors"][0]["type"], "session_not_initialized")

    def test_finalize_report_without_init_returns_error(self):
        """Verify finalize_report returns error when session not initialized."""
        result = finalize_report("test.docx")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("errors", result)
        self.assertEqual(result["errors"][0]["type"], "session_not_initialized")

    def test_init_report_creates_session(self):
        """Verify init_report creates a session."""
        import src.mcp_server_yaml as server_module
        
        result = init_report(
            working_dir="/tmp",
            metadata={"TITLE": "Test Report"}
        )
        
        self.assertEqual(result["status"], "initialized")
        self.assertIsNotNone(server_module._active_session)
        self.assertIsNotNone(server_module._working_dir)

    def test_full_workflow(self):
        """Test complete workflow: init -> submit -> finalize."""
        import tempfile
        import shutil
        import src.mcp_server_yaml as server_module
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Initialize
            result = init_report(
                working_dir=temp_dir,
                metadata={"VERSION": "1.0"}
            )
            self.assertEqual(result["status"], "initialized")
            
            # Submit chunk
            yaml_content = """
- type: heading
  level: 1
  text: "Test Chapter"

- type: paragraph
  text: "Test paragraph content."
"""
            result = submit_chunk(yaml_content)
            self.assertEqual(result["status"], "success")
            self.assertIn("outline", result)
            
            # Finalize
            result = finalize_report("test_output.docx")
            self.assertEqual(result["status"], "finalized")
            self.assertIn("output_path", result)
            
            # Verify file was created
            output_path = Path(result["output_path"])
            self.assertTrue(output_path.exists())
            
        finally:
            # Cleanup
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
            
            # Clean up draft_report.yaml if created
            backup = Path("draft_report.yaml")
            if backup.exists():
                backup.unlink()

    def test_get_dstu_guidelines_returns_content(self):
        """Verify guidelines resource returns content."""
        content = get_dstu_guidelines()
        
        # Should return non-empty content
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 0)
        
        # Should contain DSTU reference (Ukrainian Cyrillic version)
        self.assertIn("ДСТУ", content)


class TestMCPToolValidation(unittest.TestCase):
    """Test tool validation behavior."""

    def setUp(self):
        """Reset global state before each test."""
        import src.mcp_server_yaml as server_module
        server_module._active_session = None
        server_module._working_dir = None

    def test_submit_chunk_with_invalid_yaml(self):
        """Verify submit_chunk handles invalid YAML."""
        import tempfile
        import src.mcp_server_yaml as server_module
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            init_report(working_dir=temp_dir, metadata={})
            
            # Submit invalid YAML
            invalid_yaml = """
- type: heading
  level: 1
  text: "Valid"
  
  this is invalid yaml: [
"""
            result = submit_chunk(invalid_yaml)
            
            self.assertEqual(result["status"], "error")
            self.assertIn("errors", result)
            
        finally:
            import shutil
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)

    def test_submit_chunk_with_invalid_node_type(self):
        """Verify submit_chunk rejects unknown node types."""
        import tempfile
        import src.mcp_server_yaml as server_module
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            init_report(working_dir=temp_dir, metadata={})
            
            # Submit chunk with unknown type
            yaml_content = """
- type: unknown_node_type
  data: "some data"
"""
            result = submit_chunk(yaml_content)
            
            self.assertEqual(result["status"], "error")
            self.assertIn("errors", result)
            
        finally:
            import shutil
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
