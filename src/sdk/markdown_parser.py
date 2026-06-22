"""
Markdown Transpiler Bridge for Reports-Formater.

A zero-dependency, regex-based parser that translates natural academic
Markdown into raw dictionary nodes compatible with the Pydantic AST schemas.

This module is a pure pre-processor (Layer 3) with no knowledge of OXML
rendering or MCP transport mechanics.

Design Principles:
- Smart Defaults: paragraphs → justify, formulas → center,
  images → center+fit_to_page, tables → Table Grid+repeat_header.
- Smart Caption Absorption: italic caption paragraphs preceding code blocks
  or tables are automatically consumed as captions.
- Natural Syntax: no curly-brace attributes. LLMs write clean Markdown.
"""

import re
from typing import Optional


# ============================================================
# Regex Patterns
# ============================================================

# Headings: # Heading
HEADING_PATTERN = re.compile(r'^(#{1,9})\s+(.*)$')

# Images: ![Caption](path) — natural syntax, no attributes
IMAGE_PATTERN = re.compile(r'^!\[(.*)\]\((.*)\)$')

# LaTeX Formulas: $$formula$$ (caption)
FORMULA_PATTERN = re.compile(r'^\$\$(.*)\$\$\s*(?:\(([^)]+)\))?\s*$')

# Page breaks: --- or ***
BREAK_PATTERN = re.compile(r'^(---+|\*\*\*+)$')

# Line breaks: <br> or <br count=N>
LINE_BREAK_PATTERN = re.compile(r'^<br(?:\s+count=(\d+))?\s*/?\s*>$', re.IGNORECASE)

# List item prefixes
BULLET_PATTERN = re.compile(r'^(\s*)([-*+])\s+(.*)$')
NUMBERED_PATTERN = re.compile(r'^(\s*)(\d+)\.\s+(.*)$')
ALPHA_CYRILLIC_PATTERN = re.compile(r'^(\s*)([а-яА-Я])\)\s+(.*)$')
ALPHA_CYRILLIC_DOT_PATTERN = re.compile(r'^(\s*)([а-яА-Я])\.\s+(.*)$')
ALPHA_LATIN_PATTERN = re.compile(r'^(\s*)([a-zA-Z])\)\s+(.*)$')
ALPHA_LATIN_DOT_PATTERN = re.compile(r'^(\s*)([a-zA-Z])\.\s+(.*)$')

# Fenced code block start/end
FENCE_START_PATTERN = re.compile(r'^```(\w*)\s*$')
FENCE_END_PATTERN = re.compile(r'^```\s*$')

# Table row pattern (pipe-delimited)
TABLE_ROW_PATTERN = re.compile(r'^\|(.+)\|$')
TABLE_SEPARATOR_PATTERN = re.compile(r'^\|[\s\-:|]+\|$')

# Smart Caption Absorption patterns
# Code listing caption: Лістинг 5.1 — Name or Лістинг 5.1 — Name (path)
# Group 1: Listing number (e.g., "5.1" or "А.1")
# Group 2: Caption text only (without path)
# Group 3: Optional path in parentheses (must contain file extension)
CODE_CAPTION_PATTERN = re.compile(
    r'^Лістинг\s+([a-zA-Zа-яА-ЯёЁҐєЄіІїЇ0-9._-]+)\s*—\s*(.+?)(?:\s*\(([^)]*\.[a-zA-Z0-9]+)\))?\s*$'
)

# Table caption: Таблиця 1.1 — Name
# Group 1: Table number (e.g., "1.1" or "А.1")
# Group 2: Caption text
TABLE_CAPTION_WITH_ATTRS_PATTERN = re.compile(
    r'^Таблиця\s+([a-zA-Zа-яА-ЯёЁҐєЄіІїЇ0-9._-]+)\s*—\s*(.+?)\s*$'
)

# Appendix marker: # Додаток А. Назва or # Додаток А - Назва or # Додаток А
# Group 1: Letter label (Cyrillic or Latin uppercase)
# Group 2: Optional title text
APPENDIX_PATTERN = re.compile(
    r'^#\s*Додаток\s+([А-ЯІЇЄҐA-Z])(?:(?:\.\s*|\s*-\s*|\s+)(.*))?$',
    re.IGNORECASE
)


