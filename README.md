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

Formatting technical documentation and academic reports strictly adhering to local standards (e.g., DSTU 3008-2015) is a highly time-consuming process. Manual formatting in word processors often leads to formatting errors, broken cross-references, and lost time on styling rather than content creation. In adition formating of reports currently is the onliest bottleneck for working with an AI.

**Reports-Formater** is a CLI-based tool designed to fully automate the generation of `.docx` documents from structured YAML content.

### Designed for AI CLI-Agents

This project was built with AI integration in mind. It is optimized to minimize the cognitive load on Language Models. Even less capable models can flawlessly generate the required YAML structure because the visual styling (fonts, alignments, margins) is completely abstracted away into configuration files. 

By using this tool, CLI-Agents (such as Qwen, Gemini, etc.) can generate technical documentation and immediately compile it into a ready-to-print `.docx` file directly in the terminal, completely avoiding manual formatting.

## Features

- **Dual-Protocol Gateway:** Choose between YAML (structured) or Markdown (natural) input formats.
- **MCP Integration:** Native Model Context Protocol servers for seamless AI client integration (Cursor, Claude Desktop).
- **YAML-Driven Content:** Write your paragraphs, headings, lists, tables, code blocks, and formulas in structured YAML.
- **Markdown-First Mode:** Write reports in natural Pandoc-style Markdown with automatic transpilation to internal AST.
- **Strict Compliance:** Automated enforcement of heading styles, paragraph spacing, and page numbering layouts.
- **Complex Structures:** Support for repeating table headers across pages, code block captions, and multi-level alphabetic lists.
- **Formula Rendering:** Advanced mathematical formulas using a two-tier hybrid system (Matplotlib + System LaTeX).
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

The `requirements.txt` includes: `python-docx`, `PyYAML`, `pydantic`, `matplotlib`, `pytest`.
Requires **Python 3.10+**.

### LaTeX Support (Optional but Recommended)

For rendering mathematical formulas, this project uses a two-tier strategy:
1. **Matplotlib (Built-in):** Handles standard mathematical expressions seamlessly in the background.
2. **System LaTeX (Fallback):** Automatically used when Matplotlib encounters complex structures it cannot render natively (e.g., `\begin{cases}`).

If system LaTeX is not installed, complex formulas will be rendered as text placeholders.

**To install LaTeX:**
```bash
# Ubuntu / Debian
sudo apt install texlive-full
```
Ensure that `latex` and `dvipng` are accessible in your `$PATH`.

## Usage

### CLI Execution

Generate a report from a YAML file:
```bash
python -m src.main input.yaml --output report.docx
```

Generate using a specific title page template:
```bash
python -m src.main input.yaml --template title_template.docx --output report.docx
```

Verbose mode for debugging:
```bash
python -m src.main input.yaml --output report.docx -v
```

### AI Integration

To generate documents using an LLM:
1. Provide the LLM with the prompt found in `familiarization/ai_system_prompt.md`.
2. The AI will output a correctly structured YAML file.
3. Pass the generated YAML file to this CLI tool to build the Word document.

Or, if you using CLI-Agent, they can automatically create files and run the tool. But you also need give them instructions to do that `familiarization/ai_system_prompt.md`, `familiarization/user_guide.md`.

### Dual-Protocol Gateway (MCP Integration)

The project provides two Model Context Protocol (MCP) servers for seamless AI client integration:

#### YAML Protocol Server
For structured, schema-driven content generation:
```bash
python -m src.mcp_server_yaml
```
- Exposes tools: `init_report`, `submit_chunk`, `finalize_report`
- Resource: `dstu://guidelines` (YAML schema reference)
- Best for: Precise control over document structure

#### Markdown Protocol Server
For natural, Pandoc-style Markdown input:
```bash
python -m src.mcp_server_markdown
```
- Exposes tools: `init_report`, `submit_markdown_chunk`, `finalize_report`
- Resource: `dstu://guidelines` (Markdown syntax reference)
- Best for: Writing reports in natural Markdown with automatic transpilation

#### Client Configuration

**Cursor:**
1. Open Settings → Features → MCP
2. Click "Add MCP Server"
3. Select "Command" type
4. Name: `reports-formater-yaml` or `reports-formater-markdown`
5. Command: `python -m src.mcp_server_yaml` or `python -m src.mcp_server_markdown`
6. Working directory: your project root

**Claude Desktop:**
Edit `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "reports-formater-yaml": {
      "command": "python",
      "args": ["-m", "src.mcp_server_yaml"],
      "cwd": "/path/to/reports-formater"
    },
    "reports-formater-markdown": {
      "command": "python",
      "args": ["-m", "src.mcp_server_markdown"],
      "cwd": "/path/to/reports-formater"
    }
  }
}
```

Both servers provide real-time validation, stateful session management, and automatic .docx generation through the MCP protocol.

## Try it Yourself (Tutorial)

Want to try generate document? Check out the [`tutorial/`](tutorial/) folder for a simple step-by-step guide. It includes sample programming tasks to feed to your AI and an empty YAML file to practice with.

If you ever need help understanding how this project works, simply copy the following files and ask your AI to explain them to you:
- [`context/ARCHITECTURE.md`](context/ARCHITECTURE.md)
- [`context/introduction.md`](context/introduction.md)
- [`familiarization/user_guide.md`](familiarization/user_guide.md)
- [`familiarization/ai_system_prompt.md`](familiarization/ai_system_prompt.md)

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
| [`familiarization/user_guide.md`](familiarization/user_guide.md) | Syntax guide for YAML nodes and supported features |
| [`familiarization/DSTU_3008-15.md`](familiarization/DSTU_3008-15.md) | Extracts from the DSTU 3008-2015 standard |

## Acknowledgements

Artificial Intelligence played a significant role in the development of this project. AI models were helping to design the architecture, write the documentation, implement tests, and solve complex layout challenges (like the image insertion into a table, for formula alignment or working with headers/footers).

Models used during development:
- Gemini 3.1 Pro, Gemini 3.0 Pro, Gemini 3.0 Flash
- Claude Opus 4.6 Thinking, Claude Sonnet 4.5 Thinking

## License

Distributed under the MIT License. See `LICENSE` for more information. This project is provided "as is", without warranty of any kind. You are free to use, modify, and distribute it.
