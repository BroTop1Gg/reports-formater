# Project Introduction & Developer Onboarding

## 1. Project Mission
The goal of `reports-formater` is to automate the creation of University Laboratory Reports that strictly adhere to academic standards (DSTU 3008-2015). It eliminates manual formatting work for students by generating `.docx` files from structured YAML content.

## 2. Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Generate report from YAML
python -m src.main input.yaml --output report.docx

# With custom template
python -m src.main input.yaml --template title_template.docx --output report.docx

# Verbose mode (debug logging)
python -m src.main input.yaml --output report.docx -v
```

**Dependencies** (`requirements.txt`): `python-docx`, `PyYAML`, `pydantic`, `matplotlib`, `pytest`.

## 3. Core Philosophy (The "Linux Way")
*   **Modular Architecture:** The system uses a Factory pattern (`ReportFactory`) and specialized **Renderers**. Each content type (Paragraph, Table, Image, Formula, etc.) has its own dedicated handler.
*   **Composition over Complexity:** Complex layouts (like Title Pages) are not hardcoded. They are either handled by **Templates** (preferred) or composed of atomic blocks (`page_break`, `paragraph`).
*   **Explicit > Implicit:** If a user wants a centered caption, they explicitly set `align: center`.
*   **Configuration-Driven:** Fonts, sizes, spacing, and alignment are managed entirely in `report_styles.json`. The code does not hardcode visual properties.

## 4. Architecture Overview
The project follows a **Template Strategy**:
1.  **Input:** YAML file (Content + Metadata).
2.  **Base:** Existing `.docx` Template (contains Title Page, Margins).\
    If no template — uses `DEFAULT_TEMPLATE.docx` (a minimal fallback for styles).
3.  **Process:**
    *   Load Template.
    *   Inject Metadata (`{{STUDENT}}` -> "Ivanov") via `PlaceholderService`.
    *   Append Content (Headings, Text, Tables, Code, Images, Formulas) to the end.
    *   Configure Header/Footer (text + page numbering) using `header_footer` style.
4.  **Output:** Final Report `.docx`.

## 5. Project Structure
```
reports-formater/
├── src/
│   ├── main.py                  # CLI entry point (argparse)
│   ├── report_factory.py         # Orchestrator, header/footer, page layout
│   ├── report_styles.json        # Global style configuration
│   ├── DEFAULT_TEMPLATE.docx     # Fallback template for Word styles
│   ├── config/
│   │   ├── models.py             # Pydantic config models (ReportConfig, StyleConfig)
│   │   ├── loader.py             # Config loading & merging
│   │   └── schemas.py            # YAML content node validation
│   ├── renderers/
│   │   ├── base.py               # BaseRenderer, RenderContext, ContentContainer
│   │   ├── paragraph_renderer.py
│   │   ├── heading_renderer.py
│   │   ├── list_renderer.py
│   │   ├── table_renderer.py
│   │   ├── image_renderer.py
│   │   ├── code_block_renderer.py
│   │   ├── formula_renderer.py
│   │   └── break_renderer.py
│   ├── services/
│   │   ├── rendering_service.py  # Renderer registry & dispatch
│   │   ├── spacing_engine.py     # DSTU spacing rules
│   │   ├── style_manager.py      # Word style fuzzy matching
│   │   └── placeholder_service.py
│   └── utils/
│       ├── docx_utils.py         # OXML helpers, get_alignment_enum
│       ├── formatting.py         # Inline markdown parser
│       └── file_io.py            # FailSafeSaver
├── tests/
│   ├── input/                    # Test YAML files & assets
│   ├── output/                   # Generated test reports
│   └── run_tests.sh              # Test runner script
├── context/                      # Architecture & developer docs
├── familiarization/              # User guide & AI system prompt
└── requirements.txt
```

## 6. Key Components
*   `src/report_factory.py`: Main orchestrator. Loads template, coordinates rendering, configures header/footer and page layout.
*   `src/services/rendering_service.py`: Dispatches content to registered renderers.
*   `src/renderers/base.py`: Core abstractions (`BaseRenderer`, `RenderContext`, `ContentContainer`).
*   `src/renderers/`: Atomic handlers for each content type:
    *   `paragraph_renderer.py` — Text with inline formatting.
    *   `heading_renderer.py` — Heading levels with TOC styles.
    *   `list_renderer.py` — Bullet, numbered, `alpha_cyrillic` (а, б, в), `alpha_latin` (a, b, c).
    *   `table_renderer.py` — Grid tables with header repetition.
    *   `image_renderer.py` — Images with alignment, captions, placeholders.
    *   `code_block_renderer.py` — Monospace code blocks with repeating captions.
    *   `formula_renderer.py` — LaTeX formulas (matplotlib + system LaTeX fallback).
    *   `break_renderer.py` — Page breaks, line breaks.
*   `src/config/models.py`: Pydantic configuration models (fonts, styles, margins).
*   `src/config/schemas.py`: Pydantic validation schemas for YAML content nodes.
*   `src/config/loader.py`: Loads and merges JSON config with YAML overrides.
*   `src/report_styles.json`: Global style configuration (fonts, spacing, indents, alignment per style).
*   `src/utils/docx_utils.py`: OXML helpers (borders, alignment, table optimization).
*   `src/utils/formatting.py`: Inline markdown parser for runs (`**bold**`, `*italic*`, `` `code` ``).

## 7. Technical Specifics (DSTU 3008-2015 Compliance)
*   **Headings:** Level 1 must be Uppercase (User responsibility in YAML).
*   **Lists:** Support for `bullet`, `numbered`, `alpha_cyrillic` (Cyrillic `а)`, `б)`), and `alpha_latin` (Latin `a.`, `b.`). Indexing extends beyond alphabet (аа, аб, etc.).
*   **Tables:** Grid style. **Header Row Repetition** is enforced via OXML (`<w:tblHeader>`).
*   **Page Numbering:** Configured via `report_styles.json` or YAML override. Supports "Spread" layout (text left, number right) with tab stops.
*   **Fonts:** Each style can define its own `font_name` in `report_styles.json`, enabling font changes without touching code.

## 8. How to Contribute
*   **Verify:** Always run tests after changes (`bash tests/run_tests.sh`). Don't forget to add new functionality to **all 3** test YAML files.
*   **Style:** Follow `context/code_style.md`.
*   **Docs:** Update `familiarization/ai_system_prompt.md` and `familiarization/user_guide.md` if adding new YAML features.

## 9. See Also
*   **[philosophy.md](philosophy.md):** Core design principles ("Dumb Builder", "Explicit > Implicit").
*   **[code_style.md](code_style.md):** Python coding standards and project-specific conventions.
*   **[ARCHITECTURE.md](ARCHITECTURE.md):** Detailed system architecture with data flow diagram.