# ============================================================
# Core Parsing Functions
# ============================================================

def parse_markdown_to_nodes(md_text: str) -> list[dict]:
    """
    Parse natural academic Markdown into a list of raw dictionary nodes.

    Uses a state machine with pending_caption for Smart Caption Absorption.
    All elements receive Smart Defaults automatically.

    Args:
        md_text: Markdown text string.

    Returns:
        List of dictionaries representing content nodes.
    """
    lines = md_text.split('\n')
    nodes = []
    i = 0
    pending_caption: Optional[str] = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # 1. Page breaks: --- or ***
        if BREAK_PATTERN.match(stripped):
            # Flush pending caption as paragraph if not consumed
            if pending_caption is not None:
                nodes.append(_make_paragraph(pending_caption))
                pending_caption = None
            nodes.append({"type": "break", "style": "page"})
            i += 1
            continue

        # 2. Line breaks: <br> or <br count=N>
        lb_match = LINE_BREAK_PATTERN.match(stripped)
        if lb_match:
            if pending_caption is not None:
                nodes.append(_make_paragraph(pending_caption))
                pending_caption = None
            count = int(lb_match.group(1)) if lb_match.group(1) else 1
            nodes.append({"type": "break", "style": "line", "count": count})
            i += 1
            continue

        # 3. Appendix markers: # Додаток А. Назва (must check before headings)
        appendix_match = APPENDIX_PATTERN.match(stripped)
        if appendix_match:
            if pending_caption is not None:
                nodes.append(_make_paragraph(pending_caption))
                pending_caption = None
            label = appendix_match.group(1).upper()
            title = appendix_match.group(2)
            title = title.strip() if title else None
            nodes.append({
                "type": "appendix_marker",
                "label": label,
                "title": title
            })
            i += 1
            continue

        # 4. Headings
        heading_match = HEADING_PATTERN.match(stripped)
        if heading_match:
            # Flush pending caption — heading is not a code/table
            if pending_caption is not None:
                nodes.append(_make_paragraph(pending_caption))
                pending_caption = None
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            nodes.append({
                "type": "heading",
                "level": level,
                "text": text
            })
            i += 1
            continue

        # 4. Smart Caption Absorption: check for caption lines
        listing_cap = CODE_CAPTION_PATTERN.match(stripped)
        if listing_cap:
            # Store as pending — will be consumed by next code block
            pending_caption = stripped  # Store the full caption line for later extraction
            i += 1
            continue

        table_cap = TABLE_CAPTION_WITH_ATTRS_PATTERN.match(stripped)
        if table_cap:
            pending_caption = stripped
            i += 1
            continue

        # 5. Fenced code blocks
        fence_match = FENCE_START_PATTERN.match(stripped)
        if fence_match:
            language = fence_match.group(1) or None

            # Collect code content until closing fence
            code_lines = []
            i += 1
            while i < len(lines):
                if FENCE_END_PATTERN.match(lines[i].strip()):
                    i += 1
                    break
                code_lines.append(lines[i])
                i += 1

            code_content = '\n'.join(code_lines)

            node: dict = {"type": "code", "code": code_content}
            if language:
                node["language"] = language

            # Smart Caption Absorption: consume pending caption
            if pending_caption is not None:
                cap_match = CODE_CAPTION_PATTERN.match(pending_caption)
                if cap_match:
                    number = cap_match.group(1)
                    text = cap_match.group(2).strip()
                    node["caption"] = f"Лістинг {number} — {text}"
                    path = cap_match.group(3)
                    if path:
                        node["path"] = path.strip()
                        # If path provided and code is empty, remove code key
                        if not code_content.strip():
                            del node["code"]
                else:
                    # Not a listing caption — flush as paragraph
                    nodes.append(_make_paragraph(pending_caption))
                pending_caption = None

            nodes.append(node)
            continue

        # 6. Images (natural syntax)
        image_match = IMAGE_PATTERN.match(stripped)
        if image_match:
            # Flush pending caption
            if pending_caption is not None:
                nodes.append(_make_paragraph(pending_caption))
                pending_caption = None

            caption = image_match.group(1).strip()
            path = image_match.group(2).strip()

            node = {
                "type": "image",
                "path": path,
                "caption": caption if caption else None,
                # Smart Defaults
                "align": "center",
                "fit_to_page": True,
            }

            # Natural placeholder detection
            if path.lower() == "placeholder":
                node["path"] = "images/placeholder.png"
                node["placeholder"] = True

            nodes.append(node)
            i += 1
            continue

        # 7. LaTeX Formulas
        formula_match = FORMULA_PATTERN.match(stripped)
        if formula_match:
            # Flush pending caption
            if pending_caption is not None:
                nodes.append(_make_paragraph(pending_caption))
                pending_caption = None

            content = formula_match.group(1).strip()
            caption_text = formula_match.group(2)  # May be None

            node = {
                "type": "formula",
                "content": content,
                # Smart Default
                "align": "center",
            }

            if caption_text:
                node["caption"] = f"({caption_text.strip()})"

            nodes.append(node)
            i += 1
            continue

        # 8. Tables (pipe tables with Smart Caption Absorption)
        if TABLE_ROW_PATTERN.match(stripped):
            table_result = _parse_table(lines, i, pending_caption)
            if table_result:
                nodes.append(table_result["node"])
                i = table_result["next_index"]
                pending_caption = table_result.get("consumed_caption")
                # If caption was consumed, pending_caption is now None
                # If not consumed, it stays for next iteration
                continue

        # 9. Lists
        list_result = _parse_list(lines, i)
        if list_result:
            # Flush pending caption
            if pending_caption is not None:
                nodes.append(_make_paragraph(pending_caption))
                pending_caption = None
            nodes.extend(list_result["nodes"])
            i = list_result["next_index"]
            continue

        # 10. Paragraphs (Smart Default: justify)
        # First, flush any pending caption that wasn't consumed
        if pending_caption is not None:
            nodes.append(_make_paragraph(pending_caption))
            pending_caption = None
        
        para_result = _parse_paragraph(lines, i)
        if para_result:
            # Check if this paragraph is itself a caption pattern
            # (shouldn't happen since we check above, but safety net)
            nodes.append(para_result["node"])
            i = para_result["next_index"]
            continue

        # Fallback: skip unrecognized line
        i += 1

    # Flush any remaining pending caption
    if pending_caption is not None:
        nodes.append(_make_paragraph(pending_caption))

    return nodes


