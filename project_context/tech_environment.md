# Tech Environment

## Tech Stack
- **Language:** Python 3.12.3
- **Rendering Backend:** `python-docx` (OXML manipulation)
- **Mathematical Layout:** `matplotlib` (Agg backend) + System LaTeX fallback (`texlive`)
- **State Validation:** `pydantic` (V2 validation schemas)
- **Serialization:** `PyYAML` (safe loading and parsing)
- **Markdown Parsing:** `re` (stdlib regex, zero external dependencies)
- **Interface Protocol:** `mcp` (Anthropic Model Context Protocol Python SDK)
- **Testing:** `pytest` (primary) / `unittest` (legacy compatibility)

## Absolute Workspace Layout
All operations and tool executions MUST target paths relative to this absolute workspace root:
`WORKSPACE_ROOT = /home/acer/Projects/DevelopingUtilities/reports-formater/`

### Key Absolute Paths
- **Venv Python:** `/home/acer/Projects/DevelopingUtilities/reports-formater/venv/bin/python`
- **CLI Main:** `src/main.py`
- **SDK Package:** `src/sdk/`
  - `src/sdk/markdown_parser.py` - Natural Markdown transpiler (Phase 4)
  - `src/sdk/session.py` - ReportSession state buffer
- **MCP Servers:**
  - `src/mcp_server_yaml.py`
  - `src/mcp_server_markdown.py`
- **Reference Inputs:**
  - `tests/input/test_with_title.yaml` - YAML reference document
  - `tests/input/test_with_title.md` - Natural Markdown equivalent
- **Test Configuration:** `tests/conftest.py` - Pytest path configuration

## Verification & Test Commands
To execute audits, activate the virtual environment and run the test pyramid:
```bash
cd /home/acer/Projects/DevelopingUtilities/reports-formater
source venv/bin/activate

# Run all tests (73 tests, ~12 seconds)
python -m pytest tests/ -v

# Run structural identity validation (E2E parity)
python -m pytest tests/test_e2e_identity.py -v

# Run Markdown parser unit tests (31 tests)
python -m pytest tests/test_markdown_parser.py -v

# Run specific test with verbose output
python -m pytest tests/test_e2e_identity.py::TestStructuralIdentity::test_monolithic_yaml_vs_mcp_markdown_parity -xvs
```

## Virtual Environment Verification
The environment contains `mcp` library dependencies. Standard standard-out and standard-in (Stdio) protocols are utilized for JSON-RPC 2.0 communication.

## Test Suite Structure (Phase 4)
- **test_markdown_parser.py** (31 tests) - Natural Markdown syntax parsing
  - Smart Defaults (paragraph, formula, image, table)
  - Smart Caption Absorption (with/without path extraction)
  - Natural image placeholders
  - LaTeX formulas, line breaks, page breaks
- **test_e2e_identity.py** (3 tests) - Structural parity validation
  - YAML vs chunked YAML
  - YAML vs Markdown (100% parity)
- **test_self_healing_sim.py** (8 tests) - Validation & recovery
- **test_mcp_server.py** (15 tests) - MCP registration & tools
- **test_sdk_session.py** (12 tests) - Session API
- **test_mcp_transport.py** (3 tests) - MCP protocol
- **test_cli_markdown.py** (1 test) - CLI markdown compilation

**Total:** 73 tests, 100% pass rate, ~12s execution time

## Key Technical Changes (Phase 4)
- **Removed:** All curly-brace attribute parsing (`{align=...}`, `{width=...}`, `{style=...}`)
- **Added:** Smart Defaults (automatic formatting for paragraphs, formulas, images, tables)
- **Added:** Smart Caption Absorption (italic captions before code blocks/tables)
- **Added:** Natural image placeholders (`![Caption](placeholder)`)
- **Added:** Path extraction from listing captions (`*Лістинг 1.1 — Description (path/to/file.py)*`)
- **Fixed:** Regex pattern to correctly separate caption from path (uses group(1) for full caption)
