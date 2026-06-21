# System Design: Natural Markdown-First Stateful Gateway

## Architecture Overview
The system is divided into four highly decoupled, modular layers. Lower layers have no knowledge of upper layers.

```text
  [Layer 4: Interface (mcp_server_*.py)]  <── Exposes Tools & Resources over Stdio JSON-RPC
                   │
  [Layer 3: Transpiler (sdk/markdown_parser.py)] <── Natural Markdown → Smart Defaults → Raw Dicts
                   │
  [Layer 2: State Buffer (sdk/session.py)] <── Manages memory, Pydantic gateway, draft recovery
                   │
  [Layer 1: Core Engine (report_factory.py)] <── Stateless OXML Document Compilation
```

## Modular Components

### Layer 1: Stateless Core Engine
- **Responsibility:** Takes validated Pydantic models (from `src/config/schemas.py`) and compiles them into a ДСТУ-compliant `.docx` document.
- **Core Orchestrator:** `src/report_factory.py`
- **Spacing Rule Engine:** `src/services/spacing_engine.py` (Margin collapsing, empty line injection).

### Layer 2: In-Memory Stateful SDK (`ReportSession`)
- **Location:** `src/sdk/session.py`
- **Key Mechanics:**
  - `self.nodes: List[AnyContentNode]` - Holds the parsed AST.
  - `add_chunk(yaml_string)` - Atomically validates and appends nodes. On Pydantic/File failure, rolls back memory state and returns structured JSON diagnostics.
  - `add_markdown_chunk(markdown_string)` - Transpiles natural Markdown to AST nodes via Layer 3, then validates and appends.
  - `finalize(output_path)` - Serializes Pydantic nodes to raw dicts and invokes `ReportFactory.build()`.
  - `_write_backup()` - Writes `draft_report.yaml` on every successful transaction.

### Layer 3: Natural Markdown Transpiler Bridge
- **Location:** `src/sdk/markdown_parser.py`
- **Responsibility:** A pure string-processing utility translating natural academic Markdown to raw dictionary nodes with Smart Defaults and Smart Caption Absorption.
- **Design Principles:**
  - **Smart Defaults:** Automatic formatting (paragraphs → justify, formulas → center, images → center+fit_to_page, tables → Table Grid+repeat_header)
  - **Smart Caption Absorption:** Italic captions (`*Лістинг X.Y — Name*` or `*Таблиця X.Y — Name*`) preceding code blocks or tables are automatically consumed as caption parameters
  - **Natural Syntax:** No curly-brace attributes (`{align=...}`, `{width=...}`) — clean, LLM-friendly Markdown
- **Syntax Mappings:**
  - `# Heading` ➔ `heading`
  - `*Лістинг X.Y — Description (path)*` + fenced code block ➔ `code` (with caption and optional path)
  - `![Caption](path)` ➔ `image` (Smart Defaults: center, fit_to_page)
  - `![Caption](placeholder)` ➔ `image` (placeholder: true, path rewritten to images/placeholder.png)
  - `$$LaTeX$$ (caption)` ➔ `formula` (Smart Default: center)
  - `*Таблиця X.Y — Name*` + pipe table ➔ `table` (with caption, Smart Defaults: Table Grid, repeat_header)
  - `- item` / `1. item` / `а) item` ➔ `list` (bullet/numbered/alpha_cyrillic/alpha_latin)
  - `---` or `***` ➔ `break` (page break)
  - `<br>` or `<br count=N>` ➔ `break` (line break with optional count)
- **State Machine:** Maintains `pending_caption` state for Smart Caption Absorption
  - When italic caption detected → stored in `pending_caption`
  - If next block is code/table → caption absorbed
  - If next block is different → caption flushed as paragraph
- **Integration:** Invoked via `ReportSession.add_markdown_chunk()`.

### Layer 4: Expose Interface (MCP Servers)
To avoid attention-splintering inside the LLM context, we deploy **two isolated servers** serving different guideline prompts:
1.  **`src/mcp_server_yaml.py`:** Exposes tools to ingest structured YAML blocks. Served prompt: `ai_system_prompt_yaml.md`.
2.  **`src/mcp_server_markdown.py`:** Exposes tools to ingest natural Markdown blocks. Served prompt: `ai_system_prompt_markdown.md`.

## Data Stability & Crash Recovery
If an MCP connection terminates abruptly, the state is persisted in `draft_report.yaml`. The agent can resume editing by parsing this YAML, editing blocks natively via file tools, and re-compiling.

## Smart Defaults Architecture

### Paragraph Smart Defaults
- **Input:** Plain text paragraph
- **Output:** `{type: "paragraph", text: "...", align: "justify"}`
- **Rationale:** ДСТУ 3008-2015 requires justified alignment for body text

### Formula Smart Defaults
- **Input:** `$$formula$$ (caption)`
- **Output:** `{type: "formula", content: "...", caption: "(X.Y)", align: "center"}`
- **Rationale:** Formulas are always centered in academic documents

