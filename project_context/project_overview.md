# Project Overview: Reports-Formater AI-Native SDK

## Product Goal
Transition the "Reports-Formater" core document generator (which compiles strict, DSTU 3008-2015 compliant `.docx` academic files) into a stateful, AI-native service. The system supports two isolated, high-reliability generation interfaces: a structured YAML pipeline and a natural Markdown-First pipeline.

## The Problem
Forcing LLMs to generate massive, monolithic 50-page YAML files in one shot causes severe context window saturation, syntax formatting errors, and an inability to recover from localized schema errors. However, converting raw Markdown directly to `.docx` via standard tools breaks the highly specific, custom OXML layouts required by academic standards (e.g., center-aligned formula images with right-aligned numbering, repeated table headers on page breaks, and exact spacing rules).

## The Solution: Dual-Protocol Stateful Gateway with Natural Markdown
We implement a layered, stateful system:
1.  **The State Buffer (`ReportSession`):** Maintains the document's Abstract Syntax Tree (AST) strictly in-memory during an active session, ensuring transactional stability.
2.  **The Stdio JSON-RPC MCP Wrapper:** Exposes this state to ШІ-agents (Cursor, Claude Desktop, Aider) via standard MCP tools.
3.  **The "Natural Markdown-First" Transpiler:** Translates natural, academic-style Markdown inputs directly into our validated, internal Pydantic AST nodes on the fly. This allows LLMs to write prose in their native tongue while preserving 100% of our strict ДСТУ OXML rendering capabilities.

### Key Features (Phase 4)
- **Smart Defaults:** Automatic formatting for all elements (paragraphs → justify, formulas → center, images → center+fit_to_page, tables → Table Grid+repeat_header)
- **Smart Caption Absorption:** Italic captions (`*Лістинг X.Y — Name*` or `*Таблиця X.Y — Name*`) preceding code blocks or tables are automatically consumed as caption parameters
- **Natural Image Placeholders:** `![Caption](placeholder)` automatically generates placeholder images
- **Path Extraction:** Listing captions can include file paths in parentheses for automatic code loading
- **Zero Curly-Brace Attributes:** Clean, LLM-friendly syntax without complex `{align=...}` or `{width=...}` notation

## Success Metrics & Constraints (STRICT)
- **Zero Core Modifications:** The core rendering pipeline (`ReportFactory`, `SpacingEngine`, `RenderingService`, and all renderers in `src/renderers/`) remains entirely stateless and untouched to prevent regressions.
- **Backward Compatibility:** CLI execution (`python -m src.main`) and raw YAML-chunk processing continue to work flawlessly. We do not break userspace.
- **Zero-Trust Validation:** All-or-nothing chunk processing prevents partial state corruption in-memory.
- **Strict Layer Isolation:** The Markdown translation layer remains a pure pre-processor, completely decoupled from OXML rendering and MCP transport mechanics.
- **100% E2E Parity:** YAML and Markdown pipelines produce identical output (verified by `test_monolithic_yaml_vs_mcp_markdown_parity`).

## Current Status (Phase 4 Complete - 2026-06-22)
- **Total Tests:** 73 (100% pass rate)
- **Execution Time:** ~12 seconds
- **Markdown Parser:** Natural syntax with Smart Defaults and Caption Absorption
- **Structural Parity:** 100% (YAML ↔ Markdown)
- **Production Ready:** Yes

## Architecture Highlights
```
┌─────────────────────────────────────────────────────────┐
│                    MCP Clients                           │
│  (Cursor, Claude Desktop, AI Agents)                    │
└────────────┬─────────────────────┬──────────────────────┘
             │                     │
             │ YAML                │ Natural Markdown
             ▼                     ▼
┌────────────────────┐   ┌────────────────────────┐
│ mcp_server_yaml.py │   │ mcp_server_markdown.py │
│  submit_chunk()    │   │ submit_markdown_chunk()│
└────────┬───────────┘   └────────┬───────────────┘
         │                        │
         │                        ▼
         │              ┌──────────────────────────┐
         │              │ markdown_parser.py       │
         │              │ (Smart Defaults +        │
         │              │  Caption Absorption)     │
         │              └────────┬─────────────────┘
         │                       │
         └───────┬───────────────┘
                 │
                 ▼
      ┌──────────────────┐
      │  ReportSession   │
      │  (session.py)    │
      │  - add_chunk()   │
      │  - nodes[]       │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ ReportFactory    │
      │ (report_factory) │
      └────────┬─────────┘
               │
               ▼
          .docx output
```

## Natural Markdown Syntax Examples
```markdown
# ЗАГОЛОВОК

Звичайний параграф (автоматично вирівнюється по ширині).

*Лістинг 1.1 — Приклад коду (src/example.py)*
```python
def hello():
    print("Hello, World!")
```

*Таблиця 1.1 — Результати тестів*
| Тест | Результат |
|------|-----------|
| A    | Pass      |
| B    | Fail      |

![Рисунок 1.1 — Скріншот](images/screenshot.png)
![Рисунок 1.2 — Плейсхолдер](placeholder)

$$E = mc^2$$ (1.1)
```

## Key Benefits
1. **LLM-Friendly:** Natural syntax reduces cognitive load and syntax errors
2. **Automatic Formatting:** Smart Defaults ensure ДСТУ compliance without manual configuration
3. **Intuitive Captions:** Italic captions before blocks are automatically linked
4. **Zero Dependencies:** Markdown parser uses only stdlib `re` module
5. **Full Parity:** YAML and Markdown pipelines produce identical output
6. **Self-Healing:** Structured error payloads enable LLM recovery from validation failures
