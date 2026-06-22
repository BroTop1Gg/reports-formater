# User Guide: Reports-Formater

This tool automates the creation of `.docx` reports based on structured YAML or natural Markdown content files and a DOCX template. It adheres to DSTU 3008-2015 standards for Ukrainian university lab reports.

---

## Dual-Protocol Gateway

Reports-Formater supports two input protocols:

1.  **YAML Protocol** — Structured, explicit format with full control over all parameters.
2.  **Markdown Protocol** — Natural, highly readable format with automatic transpilation to the internal AST.

Both protocols are fully supported across all three interfaces:
*   **CLI** — Direct command-line execution (accepts both `.yaml` and `.md` files).
*   **Programmatic SDK** — Python API for custom integration into developers’ scripts.
*   **MCP Servers** — Model Context Protocol servers for seamless AI client integration (Claude Desktop, etc.).

---

## 1. Installation

### Prerequisites
*   Python 3.10+
*   pip (Python package manager)

### Setup

**Linux / macOS:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Windows:**
```cmd
:: Create virtual environment
python -m venv venv

:: Activate virtual environment
venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt
```

### LaTeX Support (Optional)
To render complex mathematical equations, the tool uses Matplotlib natively. For highly complex LaTeX expressions (such as `\begin{cases}` matrices), a local LaTeX compiler is used as a fallback.

To install LaTeX on Linux:
```bash
sudo apt install texlive-full texlive-lang-cyrillic
```
Ensure that `latex` and `dvipng` are accessible in your `$PATH`.

---

## 2. Usage (CLI Execution)

The tool is invoked via `python -m src.main` from the project root. It automatically detects the file extension and compiles accordingly.

### Command Syntax
```bash
python -m src.main <input_file> [--template <template_path>] [--output <output_path>] [--config <config_path>] [-v]
```

### Arguments
| Argument | Required | Description |
|---|---|---|
| `input_file` | ✅ | Path to either a YAML (`.yaml` / `.yml`) or Markdown (`.md` / `.markdown`) content file. |
| `--template` | ❌ | Path to base `.docx` template with title page and `{{PLACEHOLDERS}}`. If omitted, the default template (`src/DEFAULT_TEMPLATE.docx`) is used. |
| `--output` | ❌ | Path for the generated `.docx` file (default: `output.docx`). |
| `--config` | ❌ | Path to custom `report_styles.json`. If omitted, the default `src/report_styles.json` is used. |
| `-v, --verbose` | ❌ | Enable debug-level logging for layout tracking. |

### YAML Front-Matter (For Markdown Files)
When compiling a `.md` file, you can define document metadata and page layout options directly on the very first lines of your file using standard YAML Front-Matter:

```markdown
---
page_numbering: true
header_text: "Іваненко І.І., група ЗП-31"
---

# ЛАБОРАТОРНА РОБОТА № 5

Тема: розробка асинхронних сервісів...
```

### Examples

**Compile Markdown directly with running header & page numbering:**
```bash
python -m src.main report.md --output Technical_Report.docx
```

**Compile YAML with a custom title page template:**
```bash
python -m src.main report.yaml --template templates/title_template.docx --output Technical_Report.docx
```

---

## 3. Programmatic Python SDK Guide

For developers looking to integrate the generator into custom applications, the SDK provides the `ReportSession` API to accumulate nodes in-memory:

```python
from pathlib import Path
from src.sdk.session import ReportSession

# 1. Initialize session with metadata
session = ReportSession(metadata={"VERSION": "1.0"})

# 2. Configure global document overrides
session.metadata["page_numbering"] = True
session.metadata["header_text"] = "Іваненко І.І., група ЗП-31"

# 3. Accumulate Markdown or YAML chunks in-memory
session.add_markdown_chunk("# ЛАБОРАТОРНА РОБОТА № 5")
session.add_markdown_chunk("Тема: «Обчислення характеристик швидкодії».")

# 4. Finalize and compile into a beautifully styled .docx
output_path = Path("output_report.docx")
session.finalize(output_path)
```

---

## 4. AI MCP Integration Guide

The project provides two Model Context Protocol (MCP) stdio servers for seamless AI client integration:

### YAML Protocol Server
For structured, schema-driven content generation:
```bash
python -m src.mcp_server_yaml
```
- Tools: `init_report`, `submit_chunk`, `finalize_report`
- Resource: `dstu://guidelines` (YAML schema reference `ai_system_prompt_yaml.md`)

### Markdown Protocol Server
For natural, Pandoc-style Markdown input:
```bash
python -m src.mcp_server_markdown
```
- Tools: `init_report`, `submit_markdown_chunk`, `finalize_report`
- Resource: `dstu://guidelines` (Markdown syntax reference `ai_system_prompt_markdown.md`)

### Client Configuration (mcp_config.json)

Register the servers in your MCP host (like Claude Desktop) using absolute paths:

```json
{
  "mcpServers": {
    "reports-formatter-yaml": {
      "command": "/path/to/reports-formater/venv/bin/python",
      "args": ["-m", "src.mcp_server_yaml"],
      "env": {
        "PYTHONPATH": "/path/to/reports-formater"
      }
    },
    "reports-formatter-markdown": {
      "command": "/path/to/reports-formater/venv/bin/python",
      "args": ["-m", "src.mcp_server_markdown"],
      "env": {
        "PYTHONPATH": "/path/to/reports-formater"
      }
    }
  }
}
```

---

## 5. Running Tests

The test suite runs scenarios verifying structural parity, self-healing validation, and transport layers.

**Linux / macOS:**
```bash
bash tests/run_tests.sh
```

**Windows:**
```cmd
tests\run_tests.bat
```

Output `.docx` files are saved to `tests/output/`.

---

## 6. Configuration & Style Hierarchy

The tool uses a **layered configuration** system. Each layer overrides the previous one:

| Priority | Source | What it controls |
|---|---|---|
| 1 (Lowest) | **Pydantic defaults** (hardcoded in `src/config/models.py`) | Fallback values if nothing else is specified. |
| 2 | **`src/report_styles.json`** | Main style configuration: fonts, margins, spacing, indents, page numbering. |
| 3 (Highest) | **Input File** (YAML overrides / MD Front-Matter) | Runtime overrides: `page_numbering`, `header_text`, `metadata` for placeholders. |

The `.docx` template (via `--template`) defines the visual base of the document (title page, default margins), but the style configuration is always applied on top of it.

---

## 7. Examples & Reference

The `tests/input/` directory contains canonical reference files that demonstrate all supported features:

| File | What it demonstrates |
|---|---|
| `test_with_title.yaml` | Full report with title page (metadata + template), all YAML node types. |
| `test_with_title.md` | Clean Markdown-First reference document (headers, lists, tables, code, formulas). |
| `test_without_title.yaml` | Report without title page, with header text and page numbering. |
| `test_title_and_numbering.yaml` | Title page + page numbering (numbering skips first page). |
| `title_template.docx` | Example title page template with `{{PLACEHOLDERS}}`. |
| `title_placeholders_list.txt` | List of available placeholder names for the title template. |
```