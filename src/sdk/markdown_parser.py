"""
Markdown Transpiler Bridge for Reports-Formater.

A zero-dependency, regex-based parser that translates Pandoc-style academic
Markdown into raw dictionary nodes compatible with the Pydantic AST schemas.

This module is a pure pre-processor (Layer 3) with no knowledge of OXML
rendering or MCP transport mechanics.
"""

import re
from typing import Any, Optional


# ============================================================
# Regex Patterns
# ============================================================

# Headings: # Heading
HEADING_PATTERN = re.compile(r'^(#{1,9})\s+(.*)$')

# Images: ![Caption](path){width=10.0 fit_to_page=true}
IMAGE_PATTERN = re.compile(r'^!\[(.*)\]\((.*)\)\{(.*)\}$')

# LaTeX Formulas: $$formula$$ (caption) {align=center}
# Captures the full (caption) including parentheses
FORMULA_PATTERN = re.compile(r'^\$\$(.*)\$\$\s*(\([^)]*\))?\s*(?:\{(.*)\})?\s*$')

# Page breaks: --- or ***
BREAK_PATTERN = re.compile(r'^(---+|\*\*\*+)$')

# List item prefixes
BULLET_PATTERN = re.compile(r'^(\s*)([-*+])\s+(.*)$')
NUMBERED_PATTERN = re.compile(r'^(\s*)(\d+)\.\s+(.*)$')
ALPHA_CYRILLIC_PATTERN = re.compile(r'^(\s*)([а-яА-Я])\)\s+(.*)$')
ALPHA_CYRILLIC_DOT_PATTERN = re.compile(r'^(\s*)([а-яА-Я])\.\s+(.*)$')
ALPHA_LATIN_PATTERN = re.compile(r'^(\s*)([a-zA-Z])\)\s+(.*)$')
ALPHA_LATIN_DOT_PATTERN = re.compile(r'^(\s*)([a-zA-Z])\.\s+(.*)$')

# Table caption patterns
TABLE_CAPTION_PATTERN = re.compile(r'^:\s*(.*)$')
TABLE_CAPTION_ALT_PATTERN = re.compile(r'^[Tt]able:\s*(.*)$')

# Fenced code block start/end
FENCE_START_PATTERN = re.compile(r'^```(\w*)\s*(?:\{(.*)\})?\s*$')
FENCE_END_PATTERN = re.compile(r'^```\s*$')

# Trailing attributes: text {key=value key2="value with spaces"}
TRAILING_ATTRS_PATTERN = re.compile(r'\{([^}]+)\}\s*$')

# Table row pattern (pipe-delimited)
TABLE_ROW_PATTERN = re.compile(r'^\|(.+)\|$')
TABLE_SEPARATOR_PATTERN = re.compile(r'^\|[\s\-:|]+\|$')

# Table caption with attributes pattern
TABLE_CAPTION_WITH_ATTRS_PATTERN = re.compile(
    r'^[Tt]able:\s*(.*?)(?:\s*\{([^}]+)\})?\s*$'
)


# ============================================================
# Attribute Parsing
# ============================================================

def parse_attributes(attr_string: str) -> dict[str, Any]:
    """
    Parse key=value pairs from an attribute string.
    
    Handles:
    - key=value (no quotes)
    - key="value with spaces"
    - key=true/false (converted to bool)
    - key=123.45 (converted to float)
    - key=123 (converted to int)
    
    Args:
        attr_string: String like 'width=10.0 fit_to_page=true caption="Listing 1.1"'
        
    Returns:
        Dictionary of parsed attributes.
    """
    result = {}
    
    # Match key=value pairs (value can be quoted or unquoted)
    # Pattern: key="quoted value" or key=unquoted_value
    pattern = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|[^\s]+)')
    
    for match in pattern.finditer(attr_string):
        key = match.group(1)
        value = match.group(2)
        
        # Remove quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
            # Unescape backslashes and quotes
            value = value.replace('\\"', '"').replace('\\\\', '\\')
        else:
            # Convert types for unquoted values
            value = _convert_value(value)
        
        result[key] = value
    
    return result


