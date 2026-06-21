# Project Overview: Reports-Formater AI-Native SDK

## Product Goal
Transition the "Reports-Formater" core document generator (which compiles strict, DSTU 3008-2015 compliant `.docx` academic files) into a stateful, AI-native service. The system must support two isolated, high-reliability generation interfaces: a structured YAML pipeline and a natural Markdown-First pipeline.

## The Problem
Forcing LLMs to generate massive, monolithic 50-page YAML files in one shot causes severe context window saturation, syntax formatting errors, and an inability to recover from localized schema errors. However, converting raw Markdown directly to `.docx` via standard tools breaks the highly specific, custom OXML layouts required by academic standards (e.g., center-aligned formula images with right-aligned numbering, repeated table headers on page breaks, and exact spacing rules).

## The Solution: Dual-Protocol Stateful Gateway
We implement a layered, stateful system:
1.  **The State Buffer (`ReportSession`):** Maintains the document's Abstract Syntax Tree (AST) strictly in-memory during an active session, ensuring transactional stability.
2.  **The Stdio JSON-RPC MCP Wrapper:** Exposes this state to ШІ-agents (Cursor, Claude Desktop, Aider) via standard MCP tools.
3.  **The "Markdown-First" Transpiler:** Translates natural, academic-style Markdown inputs directly into our validated, internal Pydantic AST nodes on the fly. This allows LLMs to write prose in their native tongue while preserving 100% of our strict ДСТУ OXML rendering capabilities.

## Success Metrics & Constraints (STRICT)
- **Zero Core Modifications:** The core rendering pipeline (`ReportFactory`, `SpacingEngine`, `RenderingService`, and all renderers in `src/renderers/`) must remain entirely stateless and untouched to prevent regressions.
- **Backward Compatibility:** CLI execution (`python -m src.main`) and raw YAML-chunk processing must continue to work flawlessly. We do not break userspace.
- **Zero-Trust Validation:** All-or-nothing chunk processing prevents partial state corruption in-memory.
- **Strict Layer Isolation:** The Markdown translation layer must remain a pure pre-processor, completely decoupled from OXML rendering and MCP transport mechanics.