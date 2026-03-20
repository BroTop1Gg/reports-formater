# User Guide: Reports-Formater (CLI Tool)

This tool automates the creation of `.docx` reports based on a YAML content file and a DOCX template. It adheres to DSTU 3008-2015 standards for Ukrainian university lab reports.

## 1. Installation

### Prerequisites
*   Python 3.8+
*   pip (Python package manager)

### Setup

**Linux:**
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

## 2. Usage

The tool is invoked via `python -m src.main` from the project root.

### Command Syntax
```
python -m src.main <input_yaml> [--template <template_path>] [--output <output_path>] [--config <config_path>] [-v]
```

### Arguments
| Argument | Required | Description |
|---|---|---|
| `input_yaml` | ✅ | Path to the YAML content file (e.g., `report.yaml`). |
| `--template` | ❌ | Path to base `.docx` template with title page and `{{PLACEHOLDERS}}`. If not provided, the default template (`src/DEFAULT_TEMPLATE.docx`) is used. |
| `--output` | ❌ | Path for the output `.docx` file. Defaults to `output.docx`. |
| `--config` | ❌ | Path to a custom `report_styles.json`. Defaults to `src/report_styles.json`. |
| `-v, --verbose` | ❌ | Enable debug-level logging for troubleshooting. |

### Examples

**Report without title page (header + page numbering):**
```bash
python -m src.main report.yaml --output Technical_Report.docx
```

**Report with custom title page template:**
```bash
python -m src.main report.yaml --template templates/title_template.docx --output Technical_Report.docx
```

**Verbose mode for debugging:**
```bash
python -m src.main report.yaml --output Technical_Report.docx -v
```

## 3. Workflow

1.  **Prepare a Template (optional):** Create a Word document with your Title Page. Use placeholders like `{{STUDENT_NAME}}`, `{{CURRENT_YEAR}}` where text should be injected. See `tests/input/title_template.docx` for reference. Recommended to create "title_placeholders" txt document (and add it to AI) to avoid AI placeholders name missmatch.
2.  **Write Content in YAML:** Create a `.yaml` file describing the report structure. Refer to `familiarization/ai_system_prompt.md` for the full YAML schema, or ask an LLM to generate it.
3.  **Build:** Run the CLI command above.
4.  **Verify:** Open the generated `.docx` in Word or LibreOffice to verify format.

## 4. Running Tests

Tests generate sample `.docx` files from test YAML inputs and verify visually.

**Linux:**
```bash
bash tests/run_tests.sh
```

**Windows:**
```cmd
tests\run_tests.bat
```

The test suite runs 3 scenarios:
1.  Report WITH title page template (no page numbering).
2.  Report WITHOUT title page (header + page numbering).
3.  Report WITH title page AND page numbering.

Output files are saved to `tests/output/`.

## 5. Configuration & Style Hierarchy

The tool uses a **layered configuration** system. Each layer overrides the previous one:

| Priority | Source | What it controls |
|---|---|---|
| 1 (Lowest) | **Pydantic defaults** (hardcoded in `src/config/models.py`) | Fallback values if nothing else is specified. |
| 2 | **`src/report_styles.json`** | Main style configuration: fonts, margins, spacing, indents, page numbering. |
| 3 (Highest) | **YAML file** (your `report.yaml`) | Runtime overrides: `page_numbering`, `header_text`, `metadata` for placeholders. |

The `.docx` **template** (via `--template`) is a separate layer. It defines the visual base of the document (title page, styles, headers/footers), but the tool always applies margins and formatting from the config on top of it.

> **Note:** If no `--template` is provided and `src/DEFAULT_TEMPLATE.docx` exists, it is used as a fallback. If that file is also missing, the tool creates a blank document. The program will **not** crash.

### What you can change

| File | Purpose | When to edit |
|---|---|---|
| `src/report_styles.json` | Fonts, margins, spacing rules, indents, page numbering defaults. | When you need different formatting (e.g., different margins, font size, or list indentation). |
| `familiarization/ai_system_prompt.md` | System prompt for LLM. Defines YAML schema, DSTU rules, and report structure conventions. | When you want the AI to follow different report conventions or support new YAML features. |
| Template `.docx` file | Title page layout, Word styles, headers/footers, `{{PLACEHOLDER}}` fields. | When you need a different title page design or base document. |
| YAML report file | Content + runtime config overrides. | Every report — this is your main input. |

### Design Philosophy: "Dumb Builder"

The tool is designed as a **"dumb builder"** — it renders exactly what it receives in the YAML, no more, no less. It does not make assumptions about content, does not reorder elements, and does not add hidden formatting.

This means:
*   **Full user control.** The AI (or the user) is responsible for the *content and structure*. The builder is responsible only for *formatting*.
*   **Adaptability.** To adapt the tool for different standards or institutions, you only need to modify two files: `report_styles.json` (formatting) and `ai_system_prompt.md` (content rules for the AI). The source code itself does not need changes.
*   **Transparency.** All formatting decisions come from the configuration — there are no "magic" hidden rules inside the code (at the very least I try to do that way).

> **Limitation:** Some formatting details (like spacing between specific element types) are managed by the `SpacingEngine` based on `spacing_rules` in `report_styles.json`. While configurable, these rules may not cover every edge case.

## 6. Examples & Reference

The `tests/input/` directory contains canonical reference files that demonstrate all supported features:

| File | What it demonstrates |
|---|---|
| `test_with_title.yaml` | Full report with title page (metadata + template), all content types. |
| `test_without_title.yaml` | Report without title page, with header text and page numbering. |
| `test_title_and_numbering.yaml` | Title page + page numbering (numbering skips first page). |
| `title_template.docx` | Example title page template with `{{PLACEHOLDERS}}`. |
| `title_placeholders_list.txt` | List of available placeholder names for the title template. |

To understand how the YAML content maps to the final `.docx`, run the tests and compare the input YAML with the generated output in `tests/output/`.