# Reports-Formater

## Announcement

![](other/glory_to_ukraine.png)

Use this project only if:

- You **condemn Russia and its military aggression against Ukraine**
- You **recognize that Russia is an occupant that unlawfully invaded a sovereign state**
- You **support Ukraine's territorial integrity, including its claims over temporarily occupied territories of Crimea and Donbas**
- You **reject false narratives perpetuated by Russian state propaganda**

Otherwise, leave this project immediately

Putin idi nachui.

---

## About The Project

Formatting technical documentation and academic reports strictly adhering to local standards (e.g., DSTU 3008-2015) is a highly time-consuming process. Manual formatting in word processors often leads to formatting errors, broken cross-references, and lost time on styling rather than content creation. In addition, formatting of reports currently is the only bottleneck for working with an AI.

**Reports-Formater** is an AI-native, dual-protocol document compiler designed to fully automate the generation of `.docx` documents from structured YAML or natural academic Markdown content.

### Designed for AI CLI-Agents

This project was built with AI integration in mind. It is optimized to minimize the cognitive load on Language Models. Even less capable models can flawlessly generate the required YAML structure because the visual styling (fonts, alignments, margins) is completely abstracted away into configuration files. 

By using this tool, CLI-Agents (such as Qwen, Gemini, etc.) can generate technical documentation and immediately compile it into a ready-to-print `.docx` file directly in the terminal, completely avoiding manual formatting.

## Features

- **Dual-Protocol Gateway:** Choose between structured YAML or natural academic Markdown-First input formats.
- **MCP Integration:** Native Model Context Protocol (stdio transport) servers for seamless AI client integration (Claude Desktop, etc.).
- **YAML-Driven Content:** Write your paragraphs, headings, lists, tables, code blocks, and formulas in structured YAML.
- **Markdown-First Mode:** Write reports in natural Pandoc-style Markdown (no visual formatting tags) with automatic transpilation to internal AST.
- **Programmatic Python SDK:** Seamlessly integrate the stateful document buffer (`ReportSession`) directly into your own custom Python pipelines.
- **Strict Compliance:** Automated enforcement of heading styles, paragraph spacing, and page numbering layouts.
- **Complex Structures:** Support for repeating table headers across pages, code block captions, and multi-level alphabetic lists.
- **Formula Rendering:** Advanced mathematical formulas using a two-tier hybrid system (Matplotlib + System LaTeX with full Cyrillic support).
- **Template Support:** Use `.docx` templates with placeholders (e.g., `{{TITLE}}`, `{{AUTHOR}}`) to automatically generate complex title pages.

### Compatibility Note
The generated `.docx` files use advanced OXML structures.

- **Looks good in:** LibreOffice Writer, Google Docs.
- **Looks weird in:** MS Word (Online) - known bugs with tables and headers.
- **Not tested in:** MS Word (Desktop)

## Installation

### Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes: `python-docx`, `PyYAML`, `pydantic`, `matplotlib`, `pytest`, `mcp`.
Requires **Python 3.10+**.

### LaTeX Support (Optional but Recommended)

For rendering mathematical formulas, this project uses a two-tier strategy:
1. **Matplotlib (Built-in):** Handles standard mathematical expressions seamlessly in the background.
2. **System LaTeX (Fallback):** Automatically used when Matplotlib encounters complex structures it cannot render natively (e.g., `\begin{cases}`).

If system LaTeX is not installed, complex formulas will be rendered as text placeholders.

**To install LaTeX with Cyrillic support:**
```bash
# Ubuntu / Debian
sudo apt install texlive-full texlive-lang-cyrillic
```
Ensure that `latex` and `dvipng` are accessible in your `$PATH`.

## Usage

### 1. CLI Execution

#### Compile YAML Content:
```bash
python -m src.main input.yaml --output report.docx
```

#### Compile Natural Markdown (with YAML Front-Matter):
Write your metadata inside `---` delimiters at the very top of your `.md` file, then compile it directly:
```bash
python -m src.main input.md --output report.docx
```

#### Other CLI Arguments:
Generate using a specific title page template:
```bash
python -m src.main input.yaml --template title_template.docx --output report.docx
```

Verbose mode for debugging:
```bash
python -m src.main input.yaml --output report.docx -v
```

### 2. Programmatic Python SDK

You can use the stateful SDK inside your own custom Python scripts to build reports incrementally in memory:

```python
from pathlib import Path
from src.sdk.session import ReportSession

# Initialize session with metadata
session = ReportSession(metadata={"VERSION": "1.0", "CURRENT_YEAR": "2026"})

# Add Markdown chunk (Smart Defaults and Caption Absorption are applied automatically)
session.add_markdown_chunk("# ЛАБОРАТОРНА РОБОТА № 5")
session.add_markdown_chunk("Тема: Розробка ПЗ.\n\nМета: Дослідити...")

# Finalize and compile .docx
output_path = Path("output.docx")
session.finalize(output_path)
```

### 3. AI Integration (Legacy File Method)

To generate documents using an LLM:
1. Provide the LLM with the prompt found in `familiarization/ai_system_prompt_yaml.md` or `familiarization/ai_system_prompt_markdown.md`.
2. The AI will output a correctly structured file.
3. Pass the generated file to this CLI tool to build the Word document.

