# Project Memory

## Phase 4 Completion - 2026-06-22

### Natural Markdown Syntax Refactoring

**Status:** Complete  
**Test Results:** 73/73 passed (100% success rate)

---

### Key Technical Facts

#### 1. Markdown Parser Refactoring (Phase 4)
- **File:** `src/sdk/markdown_parser.py`
- **Purpose:** Eliminate Pandoc-style curly-brace attributes in favor of natural, LLM-friendly syntax
- **Smart Defaults Implemented:**
  - Paragraphs: `align: "justify"` (automatic)
  - Formulas: `align: "center"` (automatic)
  - Images: `align: "center"`, `fit_to_page: true` (automatic)
  - Tables: `style: "Table Grid"`, `repeat_header: true` (automatic)
- **Smart Caption Absorption:**
  - Italic captions (`*Лістинг X.Y — Name*`) before code blocks → `caption` parameter
  - Italic captions (`*Таблиця X.Y — Name*`) before tables → `caption` parameter
  - Path extraction: `*Лістинг 1.1 — Description (path/to/file.py)*` → separate `caption` and `path` fields
- **Natural Image Placeholders:** `![Caption](placeholder)` → `placeholder: true`, path rewritten to `images/placeholder.png`
- **Removed:** All `{align=...}`, `{width=...}`, `{style=...}` attribute parsing
- **Test Coverage:** 31 unit tests in `test_markdown_parser.py`

#### 2. Regex Pattern Architecture
- **LISTING_CAPTION_PATTERN:** `r'^\*(Лістинг\s+\d+(?:\.\d+)*\s*—\s*(.+?))\s*(?:\(([^)]*\.[a-zA-Z0-9]+)\))?\*$'`
  - Group 1: Full caption text (including "Лістинг X.Y — " prefix)
  - Group 2: Caption text only (without path)
  - Group 3: Optional path in parentheses (must contain file extension)
- **TABLE_CAPTION_ABSORB_PATTERN:** `r'^\*(Таблиця\s+\d+(?:\.\d+)*\s*—\s*[^*]+)\*$'`
- **Key Fix:** Caption extraction uses `cap_match.group(1)` (full caption), not `group(2)` (text only), to preserve "Лістинг X.Y — " prefix

#### 3. State Machine Implementation
- **Pending Caption Logic:** Parser maintains `pending_caption` state
  - When italic caption detected → stored in `pending_caption`
  - If next block is code/table → caption absorbed
  - If next block is different → caption flushed as paragraph
- **Flush Points:** Before headings, images, formulas, lists, page breaks, line breaks, and at end of document

#### 4. Test Files Update
- **`tests/input/test_with_title.md`:** Rewritten with natural syntax
  - Removed all `{...}` attributes
  - Used italic captions for code blocks and tables
  - Used `![Caption](placeholder)` for image placeholders
- **`tests/input/test_with_title.yaml`:** Updated to match MD structure
  - Removed "2.2 Paragraph Alignment" section (not in MD)
  - Changed `---` to `<br>` for line break (YAML uses `style: line`)
- **`tests/test_markdown_parser.py`:** Complete overhaul
  - Tests for Smart Defaults (paragraph, formula, image, table)
  - Tests for Smart Caption Absorption (with/without path)
  - Tests for natural image placeholders
  - Tests for caption flush when not followed by code/table

#### 5. System Prompts Update
- **`familiarization/ai_system_prompt_markdown.md`:** Updated with natural syntax specification
  - Explicit prohibition of curly-brace attributes
  - Smart Defaults documentation
  - Smart Caption Absorption examples
  - Natural image placeholder syntax
- **`familiarization/ai_system_prompt_yaml.md`:** Minor updates

#### 6. Pytest Configuration
- **File:** `tests/conftest.py`
- **Purpose:** Fix module import issues
- **Implementation:** `sys.path.insert(0, project_root)` to enable `from src.sdk...` imports
- **Result:** All tests run without import errors across different environments