def _make_paragraph(text: str) -> dict:
    """Create a paragraph node with Smart Defaults."""
    # Strip italic markers if present (from flushed captions)
    clean = text.strip()
    if clean.startswith('*') and clean.endswith('*'):
        clean = clean[1:-1].strip()
    return {
        "type": "paragraph",
        "text": clean,
        "align": "justify",
    }


# ============================================================
# Block Parsers
# ============================================================

def _parse_table(
    lines: list[str], start: int, pending_caption: Optional[str]
) -> Optional[dict]:
    """
    Parse a pipe table with Smart Caption Absorption.

    If pending_caption matches TABLE_CAPTION_ABSORB_PATTERN, consume it
    as the table caption. Otherwise, flush it as a paragraph first.
    """
    rows = []
    i = start
    caption = None
    consumed = False

    # Smart Caption Absorption from pending state
    if pending_caption is not None:
        cap_match = TABLE_CAPTION_WITH_ATTRS_PATTERN.match(pending_caption)
        if cap_match:
            number = cap_match.group(1)
            text = cap_match.group(2).strip()
            caption = f"Таблиця {number} — {text}"
            consumed = True

    # Parse table rows
    while i < len(lines):
        line = lines[i].strip()

        if TABLE_SEPARATOR_PATTERN.match(line):
            i += 1
            continue

        row_match = TABLE_ROW_PATTERN.match(line)
        if row_match:
            cells_str = row_match.group(1)
            cells = [cell.strip() for cell in cells_str.split('|')]
            # Replace <br> with newline for multi-paragraph cells
            cells = [cell.replace('<br>', '\n').replace('<BR>', '\n') for cell in cells]
            rows.append(cells)
            i += 1
        else:
            break

    if not rows:
        return None

    node: dict = {
        "type": "table",
        "rows": rows,
        # Smart Defaults
        "style": "Table Grid",
        "repeat_header": True,
    }

    if caption:
        node["caption"] = caption

    result: dict = {"node": node, "next_index": i}
    if consumed:
        result["consumed_caption"] = None  # Signal that caption was consumed
    else:
        result["consumed_caption"] = pending_caption  # Pass through unchanged

    return result


