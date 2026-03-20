"""
Formatting utilities for Reports-Formater.

Provides inline markdown parsing and text formatting helpers.
"""

import re
import logging
from typing import Optional

from docx.shared import Pt, Cm
from docx.text.paragraph import Paragraph

logger = logging.getLogger(__name__)


# Regex pattern for inline formatting: **bold**, *italic*, `code`
INLINE_PATTERN = re.compile(r'(\*\*.+?\*\*)|(`.+?`)|(\*.+?\*)')


def parse_inline_formatting(
    paragraph: Paragraph,
    text: str,
    default_font: str = "Times New Roman",
    code_font: Optional[str] = None,
    base_size_pt: int = 14,
    code_size_pt: int = 12,
    first_line_indent: Optional[float] = None,
    custom_font: Optional[str] = None,
) -> None:
    """
    Parse simple markdown-like syntax and add formatted runs to paragraph.
    
    Supported syntax:
    - **bold text**
    - *italic text*
    - `inline code`
    
    Args:
        paragraph: Target paragraph object.
        text: Text with inline formatting markers.
        default_font: Global default font if no specific font is set.
        code_font: Optional specific font for code segments.
        base_size_pt: Base font size in points.
        code_size_pt: Font size for inline code.
        first_line_indent: Optional first line indent in cm.
        custom_font: Optional font name for normal text (overrides default_font).
    """
    if first_line_indent is not None:
        paragraph.paragraph_format.first_line_indent = Cm(first_line_indent)
    parts = INLINE_PATTERN.split(text)
    
    for part in parts:
        if not part:
            continue
        
        run = paragraph.add_run()
        run.font.name = custom_font or default_font
        run.font.size = Pt(base_size_pt)
        
        if part.startswith('**') and part.endswith('**'):
            # Bold
            run.text = part[2:-2]
            run.bold = True
        elif part.startswith('`') and part.endswith('`'):
            # Inline code
            run.text = part[1:-1]
            if code_font:
                run.font.name = code_font
            run.font.size = Pt(code_size_pt)
        elif part.startswith('*') and part.endswith('*'):
            # Italic
            run.text = part[1:-1]
            run.italic = True
        else:
            # Plain text
            run.text = part
