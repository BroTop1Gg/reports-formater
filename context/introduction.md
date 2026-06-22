# Developer Onboarding & Extension Guide

Welcome to the `reports-formater` development workspace. This guide is the single
source of truth for human developers and autonomous AI agents who need to understand
the codebase layout, internal service boundaries, and the exact protocol required
to extend the platform safely.

---

## 1. Physical Directory Tree

```text
reports-formater/
│
├── context/                          # Architectural decisions & developer guides
│   ├── ARCHITECTURE.md               # 4-layer system boundaries and data flow
│   ├── code_style.md                 # Python conventions & intervention safety rules
│   ├── introduction.md               # THIS FILE — onboarding & extension guide
│   ├── philosophy.md                 # Dumb Builder vs Smart Transpiler paradigm
│   └── todo.txt                      # Working notes / scratch
│
├── familiarization/                  # System manuals & AI generation guidelines
│   ├── ai_system_prompt_yaml.md      # Reference prompt for YAML-driven AI generation
│   ├── ai_system_prompt_markdown.md  # Reference prompt for Markdown-driven AI generation
│   └── user_guide.md                 # Complete user manual (CLI, SDK, MCP)
│
├── project_context/                  # Project management & memory
│   ├── active_development.md         # Current phase status & test results
│   ├── memory.md                     # Durable changelog ledger (lessons, decisions)
│   ├── project_overview.md           # High-level project summary
│   ├── system_design.md              # Detailed system design notes
│   └── tech_environment.md           # Toolchain & dependency versions
│
├── src/                              # Production codebase
│   ├── config/
│   │   ├── __init__.py
│   │   ├── models.py                 # Typed Pydantic configuration models (Layer 1)
│   │   ├── loader.py                 # Layered config loader with deep merge
│   │   └── schemas.py                # AST node Pydantic V2 schemas (Layer 2)
│   │
│   ├── sdk/
│   │   ├── __init__.py
│   │   ├── session.py                # ReportSession state manager (Layer 2)
│   │   └── markdown_parser.py        # Natural Markdown → AST transpiler (Layer 3)
│   │
│   ├── renderers/                    # Specialized OXML visual writers (Layer 1)
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseRenderer + RenderContext protocols
│   │   ├── paragraph_renderer.py     # Standard text paragraphs
│   │   ├── heading_renderer.py       # Headings with TOC support
│   │   ├── list_renderer.py          # Bullet, numbered, alpha (Cyrillic/Latin)
│   │   ├── table_renderer.py         # Grid tables with caption + header repeat
│   │   ├── image_renderer.py         # Images + invisible layout tables
│   │   ├── code_block_renderer.py    # Monospaced code listings with captions
│   │   ├── formula_renderer.py       # LaTeX → PNG → embedded images
│   │   └── break_renderer.py         # Page breaks, line breaks, section breaks
│   │
│   ├── services/                     # Layer 1 support services
│   │   ├── __init__.py
│   │   ├── rendering_service.py      # Renderer registry + Strategy dispatcher
│   │   ├── spacing_engine.py         # DSTU-compliant margin collapsing
│   │   ├── style_manager.py          # Fuzzy matching for MS Word XML style IDs
│   │   └── placeholder_service.py    # Cascade {{KEY}} replacement in templates
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── docx_utils.py             # OXML manipulation (invisible tables, borders)
│   │   ├── file_io.py                # FailSafeSaver — retry + timestamped rename
│   │   └── formatting.py             # Inline markdown bold/italic/code formatter
│   │
│   ├── mcp_server_yaml.py            # Structured YAML MCP Stdio interface (Layer 4)
│   ├── mcp_server_markdown.py        # Natural Markdown MCP Stdio interface (Layer 4)
│   ├── main.py                       # Consolidated CLI entry point (Layer 4)
│   ├── report_factory.py             # Top-level orchestrator (Layer 1)
│   ├── report_styles.json            # Visual identity config (fonts, margins, spacing)
│   └── DEFAULT_TEMPLATE.docx         # Empty default OXML template
│
├── tests/                            # Test pyramid
│   ├── conftest.py                   # Shared fixtures
│   ├── input/                        # Reference test documents & templates
│   ├── output/                       # Compiled test output (gitignored)
│   ├── assets/                       # Test images
│   ├── test_markdown_parser.py       # Unit tests for Layer 3 transpiler
│   ├── test_sdk_session.py           # Unit tests for Layer 2 SDK session
│   ├── test_mcp_server.py            # Unit tests for Layer 4 MCP wrappers
│   ├── test_mcp_transport.py         # Stdio JSON-RPC 2.0 integration tests
│   ├── test_self_healing_sim.py      # Real-time validation & self-healing tests
│   ├── test_cli_markdown.py          # CLI integration tests
│   ├── test_e2e_identity.py          # E2E structural parity (YAML ↔ Markdown)
│   ├── run_tests.sh                  # Bash test runner
│   └── run_tests.bat                 # Windows test runner
│
├── tutorial/                         # Ready-to-run example documents
│   ├── report.md                     # Markdown tutorial template (ДСТУ lab report)
│   ├── report.yaml                   # Legacy YAML tutorial template
│   ├── TUTORIAL.md                   # Tutorial usage instructions
│   └── tasks.txt                     # Tutorial exercise tasks
│
├── other/                            # Reference materials (standards, images)
├── .gitignore                        # Git ignore rules
├── mcp_config.json                   # Local MCP config (PRIVATE — gitignored)
├── mcp_config.json.example           # Template MCP config (TRACKED — generic paths)
├── requirements.txt                  # Python dependencies
├── LICENSE                           # Project license
└── README.md                         # Project overview & quick start
```

