#!/usr/bin/env python3
"""
MCP Server for ReportSession SDK.

Exposes the ReportSession API via Model Context Protocol (stdio transport).
State is maintained in-memory during the server session.
"""

import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP
from src.sdk.session import ReportSession

# Global session state (in-memory, per server instance)
_active_session: ReportSession | None = None
_working_dir: Path | None = None

# Initialize FastMCP server
mcp = FastMCP(
    name="reports-formater-yaml",
    instructions="MCP server for generating DSTU 3008-2015 compliant technical reports from YAML content.",
)


@mcp.tool()
def init_report(working_dir: str, metadata: Dict[str, Any]) -> Dict[str, str]:
    """
    Initialize a new report session.
    
    Args:
        working_dir: Directory for relative assets resolution.
        metadata: Initial report placeholders and template selections.
    
    Returns:
        Status confirmation.
    """
    global _active_session, _working_dir
    
    _working_dir = Path(working_dir).resolve()
    _active_session = ReportSession(metadata=metadata)
    
    return {"status": "initialized"}


@mcp.tool()
def submit_chunk(yaml_content: str) -> Dict[str, Any]:
    """
    Submit a YAML content chunk for validation and accumulation.
    
    Args:
        yaml_content: A declarative YAML chunk (can be a list of nodes).
    
    Returns:
        The exact dictionary returned by the SDK (either the structural
        outline on success, or structured errors list on failure).
    """
    if _active_session is None:
        return {
            "status": "error",
            "errors": [{"type": "session_not_initialized", "message": "Call init_report first"}]
        }
    
    return _active_session.add_chunk(yaml_content)


@mcp.tool()
def finalize_report(output_filename: str) -> Dict[str, Any]:
    """
    Finalize the report and generate the .docx file.
    
    Args:
        output_filename: Filename for the generated .docx report.
    
    Returns:
        Status and absolute output path.
    """
    if _active_session is None:
        return {
            "status": "error",
            "errors": [{"type": "session_not_initialized", "message": "Call init_report first"}]
        }
    
    if _working_dir is None:
        return {
            "status": "error",
            "errors": [{"type": "working_dir_not_set", "message": "Call init_report first"}]
        }
    
    # Convert to absolute path using session's working_dir
    output_path = (_working_dir / output_filename).resolve()
    
    # Invoke finalize
    actual_path = _active_session.finalize(output_path)
    
    return {
        "status": "finalized",
        "output_path": str(actual_path)
    }


@mcp.resource(
    uri="dstu://guidelines",
    name="Ukrainian DSTU 3008-2015 Formatting Guidelines (YAML)",
    description="Strict guidelines, formatting instructions, quoting rules, and YAML schema rules for generating compliant university reports.",
    mime_type="text/markdown"
)
def get_dstu_guidelines() -> str:
    """
    Read and return the DSTU 3008-2015 guidelines for YAML interface.
    
    Returns:
        Content of familiarization/ai_system_prompt_yaml.md
    """
    guidelines_path = PROJECT_ROOT / "familiarization" / "ai_system_prompt_yaml.md"
    
    if not guidelines_path.exists():
        return f"Error: Guidelines file not found at {guidelines_path}"
    
    return guidelines_path.read_text(encoding="utf-8")


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