#### 7. Test Coverage Summary (Phase 4)
- `test_markdown_parser.py`: 31 tests (natural syntax parsing)
- `test_mcp_transport.py`: 3 tests (MCP protocol)
- `test_e2e_identity.py`: 3 tests (structural parity)
- `test_self_healing_sim.py`: 8 tests (validation & recovery)
- `test_mcp_server.py`: 15 tests (MCP registration)
- `test_sdk_session.py`: 12 tests (session API)
- `test_cli_markdown.py`: 1 test (CLI markdown compilation)
- **Total:** 73 tests, 100% pass rate, ~12s execution time

---

### Architecture Decisions (Phase 4)

#### Decision 1: Smart Defaults Over Explicit Attributes
**Rationale:** LLMs struggle with complex attribute syntax. Automatic defaults reduce cognitive load and syntax errors.  
**Impact:** Cleaner Markdown, fewer parsing errors, faster LLM generation.

#### Decision 2: Smart Caption Absorption
**Rationale:** Natural Markdown doesn't have a standard way to associate captions with code blocks/tables. Italic paragraphs preceding blocks provide intuitive caption association.  
**Impact:** LLMs write `*Caption*` followed by block → parser automatically links them.

#### Decision 3: Path Extraction from Captions
**Rationale:** Code blocks often reference external files. Embedding path in caption parentheses keeps syntax clean while providing file reference.  
**Impact:** `*Лістинг 1.1 — Description (path/to/file.py)*` → parser extracts both caption and path.

#### Decision 4: Natural Image Placeholders
**Rationale:** `![Caption](placeholder)` is more intuitive than `![Caption](path){placeholder=true}`. Parser rewrites "placeholder" to dummy path and sets flag.  
**Impact:** Simpler syntax for LLMs, automatic placeholder generation.

#### Decision 5: Regex Group Architecture
**Rationale:** Initial implementation used `group(2)` for caption (text only), but YAML expects full caption including "Лістинг X.Y — " prefix. Changed to `group(1)` to preserve full caption.  
**Impact:** E2E parity test passes, caption text matches YAML exactly.

---

### Production Readiness Checklist (Phase 4)

- [x] Natural Markdown syntax implemented
- [x] Smart Defaults working correctly
- [x] Smart Caption Absorption validated
- [x] Path extraction from captions tested
- [x] Natural image placeholders working
- [x] All 73 tests passing
- [x] E2E parity with YAML pipeline verified
- [x] System prompts updated
- [x] Test files updated
- [x] Pytest configuration fixed

**Status:** Natural Markdown Syntax is production-ready for LLM-driven report generation.

---

### Upgrade Path (Future Work)

1. **Performance Benchmarking:** Measure parsing overhead for large documents
2. **Additional Markdown Elements:** Footnotes, citations, definition lists
3. **Real-time Preview:** Generate incremental .docx for live preview
4. **Template Customization API:** Allow users to define custom templates
5. **Multi-language Support:** Extend prompts and validation for other languages
6. **Schema Versioning:** Add backward compatibility for YAML format changes
7. **Concurrent Chunks:** Investigate parallel chunk submission (if MCP transport supports)

---

## Phase 3 Completion - 2026-06-21

### Dual-Protocol Gateway & Documentation

**Status:** Complete  
**Test Results:** 79/79 passed (100% success rate)

---

### Key Technical Facts

#### 1. Markdown Transpiler Implementation (Phase 3 - Initial)
- **File:** `src/sdk/markdown_parser.py`
- **Purpose:** Convert Pandoc-style Markdown to internal AST nodes
- **Supported Elements:**
  - Headings: `# H1`, `## H2`, etc.
  - Code blocks: ` ```python {caption="..."}` with metadata
  - Images: `![caption](path){width=10 fit_to_page=true}`
  - Formulas: `$$E=mc^2$$ (1.1) {align=center}`
  - Tables: Markdown tables with `Table: Caption` syntax
  - Lists: Bullet, numbered, alpha (Cyrillic/Latin)
  - Paragraphs: With trailing attributes `{align=justify}`
- **Integration:** `ReportSession.add_markdown_chunk()` method
- **Test Coverage:** 38 unit tests in `test_markdown_parser.py`

#### 2. Dual MCP Servers
- **YAML Server:** `src/mcp_server_yaml.py`
  - Tools: `init_report`, `submit_chunk`, `finalize_report`
  - Resource: `dstu://guidelines` → `ai_system_prompt_yaml.md`
  - Use case: Precise control, programmatic generation