def _convert_value(value: str) -> Any:
    """Convert string value to appropriate Python type."""
    # Boolean
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    # Integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Float
    try:
        return float(value)
    except ValueError:
        pass
    
    # String
    return value


# ============================================================
# Core Parsing Functions
# ============================================================

def parse_markdown_to_nodes(md_text: str) -> list[dict]:
    """
    Parse Pandoc-style academic Markdown into a list of raw dictionary nodes.
    
    This function processes the input line-by-line, identifying block-level
    elements (headings, code blocks, images, formulas, tables, lists, paragraphs)
    and converting them to dictionaries compatible with the Pydantic AST schemas.
    
    Args:
        md_text: Markdown text string.
        
    Returns:
        List of dictionaries representing content nodes.
    """
    lines = md_text.split('\n')
    nodes = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            i += 1
            continue
        
        # 1. Page breaks: --- or ***
        if BREAK_PATTERN.match(stripped):
            nodes.append({"type": "break", "style": "page"})
            i += 1
            continue
        
        # 2. Headings
        heading_match = HEADING_PATTERN.match(stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            nodes.append({
                "type": "heading",
                "level": level,
                "text": text
            })
            i += 1
            continue
        
        # 3. Fenced code blocks
        fence_match = FENCE_START_PATTERN.match(stripped)
        if fence_match:
            language = fence_match.group(1) or None
            attrs_str = fence_match.group(2) or ""
            attrs = parse_attributes(attrs_str) if attrs_str else {}
            
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
            
            node = {"type": "code", "code": code_content}
            if language:
                node["language"] = language
            if "caption" in attrs:
                node["caption"] = attrs["caption"]
            if "path" in attrs:
                node["path"] = attrs["path"]
                # If path is provided, code is optional
                if not code_content.strip():
                    del node["code"]
            
            nodes.append(node)
            continue
        
        # 4. Images (Pandoc-style)
        image_match = IMAGE_PATTERN.match(stripped)
        if image_match:
            caption = image_match.group(1).strip()
            path = image_match.group(2).strip()
            attrs_str = image_match.group(3)
            attrs = parse_attributes(attrs_str)
            
            node = {
                "type": "image",
                "path": path,
                "caption": caption if caption else None
            }
            
            # Map attributes to ImageData fields
            if "width" in attrs:
                node["width_cm"] = float(attrs["width"])
            if "height" in attrs:
                node["height_cm"] = float(attrs["height"])
            if "align" in attrs:
                node["align"] = attrs["align"]
            if "fit_to_page" in attrs:
                node["fit_to_page"] = bool(attrs["fit_to_page"])
            if "placeholder" in attrs:
                node["placeholder"] = bool(attrs["placeholder"])
            
            nodes.append(node)
            i += 1
            continue
        
        # 5. LaTeX Formulas
        formula_match = FORMULA_PATTERN.match(stripped)
        if formula_match:
            content = formula_match.group(1).strip()
            caption = formula_match.group(2)  # May be None, includes parentheses
            attrs_str = formula_match.group(3)  # May be None
            
            node = {
                "type": "formula",
                "content": content
            }
            
            if caption:
                node["caption"] = caption.strip()
            
            if attrs_str:
                attrs = parse_attributes(attrs_str)
                if "align" in attrs:
                    node["align"] = attrs["align"]
            
            nodes.append(node)
            i += 1
            continue
        
        # 6. Tables (pipe tables with captions)
        if TABLE_ROW_PATTERN.match(stripped):
            table_result = _parse_table(lines, i)
            if table_result:
                nodes.append(table_result["node"])
                i = table_result["next_index"]
                continue
        
        # 7. Lists
        list_result = _parse_list(lines, i)
        if list_result:
            nodes.extend(list_result["nodes"])
            i = list_result["next_index"]
            continue
        
        # 8. Paragraphs (default: collect consecutive non-empty lines)
        # Check if this is a table caption (Table: ...) - don't treat as paragraph
        if TABLE_CAPTION_WITH_ATTRS_PATTERN.match(stripped):
            # Skip this line, it will be consumed by table parser
            i += 1
            continue
        
        para_result = _parse_paragraph(lines, i)
        if para_result:
            nodes.append(para_result["node"])
            i = para_result["next_index"]
            continue
        
        # Fallback: skip unrecognized line
        i += 1
    
    return nodes


# ============================================================
# Block Parsers
# ============================================================

def _parse_table(lines: list[str], start: int) -> Optional[dict]:
    """
    Parse a pipe table with optional caption.
    
    Looks for caption above (Table: ...) or below (: ...) the table.
    Replaces <br> tags in cells with newlines.
    """
    rows = []
    i = start
    
    # Check for caption above (Table: ...)
    caption = None
    caption_attrs = {}
    
    # Look backwards for caption (within 2 lines)
    if start > 0:
        prev_line = lines[start - 1].strip()
        cap_match = TABLE_CAPTION_WITH_ATTRS_PATTERN.match(prev_line)
        if cap_match:
            caption = cap_match.group(1).strip()
            attrs_str = cap_match.group(2)
            if attrs_str:
                caption_attrs = parse_attributes(attrs_str)
    
    # Parse table rows
    while i < len(lines):
        line = lines[i].strip()
        
        if TABLE_SEPARATOR_PATTERN.match(line):
            # Skip separator line
            i += 1
            continue
        
        row_match = TABLE_ROW_PATTERN.match(line)
        if row_match:
            cells_str = row_match.group(1)
            # Split by | and clean up
            cells = [cell.strip() for cell in cells_str.split('|')]
            # Replace <br> with newline for multi-paragraph cells
            cells = [cell.replace('<br>', '\n').replace('<BR>', '\n') for cell in cells]
            rows.append(cells)
            i += 1
        else:
            break
    
    if not rows:
        return None
    
    # Check for caption below (: ...)
    if caption is None and i < len(lines):
        next_line = lines[i].strip()
        cap_match = TABLE_CAPTION_PATTERN.match(next_line)
        if cap_match:
            caption_text = cap_match.group(1).strip()
            # Check for trailing attributes
            attr_match = TRAILING_ATTRS_PATTERN.search(caption_text)
            if attr_match:
                caption_attrs = parse_attributes(attr_match.group(1))
                caption = caption_text[:attr_match.start()].strip()
            else:
                caption = caption_text
            i += 1
    
    node = {
        "type": "table",
        "rows": rows
    }
    
    if caption:
        node["caption"] = caption
    
    # Apply caption attributes
    if "style" in caption_attrs:
        node["style"] = caption_attrs["style"]
    if "repeat_header" in caption_attrs:
        node["repeat_header"] = bool(caption_attrs["repeat_header"])
    
    return {"node": node, "next_index": i}


def _parse_list(lines: list[str], start: int) -> Optional[dict]:
    """
    Parse consecutive list items and group them by style and level.
    
    Returns a dict with 'nodes' (list of ListData dicts) and 'next_index'.
    """
    items = []
    i = start
    
    # Detect list style from first item
    first_line = lines[start]
    style, level = _detect_list_style(first_line)
    
    if style is None:
        return None
    
    # Collect consecutive items of the same style
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if not stripped:
            # Empty line might end the list or be between items
            # Look ahead to see if list continues
            if i + 1 < len(lines):
                next_style, _ = _detect_list_style(lines[i + 1])
                if next_style == style:
                    i += 1
                    continue
            break
        
        item_style, item_level = _detect_list_style(line)
        
        if item_style != style or item_level != level:
            # Different style/level - stop collecting
            break
        
        # Extract item text
        item_text = _extract_list_item_text(line)
        if item_text is not None:
            items.append(item_text)
            i += 1
        else:
            break
    
    if not items:
        return None
    
    # Map style names to schema-compatible values
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
    """
    Detect list style and indentation level from a line.
    
    Returns (style, level) or (None, 0) if not a list item.
    """
    # Check bullet list
    match = BULLET_PATTERN.match(line)
    if match:
        indent = len(match.group(1))
        level = max(1, (indent // 2) + 1)  # 2-space indentation
        return "bullet", level
    
    # Check numbered list
    match = NUMBERED_PATTERN.match(line)
    if match:
        indent = len(match.group(1))
        level = max(1, (indent // 2) + 1)
        return "numbered", level
    
    # Check Cyrillic alpha (а) or а.)
    match = ALPHA_CYRILLIC_PATTERN.match(line)
    if match:
        indent = len(match.group(1))
        level = max(1, (indent // 2) + 1)
        return "alpha_cyrillic", level
    
    match = ALPHA_CYRILLIC_DOT_PATTERN.match(line)
    if match:
        indent = len(match.group(1))
        level = max(1, (indent // 2) + 1)
        return "alpha_cyrillic", level
    
    # Check Latin alpha (a) or a.)
    match = ALPHA_LATIN_PATTERN.match(line)
    if match:
        indent = len(match.group(1))
        level = max(1, (indent // 2) + 1)
        return "alpha_latin", level
    
    match = ALPHA_LATIN_DOT_PATTERN.match(line)
    if match:
        indent = len(match.group(1))
        level = max(1, (indent // 2) + 1)
        return "alpha_latin", level
    
    return None, 0


def _extract_list_item_text(line: str) -> Optional[str]:
    """Extract the text content from a list item line."""
    # Try each pattern and return the text group
    for pattern in [BULLET_PATTERN, NUMBERED_PATTERN, 
                    ALPHA_CYRILLIC_PATTERN, ALPHA_CYRILLIC_DOT_PATTERN,
                    ALPHA_LATIN_PATTERN, ALPHA_LATIN_DOT_PATTERN]:
        match = pattern.match(line)
        if match:
            # Convert <br> tags to newlines for multi-paragraph support
            text = match.group(3).strip()
            text = text.replace('<br>', '\n').replace('<BR>', '\n')
            return text
    return None


def _parse_paragraph(lines: list[str], start: int) -> Optional[dict]:
    """
    Parse consecutive non-empty lines as a paragraph.
    
    Handles trailing attributes: text {align=center style=normal}
    """
    para_lines = []
    i = start
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Stop at empty line
        if not stripped:
            break
        
        # Stop if this line starts a different block type
        if (HEADING_PATTERN.match(stripped) or 
            FENCE_START_PATTERN.match(stripped) or
            IMAGE_PATTERN.match(stripped) or
            FORMULA_PATTERN.match(stripped) or
            BREAK_PATTERN.match(stripped) or
            TABLE_ROW_PATTERN.match(stripped)):
            break
        
        # Check if it's a list item
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
        # Replace <br> with newline marker
        line = line.replace('<br>', '\n').replace('<BR>', '\n')
        processed_lines.append(line)
    
    # Join with space (but preserve newlines from <br>)
    text = ' '.join(processed_lines)
    
    # Check for trailing attributes
    attrs = {}
    attr_match = TRAILING_ATTRS_PATTERN.search(text)
    if attr_match:
        attrs = parse_attributes(attr_match.group(1))
        text = text[:attr_match.start()].strip()
    
    node = {
        "type": "paragraph",
        "text": text
    }
    
    if "align" in attrs:
        node["align"] = attrs["align"]
    if "style" in attrs:
        node["style"] = attrs["style"]
    
    return {"node": node, "next_index": i}