### Image Smart Defaults
- **Input:** `![Caption](path)`
- **Output:** `{type: "image", path: "...", caption: "...", align: "center", fit_to_page: true}`
- **Rationale:** Images are centered and scaled to fit page height

### Table Smart Defaults
- **Input:** Pipe table (with optional italic caption)
- **Output:** `{type: "table", rows: [...], caption: "...", style: "Table Grid", repeat_header: true}`
- **Rationale:** Tables use grid style and repeat headers on page breaks per ДСТУ

## Smart Caption Absorption Architecture

### State Machine Flow
```
1. Parser encounters italic line matching caption pattern
   → Store in pending_caption state
   → Continue to next line

2. Parser encounters next block:
   a) If code block:
      → Extract caption from pending_caption
      → Extract path if present in parentheses
      → Attach to code node
      → Clear pending_caption
   
   b) If pipe table:
      → Extract caption from pending_caption
      → Attach to table node
      → Clear pending_caption
   
   c) If any other block (heading, paragraph, image, formula, list, break):
      → Flush pending_caption as paragraph
      → Clear pending_caption
      → Process current block

3. End of document:
   → If pending_caption not None:
      → Flush as paragraph
```

### Caption Pattern Matching
- **Listing Caption:** `^\*(Лістинг\s+\d+(?:\.\d+)*\s*—\s*(.+?))\s*(?:\(([^)]*\.[a-zA-Z0-9]+)\))?\*$`
  - Group 1: Full caption (including "Лістинг X.Y — " prefix)
  - Group 2: Caption text only (without path)
  - Group 3: Optional path in parentheses (must contain file extension)
  
- **Table Caption:** `^\*(Таблиця\s+\d+(?:\.\d+)*\s*—\s*[^*]+)\*$`
  - Group 1: Full caption (including "Таблиця X.Y — " prefix)

### Path Extraction Logic
- If caption contains `(path/to/file.ext)`:
  - Extract path to `node["path"]`
  - If code block is empty and path provided:
    - Remove `code` key (file will be loaded by renderer)
  - Caption retains full text including path in parentheses

## Natural Image Placeholder Architecture

### Detection Logic
- **Input:** `![Caption](placeholder)`
- **Pattern:** `path.lower() == "placeholder"`
- **Output:**
  ```python
  {
    "type": "image",
    "path": "images/placeholder.png",  # Rewritten
    "caption": "...",
    "placeholder": True,               # Flag set
    "align": "center",
    "fit_to_page": True
  }
  ```
- **Rationale:** LLMs can use simple "placeholder" keyword instead of dummy paths

## Error Handling & Validation

### Chunk-Level Validation
- **Strategy:** All-or-nothing at chunk level
- **Mechanism:**
  1. Parse entire chunk (Markdown or YAML)
  2. Validate all nodes against Pydantic schemas
  3. If any node fails:
     - Reject entire chunk
     - Return structured error with node_index
     - Session state remains unchanged
  4. If all nodes pass:
     - Append to session.nodes
     - Write draft_report.yaml

### Error Payload Structure
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

### Self-Healing Workflow
1. LLM submits chunk
2. Parser/transpiler processes chunk
3. Validation fails → error returned
4. LLM analyzes error (node_index, message)
5. LLM corrects chunk
6. LLM resubmits corrected chunk
7. Validation passes → chunk accepted

## Performance Considerations

### Parsing Overhead
- **Markdown Parsing:** ~0.1ms per node (regex-based)
- **YAML Parsing:** ~0.05ms per node (PyYAML)
- **Validation:** ~0.2ms per node (Pydantic)
- **Total Overhead:** ~0.3-0.4ms per node

### Memory Usage
- **Session State:** ~1KB per node (Pydantic model)
- **Draft Backup:** ~10KB per 100 nodes (YAML serialization)
- **Final Document:** ~50KB per 100 nodes (OXML compilation)

### Scalability
- **Chunk Size:** Recommended 10-50 nodes per chunk
- **Session Size:** Tested up to 500 nodes (50-page document)
- **Compilation Time:** ~2-3 seconds for 500 nodes

## Security & Isolation

### Layer Isolation
- **Layer 1 (Core):** No knowledge of Markdown or MCP
- **Layer 2 (Session):** No knowledge of OXML rendering
- **Layer 3 (Transpiler):** No knowledge of session state or MCP
- **Layer 4 (MCP):** No knowledge of OXML or Pydantic validation

### Path Security
- **MCP Config:** Uses absolute paths (no relative path traversal)
- **File Loading:** Code blocks with `path` field load from filesystem
  - **Risk:** Path traversal attack
  - **Mitigation:** Validate paths against allowed directories (future work)

### Input Validation
- **YAML:** Pydantic strict type checking
- **Markdown:** Regex pattern matching + Pydantic validation
- **File Paths:** OS-level path validation (future work)