- **Markdown Server:** `src/mcp_server_markdown.py`
  - Tools: `init_report`, `submit_markdown_chunk`, `finalize_report`
  - Resource: `dstu://guidelines` → `ai_system_prompt_markdown.md`
  - Use case: LLM-native writing, faster iteration

#### 3. Structural Parity Verified
- **Test File:** `tests/test_e2e_identity.py`
- **Tests:**
  - `test_monolithic_vs_chunked_parity`: YAML vs chunked YAML
  - `test_chunked_session_accumulates_correctly`: Node accumulation
  - `test_monolithic_yaml_vs_mcp_markdown_parity`: YAML vs Markdown
- **Finding:** All three paths produce 100% identical output
- **Verified Elements:**
  - Paragraph count and text content
  - Table structure (rows, columns, cell values)
  - Inline formatting (bold, italic)
  - Paragraph alignment
  - Page margins and layout

#### 4. Self-Healing Validation Model
- **Test File:** `tests/test_self_healing_sim.py`
- **Tests:** 8 tests (7 YAML + 1 Markdown)
- **Validation Strategy:** All-or-nothing at chunk level
- **Error Payload Structure:**
  ```python
  {
    "status": "error",
    "errors": [
      {
        "node_index": int,      # Position in chunk
        "type": str,            # validation_error | yaml_parse_error | file_not_found
        "message": str,         # Pydantic error or custom message
        "node": dict            # Original malformed node
      }
    ]
  }
  ```
- **Session State:** Remains stable after errors (no partial corruption)
- **Recovery Workflow:** Error → Analyze → Correct → Resubmit → Accept

#### 5. MCP Client Configuration
- **Config File:** `mcp_config.json`
- **Absolute Paths Used:**
  - Python: `/home/acer/Projects/DevelopingUtilities/reports-formater/venv/bin/python`
  - YAML Server: `/home/acer/Projects/DevelopingUtilities/reports-formater/src/mcp_server_yaml.py`
  - Markdown Server: `/home/acer/Projects/DevelopingUtilities/reports-formater/src/mcp_server_markdown.py`
  - PYTHONPATH: `/home/acer/Projects/DevelopingUtilities/reports-formater`
- **Compatibility:** Cursor, Claude Desktop, standard MCP CLI hosts

#### 6. Documentation Overhaul
- **README.md:** Added Dual-Protocol Gateway section with MCP configuration examples
- **tutorial/TUTORIAL.md:** Rewritten for MCP-first workflow
- **familiarization/ai_system_prompt_markdown.md:** New Markdown-specific prompt
- **familiarization/ai_system_prompt_yaml.md:** YAML-specific prompt (renamed from ai_system_prompt.md)

---

### Architecture Decisions (Phase 3)

#### Decision 1: Dual-Protocol Gateway
**Rationale:** Different use cases require different input formats. YAML provides precise control; Markdown enables LLM-native writing.  
**Impact:** Users can choose their preferred format without sacrificing functionality.

#### Decision 2: Markdown Transpiler as Separate Layer
**Rationale:** Keeps transpilation logic isolated from core rendering. Enables independent testing and future format additions.  
**Impact:** Clean separation of concerns; easy to extend with new input formats.

#### Decision 3: All-or-Nothing Chunk Validation
**Rationale:** Prevents partial state corruption. If any node in a chunk fails, the entire chunk is rejected.  
**Impact:** Session state remains consistent; LLM can retry with corrected payload.

#### Decision 4: Absolute Paths in MCP Config
**Rationale:** MCP clients require explicit paths; relative paths cause resolution issues.  
**Impact:** Configuration is portable but requires path updates if project moves.

#### Decision 5: Node-Level Error Indexing
**Rationale:** LLM needs to know which node failed to provide targeted correction.  
**Impact:** Error payloads include `node_index` for precise debugging.

---

## Phase 2 Completion - 2026-06-20

### MCP Server Implementation

**Status:** Complete

---

### Key Technical Facts

