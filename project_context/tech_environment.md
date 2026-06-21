# Tech Environment

## Tech Stack
- **Language:** Python 3.10+
- **Rendering Backend:** `python-docx` (OXML manipulation)
- **Mathematical Layout:** `matplotlib` (Agg backend) + System LaTeX fallback (`texlive`)
- **State Validation:** `pydantic` (V2 validation schemas)
- **Serialization:** `PyYAML` (safe loading and parsing)
- **Interface Protocol:** `mcp` (Anthropic Model Context Protocol Python SDK)
- **Testing:** `pytest` / `unittest` (Standard modules)

## Absolute Workspace Layout
All operations and tool executions MUST target paths relative to this absolute workspace root:
`WORKSPACE_ROOT = /home/acer/Projects/DevelopingUtilities/reports-formater/`

### Key Absolute Paths
- **Venv Python:** `/home/acer/Projects/DevelopingUtilities/reports-formater/venv/bin/python`
- **CLI Main:** `src/main.py`
- **SDK Package:** `src/sdk/`
- **MCP Servers:**
  - `src/mcp_server_yaml.py`
  - `src/mcp_server_markdown.py`
- **Reference Inputs:** `tests/input/test_with_title.yaml`

## Verification & Test Commands
To execute audits, activate the virtual environment and run the test pyramid:
```bash
cd /home/acer/Projects/DevelopingUtilities/reports-formater
source venv/bin/activate

# Run all tests (including legacy and SDK)
python -m pytest tests/ -v

# Run structural identity validation (E2E)
python -m pytest tests/test_e2e_identity.py -v
```

## Virtual Environment Verification
The environment contains `mcp` library dependencies. Standard standard-out and standard-in (Stdio) protocols are utilized for JSON-RPC 2.0 communication.