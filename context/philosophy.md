# PHILOSOPHY.md

## Core Concept: The "Dumb Builder" (Unix Way)

This project adheres to the **Unix philosophy**: do one thing, do it well, and be predictable.
The renderers are the "hands", not the "brain". The "brain" is the AI or the user who forms the input YAML.

### 1. Explicit over Implicit
*   **No Magic.** The script must not guess that the text "Figure 1" is a caption. If `style: caption` or `align: center` is not specified in YAML, the text renders as a standard paragraph.
*   **No Heuristics.** Do not analyze text for keywords. We are not writing Microsoft Word; we are not trying to be smarter than the user.

### 2. Configuration Hierarchy (Source of Truth)
1.  **Pydantic Models (`models.py`):** Fallback defaults. Ensures the system works even if JSON is incomplete.
2.  **JSON (`report_styles.json`):** Base configuration. Defines fonts, sizes, margins, spacing — the visual identity of the report.
3.  **YAML (Input):** Highest priority overrides. If YAML says `page_numbering: false`, we ignore JSON.

**Practical example:**
```
Font for heading = heading_base.font_name (JSON) ?? fonts.default_name (JSON) ?? "Times New Roman" (model fallback)
```

### 3. Separation of Concerns
*   **YAML (Input):** Defines structure, content, and *local* formatting (alignment of a specific block).
*   **JSON (Config):** Defines *global* style (what "normal" means, list indentation, font per style).
*   **Python (Renderers):** Dumbly translates YAML + JSON into DOCX calls. No hardcoded visual properties.

### 4. Composition over Complexity
Do not create complex block types in code (e.g., `SpecialImageBlockWithCaption`). Instead, allow the user to create an `image` node followed by a `paragraph` node with the required style in YAML. This provides flexibility without changing the code.

### 5. Configuration-Driven Design
*   If something can be configured — it must be configured, not hardcoded.
*   Fonts, sizes, alignment — everything lives in `report_styles.json`.
*   Example: the `header_footer` style controls how headers and page numbers look. Changing from `"Times New Roman"` 12pt to `"Arial"` 10pt requires only editing JSON.
### 6. Anti-Patterns (What We Consciously Do NOT Do)
*   **No text analysis.** We do NOT parse text content to determine formatting (e.g., detecting "Table 1" to apply caption style).
*   **No style guessing.** If `align` is not specified, we use the default from JSON. We never "guess" that an image caption should be centered.
*   **No template generation.** We do NOT create title pages programmatically. Title pages come from `.docx` templates with `{{PLACEHOLDERS}}`.
*   **No cross-references.** We do NOT resolve references between content nodes (e.g., "see Table 1"). This is the YAML author's responsibility.

---
**Note to AI Agents:** When modifying this project, always ask: "Am I adding hidden logic?" If yes — stop. Expose it as a configuration option instead.