---

## 2. Core Service Boundaries

### `ReportFactory` (`src/report_factory.py`)
The top-level orchestrator. Owns the full document lifecycle:
- Loads and deep-merges configuration (`ConfigLoader` → `report_styles.json` → metadata overrides).
- Loads the `.docx` template (CLI arg → YAML metadata → `DEFAULT_TEMPLATE.docx`).
- Configures page margins, headers, footers, and page numbering.
- Replaces `{{PLACEHOLDER}}` tags via `PlaceholderService` (cascade: run-level → paragraph-level).
- Parses content dicts into Pydantic nodes, applies `SpacingEngine`, then flushes to `RenderingService`.
- Saves output via `FailSafeSaver` (retry + timestamped rename if file is locked).

### `SpacingEngine` (`src/services/spacing_engine.py`)
Automates DSTU-compliant inter-block spacing. Implements margin collapsing:
- Reads spacing rules from `config.spacing_rules` (data-driven, not hardcoded).
- Injects explicit `break` nodes between adjacent content nodes when needed.
- Ensures consistent vertical rhythm across all block type transitions.

### `PlaceholderService` (`src/services/placeholder_service.py`)
Searches and replaces `{{KEY}}` tags inside `.docx` XML runs:
- **Cascade Strategy:** First attempts run-level replacement (preserves inline formatting).
- Falls back to paragraph-level replacement if MS Word splits the tag across multiple runs.
- Supports flat metadata and nested `mapping` dicts for backward compatibility.

### `docx_utils` (`src/utils/docx_utils.py`)
The single source of truth for low-level OXML manipulation:
- Constructs invisible borderless tables for anchoring images/formulas/listings side-by-side with captions.
- Provides `get_alignment_enum()` — the only allowed way to resolve alignment strings to `WD_ALIGN_PARAGRAPH` values.
- Handles border creation, cell merging, and namespace-qualified XML element construction.

---

## 3. How to Add a New Visual Block / Renderer

Follow this strict step-by-step checklist. Skipping any step risks breaking the
AST contract, the renderer registry, or the test suite.

### Step 1 — Define the AST Schema (`src/config/schemas.py`)
Create a new Pydantic model inheriting from `ContentNode`:
```python
class ChartData(ContentNode):
    type: Literal["chart"] = "chart"
    data: List[float] = Field(...)
    caption: Optional[str] = None
```
- Add it to the `AnyContentNode` union type.
- Register it in the `type_map` dict inside `parse_content_node()`.

### Step 2 — Add Configuration (if visual parameters needed)
- Add fields to `src/config/models.py` (inside `StyleConfig` or `ReportConfig`).
- Add matching values to `src/report_styles.json` with sensible defaults.

### Step 3 — Implement the Renderer (`src/renderers/`)
Create `src/renderers/chart_renderer.py`:
```python
from src.renderers.base import BaseRenderer, RenderContext

class ChartRenderer(BaseRenderer):
    node_type = "chart"

    def render(self, context: RenderContext, data: ChartData) -> None:
        # OXML writing logic here
        ...
```
- Inherit from `BaseRenderer`.
- Implement `node_type` (class attribute) and `render(context, data)`.
- Use `docx_utils` for any invisible table / border construction.
- Use `get_alignment_enum()` from `docx_utils` for alignment — never a local dict.

### Step 4 — Register the Renderer (`src/report_factory.py`)
Add the import and register in `ReportFactory.__init__`:
```python
from src.renderers.chart_renderer import ChartRenderer

self._rendering_service.register_all([
    ...existing renderers...,
    ChartRenderer(),
])
```

### Step 5 — Update the Markdown Transpiler (if applicable)
If the new block can be authored in Markdown, add its regex pattern and parsing
logic to `src/sdk/markdown_parser.py`:
- Define a compiled regex pattern at module level.
- Add a parsing branch in `parse_markdown_to_nodes()`.
- Apply Smart Defaults (alignment, sizing) in the transpiler, NOT the renderer.

### Step 6 — Add Test Coverage
Add test instances of the new block to **all** reference test files:
- `tests/input/test_with_title.yaml`
- `tests/input/test_without_title.yaml`
- `tests/input/test_with_title.md`
- Add unit tests in the appropriate `tests/test_*.py` file.

### Step 7 — Run Regression Tests
```bash
python -m pytest tests/ -v
```
Verify 100% pass rate with zero blast radius on existing tests.

---

## 4. Coding Conventions

All developers and AI agents MUST strictly adhere to:
- [`context/code_style.md`](code_style.md) — Python conventions & intervention safety rules.
- [`context/philosophy.md`](philosophy.md) — The Dumb Builder vs Smart Transpiler paradigm.
- [`context/ARCHITECTURE.md`](ARCHITECTURE.md) — The 4-layer stateful/stateless execution flow.