def _parse_list(lines: list[str], start: int) -> Optional[dict]:
    """
    Parse consecutive list items and group them by style and level.

    Returns a dict with 'nodes' (list of ListData dicts) and 'next_index'.
    """
    items = []
    i = start

    first_line = lines[start]
    style, level = _detect_list_style(first_line)

    if style is None:
        return None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            if i + 1 < len(lines):
                next_style, _ = _detect_list_style(lines[i + 1])
                if next_style == style:
                    i += 1
                    continue
            break

        item_style, item_level = _detect_list_style(line)

        if item_style != style or item_level != level:
            break

        item_text = _extract_list_item_text(line)
        if item_text is not None:
            items.append(item_text)
            i += 1
        else:
            break

    if not items:
        return None

    style_map = {
        "bullet": "bullet",
        "numbered": "numbered",
        "alpha_cyrillic": "alpha_cyrillic",
        "alpha_latin": "alpha_latin"
    }

    node = {
        "type": "list",
        "style": style_map.get(style, "bullet"),
        "level": level,
        "items": items
    }

    return {"nodes": [node], "next_index": i}


def _detect_list_style(line: str) -> tuple[Optional[str], int]:
    """Detect list style and indentation level from a line."""
    for pattern, style in [
        (BULLET_PATTERN, "bullet"),
        (NUMBERED_PATTERN, "numbered"),
        (ALPHA_CYRILLIC_PATTERN, "alpha_cyrillic"),
        (ALPHA_CYRILLIC_DOT_PATTERN, "alpha_cyrillic"),
        (ALPHA_LATIN_PATTERN, "alpha_latin"),
        (ALPHA_LATIN_DOT_PATTERN, "alpha_latin"),
    ]:
        match = pattern.match(line)
        if match:
            indent = len(match.group(1))
            level = max(1, (indent // 2) + 1)
            return style, level

    return None, 0


def _extract_list_item_text(line: str) -> Optional[str]:
    """Extract the text content from a list item line."""
    for pattern in [BULLET_PATTERN, NUMBERED_PATTERN,
                    ALPHA_CYRILLIC_PATTERN, ALPHA_CYRILLIC_DOT_PATTERN,
                    ALPHA_LATIN_PATTERN, ALPHA_LATIN_DOT_PATTERN]:
        match = pattern.match(line)
        if match:
            text = match.group(3).strip()
            text = text.replace('<br>', '\n').replace('<BR>', '\n')
            return text
    return None


def _parse_paragraph(lines: list[str], start: int) -> Optional[dict]:
    """
    Parse consecutive non-empty lines as a paragraph.

    Smart Default: align=justify.
    Supports <br> tags for embedded line breaks.
    """
    para_lines = []
    i = start

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            break

        # Stop if this line starts a different block type
        if (HEADING_PATTERN.match(stripped) or
            FENCE_START_PATTERN.match(stripped) or
            IMAGE_PATTERN.match(stripped) or
            FORMULA_PATTERN.match(stripped) or
            BREAK_PATTERN.match(stripped) or
            LINE_BREAK_PATTERN.match(stripped) or
            TABLE_ROW_PATTERN.match(stripped) or
            CODE_CAPTION_PATTERN.match(stripped) or
            TABLE_CAPTION_WITH_ATTRS_PATTERN.match(stripped)):
            break

        style, _ = _detect_list_style(line)
        if style is not None:
            break

        para_lines.append(stripped)
        i += 1

    if not para_lines:
        return None

    # Join lines, converting <br> tags to newlines
    processed_lines = []
    for line in para_lines:
        line = line.replace('<br>', '\n').replace('<BR>', '\n')
        processed_lines.append(line)

    text = ' '.join(processed_lines)

    return {
        "node": {
            "type": "paragraph",
            "text": text,
            "align": "justify",
        },
        "next_index": i
    }
