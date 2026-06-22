# Philosophy: Dumb Builder Backend with Smart Transpiler Frontend

This project follows the **Unix philosophy**: do one thing, do it well, and be
predictable. To support both rigid programmatic pipelines and natural AI-driven
content generation, the system strictly segregates its intelligence across
architectural layers.

---

## The Core Paradigm

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Interface & Transport (CLI, MCP)                  │
│  Layer 3: Markdown Transpiler — SMART (heuristics allowed)  │
│  Layer 2: Session & Validation — EXPLICIT (no heuristics)   │
│  Layer 1: Rendering Core — DUMB (no heuristics, ever)       │
└─────────────────────────────────────────────────────────────┘
```

**Layers 1 & 2 are strictly explicit.** They never guess, never infer, never
analyze text content. They only read validated fields from typed Pydantic nodes.

**Layer 3 is smart.** It uses heuristics, regex, and text analysis to reduce
cognitive load on LLMs and human authors writing natural Markdown.

---

## Layer 1 & 2: "No Heuristics" Zone

Applies to: `src/renderers/*`, `ReportFactory`, `SpacingEngine`, `RenderingService`,
`PlaceholderService`, `docx_utils`, and all Pydantic schemas in `src/config/schemas.py`.

### Rules

1. **Explicit over Implicit.**
   If `style: caption` is not provided in the Pydantic node, it renders as a
   normal paragraph. The renderer never guesses intent.

2. **No Text Analysis.**
   Renderers DO NOT parse text content to determine formatting. They do not
   scan for the word "Таблиця" to apply caption styles. They do not look for
   "Лістинг" to detect code listings. They only read boolean/string flags from
   the validated AST.

3. **Zero-Trust Validation.**
   Every node passes through Pydantic V2 validation before entering the render
   pipeline. Invalid nodes are rejected with a diagnostic error — never silently
   coerced.

4. **No State Mutation During Rendering.**
   `RenderContext` and `ContentContainer` are passed down the chain. Renderers
   do not modify the global AST state or session buffer.

5. **Configuration-Driven.**
   If something can be configured visually, it MUST be configured — never
   hardcoded. Fonts, sizes, alignment, spacing — everything lives in
   `report_styles.json`.

---

## Layer 3: Smart Transpiler (Heuristics Allowed)

Applies to: `src/sdk/markdown_parser.py`

This is the **only** layer permitted to use heuristics, regex analysis, and
smart defaults. Its job is to make natural Markdown "just work" for LLMs and
human authors without requiring them to specify every visual parameter.

### Smart Defaults

The transpiler automatically applies sensible defaults so authors don't have to:

| Element   | Smart Default Applied                          |
|-----------|------------------------------------------------|
| Paragraph | `align: justify`                               |
| Image     | `align: center`, `fit_to_page: true`           |
| Formula   | `align: center`                                |
| Table     | `style: "Table Grid"`, `repeat_header: true`   |

### Smart Caption Absorption

The transpiler uses regex to detect caption patterns and automatically absorbs
them into the next block element:

- A paragraph matching `Лістинг 1.1 — Description` before a fenced code block
  is consumed as the code block's `caption` field.
- A paragraph matching `Таблиця 1.1 — Description` before a pipe table is
  consumed as the table's `caption` field.
- If the caption pattern includes a file path in parentheses, it is extracted
  as the `path` field (e.g., `Лістинг 1.1 — Script (src/main.py)`).

This means the author writes clean, natural Markdown:

```markdown
Лістинг 1.1 — Main processing script
```python
def process():
    pass
```
```

And the transpiler produces a fully-specified AST node:

```json
{
  "type": "code",
  "code": "def process():\n    pass",
  "caption": "Лістинг 1.1 — Main processing script",
  "path": null,
  "language": "python"
}
```

### Natural Placeholder Detection

When an image path is literally `placeholder`, the transpiler sets
`placeholder: true` and routes to a generated placeholder image. No special
syntax required.

---

## Configuration Hierarchy (Source of Truth)

Priority cascades from lowest to highest:

| Priority | Source                           | Description                              |
|----------|----------------------------------|------------------------------------------|
| 1 (Low)  | `src/config/models.py`           | Pydantic fallback defaults               |
| 2        | `src/report_styles.json`         | Base visual identity (fonts, margins)    |
| 3 (High) | YAML / Markdown Front-Matter     | Runtime overrides (`page_numbering`, etc)|

**Practical example:**
```
Font for heading =
    heading_base.font_name (JSON)
    ?? fonts.default_name (JSON)
    ?? "Times New Roman" (Pydantic model fallback)
```

---

## Composition over Complexity

Do NOT create complex block types in code (e.g., `SpecialImageBlockWithCaption`).
Instead, rely on AST composition: an `image` node with a `caption` attribute,
which the renderer translates into an invisible layout table. This provides
flexibility without bloating the rendering core.

---

## Anti-Patterns (What We Consciously Do NOT Do)

1. **No template generation.** Title pages come from `.docx` templates with
   `{{PLACEHOLDERS}}`, not from code.

2. **No cross-reference resolution.** We do NOT auto-link "see Table 1" to the
   actual table. This is the author's responsibility.

3. **No state mutation during rendering.** Renderers are pure functions of
   (context, data) → OXML side effects.

4. **No heuristics in Layer 1 or 2.** All guessing happens in Layer 3 only.

---

## The Golden Rule

When modifying this project, always ask:

> "Am I working in Layer 1/2 (Core) or Layer 3 (Transpiler)?"

- **If Core:** Keep it dumb, explicit, and reliant on Pydantic. No text analysis.
- **If Transpiler:** Keep it smart, regex-driven, and natural for the user.
