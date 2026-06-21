# System Design: Stateful Dual-Protocol Gateway

## Architecture Overview
The system is divided into four highly decoupled, modular layers. Lower layers have no knowledge of upper layers.

```text
  [Layer 4: Interface (mcp_server_*.py)]  <── Exposes Tools & Resources over Stdio JSON-RPC
                   │
  [Layer 3: Transpiler (sdk/markdown_parser.py)] <── Translates Markdown to Raw Python Dicts
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
  - `finalize(output_path)` - Serializes Pydantic nodes to raw dicts and invokes `ReportFactory.build()`.
  - `_write_backup()` - Writes `draft_report.yaml` on every successful transaction.

### Layer 3: Markdown Transpiler Bridge (New)
- **Location:** `src/sdk/markdown_parser.py`
- **Responsibility:** A pure string-processing utility translating academic extended-Markdown (Pandoc-style) to raw dictionary nodes.
- **Syntax Mappings:**
  - `# Heading` ➔ `heading`
  - `Fenced code blocks` ➔ `code` (extracts caption parameters from `{...}`)
  - `![Caption](path){width=10}` ➔ `image`
  - `$$LaTeX$$ (caption)` ➔ `formula`
  - `Pipe tables + : Caption` ➔ `table`
- **Integration:** Invoked via `ReportSession.add_markdown_chunk()`.

### Layer 4: Expose Interface (MCP Servers)
To avoid attention-splintering inside the LLM context, we deploy **two isolated servers** serving different guideline prompts:
1.  **`src/mcp_server_yaml.py`:** Exposes tools to ingest structured YAML blocks. Served prompt: `ai_system_prompt_yaml.md`.
2.  **`src/mcp_server_markdown.py`:** Exposes tools to ingest natural Markdown blocks. Served prompt: `ai_system_prompt_markdown.md`.

## Data Stability & Crash Recovery
If an MCP connection terminates abruptly, the state is persisted in `draft_report.yaml`. The agent can resume editing by parsing this YAML, editing blocks natively via file tools, and re-compiling.