Or, if you using CLI-Agent, they can automatically create files and run the tool. But you also need give them instructions to do that `familiarization/ai_system_prompt_markdown.md`, `familiarization/user_guide.md`.

### 4. Dual-Protocol Gateway (MCP Integration)

The project provides two Model Context Protocol (MCP) servers for seamless AI client integration:

#### YAML Protocol Server
For structured, schema-driven content generation:
```bash
python -m src.mcp_server_yaml
```
- Exposes tools: `init_report`, `submit_chunk`, `finalize_report`
- Resource: `dstu://guidelines` (YAML schema reference `ai_system_prompt_yaml.md`)
- Best for: Precise control over document structure

#### Markdown Protocol Server
For natural, Pandoc-style Markdown input:
```bash
python -m src.mcp_server_markdown
```
- Exposes tools: `init_report`, `submit_markdown_chunk`, `finalize_report`
- Resource: `dstu://guidelines` (Markdown syntax reference `ai_system_prompt_markdown.md`)
- Best for: Writing reports in natural Markdown with automatic transpilation

#### Client Configuration (mcp_config.json)
We provide `mcp_config.json.example` as a template. Rename it to `mcp_config.json`, configure your absolute paths, and register it in your MCP host (like Claude Desktop).

```json
{
  "mcpServers": {
    "reports-formatter-yaml": {
      "command": "/path/to/reports-formater/venv/bin/python",
      "args": ["-m", "src.mcp_server_yaml"],
      "env": {
        "PYTHONPATH": "/path/to/reports-formater"
      }
    },
    "reports-formatter-markdown": {
      "command": "/path/to/reports-formater/venv/bin/python",
      "args": ["-m", "src.mcp_server_markdown"],
      "env": {
        "PYTHONPATH": "/path/to/reports-formater"
      }
    }
  }
}
```

Both servers provide real-time validation, stateful session management, and automatic .docx generation through the MCP protocol.

---

## AI Autopilot Developer Integration (Aashari/Aider Protocol)

This repository is designed from the ground up to be maintained and extended by **autonomous developer agents** (such as Hermes Agent, Claude Code, etc.).

We maintain a strict stateful context directory to allow any incoming agent to instantly align with our codebase constraints:
- `project_context/project_overview.md` - Product goals and constraints.
- `project_context/system_design.md` - Multi-layered architecture boundaries.
- `project_context/tech_environment.md` - Absolute paths and testing scripts.
- `project_context/active_development.md` - Current sprint progress and steps.
- `project_context/memory.md` - Historical log of key architectural decisions.

### Initializing Agent Soul
To prevent agentic token-wasting paranoia and enforce pragmatic, cost-efficient co-authoring, always copy our customized agent doctrine to your global agent environment before initiating a coding session:
```bash
cp project_context/SOUL.md ~/.hermes/SOUL.md
```

---

## Try it Yourself (Tutorial)

Want to try generate document? Check out the [`tutorial/`](tutorial/) folder for a simple step-by-step guide. It includes sample programming tasks to feed to your AI and an empty YAML file to practice with.

If you ever need help understanding how this project works, simply copy the following files and ask your AI to explain them to you:
- [`context/ARCHITECTURE.md`](context/ARCHITECTURE.md)
- [`context/introduction.md`](context/introduction.md)
- [`familiarization/user_guide.md`](familiarization/user_guide.md)
- [`familiarization/ai_system_prompt_markdown.md`](familiarization/ai_system_prompt_markdown.md)

## Documentation

For developers, contributors, and AI agents analyzing this repository, refer to the general documentation to understand context of the project:

| File | Purpose |
|------|---------|
| [`tutorial/TUTORIAL.md`](tutorial/TUTORIAL.md) | Hands-on guide: generating reports with AI |
| [`context/introduction.md`](context/introduction.md) | Project introduction, quick start, and onboarding |
| [`context/ARCHITECTURE.md`](context/ARCHITECTURE.md) | System architecture and data flow |
| [`context/code_style.md`](context/code_style.md) | Coding standards and intervention protocols |
| [`context/philosophy.md`](context/philosophy.md) | Core design principles ("Dumb Builder") and anti-patterns |
| [`familiarization/ai_system_prompt_yaml.md`](familiarization/ai_system_prompt_yaml.md) | System prompt for LLMs to generate YAML content |
| [`familiarization/ai_system_prompt_markdown.md`](familiarization/ai_system_prompt_markdown.md) | System prompt for LLMs to generate Markdown content |
| [`familiarization/user_guide.md`](familiarization/user_guide.md) | Comprehensive System Manual (CLI, SDK, and MCP) |
| [`other/derzhstandart_3008_2015.pdf`](other/derzhstandart_3008_2015.pdf) | Official DSTU 3008-2015 Ukrainian Standard specification (PDF) |

## Acknowledgements

Artificial Intelligence played a significant role in the development and maintenance of this project. AI models helped to design the architecture, write the documentation, implement tests, and solve complex layout challenges.

Models used during development:
- **Qwen 3.7 Plus** (Fireworks.ai)
- **Hermes Agent**
- Gemini 3.1 Pro, Gemini 3.0 Pro, Gemini 3.0 Flash
- Claude Opus 4.6 Thinking, Claude Sonnet 4.5 Thinking

## License

Distributed under the MIT License. See `LICENSE` for more information. This project is provided "as is", without warranty of any kind. You are free to use, modify, and distribute it.