#### 1. Stdio JSON-RPC MCP Wrapper
- **Implementation:** Two separate MCP servers (YAML and Markdown)
- **Protocol:** Standard MCP over stdio JSON-RPC
- **Tools Exposed:**
  - `init_report(metadata)` - Initialize session with metadata
  - `submit_chunk(yaml_content)` - Submit YAML chunk (YAML server)
  - `submit_markdown_chunk(markdown_content)` - Submit Markdown chunk (Markdown server)
  - `finalize_report(output_path)` - Compile and save .docx
- **Resources Exposed:**
  - `dstu://guidelines` - Returns system prompt (YAML or Markdown)

#### 2. Crash Recovery
- **Mechanism:** `draft_report.yaml` written on every successful transaction
- **Recovery Workflow:** Parse YAML → edit blocks → re-compile
- **State Preservation:** Session state remains stable across crashes

---

## Phase 1 Completion - 2026-06-19

### Core Engine & State Buffer

**Status:** Complete

---

### Key Technical Facts

#### 1. ReportFactory (Stateless Core Engine)
- **File:** `src/report_factory.py`
- **Responsibility:** Compile validated Pydantic models into ДСТУ-compliant .docx
- **Architecture:** Stateless, no in-memory state between builds
- **Components:**
  - SpacingEngine: Margin collapsing, empty line injection
  - RenderingService: Orchestrates all renderers
  - Renderers: Paragraph, heading, table, image, formula, list, code block

#### 2. ReportSession (In-Memory State Buffer)
- **File:** `src/sdk/session.py`
- **Responsibility:** Manage document AST during active session
- **Key Mechanics:**
  - `self.nodes: List[AnyContentNode]` - Holds parsed AST
  - `add_chunk(yaml_string)` - Atomically validates and appends nodes
  - `finalize(output_path)` - Serializes nodes and invokes ReportFactory
  - `_write_backup()` - Writes `draft_report.yaml` on every transaction
- **Validation:** All-or-nothing at chunk level (Pydantic validation)

#### 3. Pydantic Validation Layer
- **Files:** `src/config/schemas.py`
- **Purpose:** Strict type validation for all content nodes
- **Node Types:**
  - HeadingData, ParagraphData, CodeBlockData, ImageData
  - TableData, FormulaData, ListData, BreakData
- **Validation Rules:**
  - Required fields enforced
  - Type constraints (e.g., heading level 1-9)
  - Cross-field validation (e.g., code block must have code or path)

---

## Project-Wide Technical Facts

### Technology Stack
- **Language:** Python 3.12
- **Core Libraries:**
  - `python-docx` - Word document generation
  - `pydantic` - Data validation
  - `pyyaml` - YAML parsing
  - `re` - Regular expressions (Markdown parsing)
- **MCP Libraries:**
  - `mcp` - Model Context Protocol implementation
- **Testing:**
  - `pytest` - Test framework
  - `unittest` - Test cases (legacy)

### File Structure
```
reports-formater/
├── src/
│   ├── config/
│   │   ├── models.py          # Configuration models
│   │   └── schemas.py         # Pydantic validation schemas
│   ├── renderers/             # OXML rendering components
│   ├── sdk/
│   │   ├── markdown_parser.py # Markdown transpiler (Phase 4)
│   │   └── session.py         # ReportSession (state buffer)
│   ├── services/              # Spacing engine, style manager
│   ├── mcp_server_yaml.py     # YAML MCP server
│   ├── mcp_server_markdown.py # Markdown MCP server
│   ├── main.py                # CLI entry point
│   └── report_factory.py      # Core engine orchestrator
├── tests/
│   ├── input/                 # Test input files (YAML, MD)
│   ├── output/                # Generated test outputs
│   ├── conftest.py            # Pytest configuration
│   └── test_*.py              # Test suites
├── familiarization/           # System prompts for AI agents
├── project_context/           # Project documentation
└── venv/                      # Virtual environment
```

### Configuration Files
- **`report_styles.json`** - Document styling (fonts, spacing, margins)
- **`mcp_config.json`** - MCP server configuration (absolute paths)
- **`pyproject.toml`** - Project metadata and dependencies

### Key Metrics (Current)
- **Total Tests:** 73
- **Pass Rate:** 100%
- **Execution Time:** ~12 seconds
- **Code Coverage:** High (all major components tested)
- **E2E Parity:** 100% (YAML ↔ Markdown)
