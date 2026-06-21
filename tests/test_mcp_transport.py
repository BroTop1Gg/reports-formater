"""
Integration tests for MCP server stdio transport.

Tests the JSON-RPC 2.0 communication over stdio by spawning the MCP server
as a subprocess and sending/receiving JSON-RPC messages.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
MARKDOWN_SERVER = PROJECT_ROOT / "src" / "mcp_server_markdown.py"
YAML_SERVER = PROJECT_ROOT / "src" / "mcp_server_yaml.py"


def _read_response(proc, expected_id, timeout=5.0):
    """Read JSON-RPC response with matching id."""
    start = time.time()
    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if line.strip():
            try:
                response = json.loads(line.strip())
                if response.get("id") == expected_id:
                    return response
            except json.JSONDecodeError:
                continue
    return None


def _initialize_server(proc):
    """Perform MCP handshake with server."""
    # Step 1: Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.flush()
    
    # Wait for initialize response
    response = _read_response(proc, expected_id=0)
    assert response is not None, "No initialize response"
    assert "result" in response, f"Initialize failed: {response}"
    
    # Step 2: Send initialized notification (no response expected)
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    proc.stdin.write(json.dumps(initialized_notification) + "\n")
    proc.stdin.flush()
    
    # Small delay to ensure server processes notification
    time.sleep(0.1)


def _extract_tool_result(response):
    """
    Extract the tool result from an MCP CallToolResponse.
    
    MCP SDK wraps tool results in:
    {
        "result": {
            "content": [{"type": "text", "text": "<json-string>"}],
            "structuredContent": {"result": {...}},
            "isError": false
        }
    }
    
    Returns the parsed inner result dict.
    """
    assert response is not None, "No response received"
    assert "result" in response, f"Error response: {response}"
    
    result = response["result"]
    
    # Try structuredContent first (MCP SDK v1.28+)
    if "structuredContent" in result:
        return result["structuredContent"].get("result", result["structuredContent"])
    
    # Fallback: parse content[0].text as JSON
    if "content" in result and len(result["content"]) > 0:
        text = result["content"][0].get("text", "")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_text": text}
    
    return result


class TestMCPTransport:
    """Test MCP server stdio transport and JSON-RPC 2.0 protocol."""

    def test_markdown_server_init_report(self):
        """Test init_report tool via JSON-RPC 2.0 over stdio."""
        proc = subprocess.Popen(
            [sys.executable, str(MARKDOWN_SERVER)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        try:
            # Perform MCP handshake
            _initialize_server(proc)
            
            # Send init_report tool call
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "init_report",
                    "arguments": {
                        "working_dir": str(PROJECT_ROOT),
                        "metadata": {"title": "Test Report"}
                    }
                }
            }
            
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.flush()
            
            # Read response
            response = _read_response(proc, expected_id=1)
            
            # Terminate server
            proc.terminate()
            proc.wait(timeout=2)
            
            # Verify response
            tool_result = _extract_tool_result(response)
            assert tool_result["status"] == "initialized"
            
        except Exception as e:
            proc.kill()
            stderr = proc.stderr.read()
            pytest.fail(f"MCP transport test failed: {e}\nStderr: {stderr}")

    def test_yaml_server_init_report(self):
        """Test YAML server init_report via JSON-RPC 2.0."""
        proc = subprocess.Popen(
            [sys.executable, str(YAML_SERVER)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        try:
            # Perform MCP handshake
            _initialize_server(proc)
            
            # Send init_report tool call
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "init_report",
                    "arguments": {
                        "working_dir": str(PROJECT_ROOT),
                        "metadata": {"title": "YAML Test"}
                    }
                }
            }
            
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.flush()
            
            # Read response
            response = _read_response(proc, expected_id=1)
            
            proc.terminate()
            proc.wait(timeout=2)
            
            tool_result = _extract_tool_result(response)
            assert tool_result["status"] == "initialized"
            
        except Exception as e:
            proc.kill()
            stderr = proc.stderr.read()
            pytest.fail(f"YAML server test failed: {e}\nStderr: {stderr}")

    def test_markdown_server_submit_chunk(self):
        """Test submit_markdown_chunk tool after initialization."""
        proc = subprocess.Popen(
            [sys.executable, str(MARKDOWN_SERVER)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        try:
            # Perform MCP handshake
            _initialize_server(proc)
            
            # Send init_report
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "init_report",
                    "arguments": {
                        "working_dir": str(PROJECT_ROOT),
                        "metadata": {}
                    }
                }
            }
            
            proc.stdin.write(json.dumps(init_request) + "\n")
            proc.stdin.flush()
            
            # Wait for init response
            init_response = _read_response(proc, expected_id=1)
            init_result = _extract_tool_result(init_response)
            assert init_result["status"] == "initialized"
            
            # Send submit_markdown_chunk
            submit_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "submit_markdown_chunk",
                    "arguments": {
                        "markdown_content": "# ВСТУП\n\nЦе тестовий абзац."
                    }
                }
            }
            
            proc.stdin.write(json.dumps(submit_request) + "\n")
            proc.stdin.flush()
            
            # Wait for submit response
            submit_response = _read_response(proc, expected_id=2)
            
            proc.terminate()
            proc.wait(timeout=2)
            
            submit_result = _extract_tool_result(submit_response)
            assert submit_result["status"] == "success"
            assert "outline" in submit_result
            
        except Exception as e:
            proc.kill()
            stderr = proc.stderr.read()
            pytest.fail(f"Submit chunk test failed: {e}\nStderr: {stderr}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
