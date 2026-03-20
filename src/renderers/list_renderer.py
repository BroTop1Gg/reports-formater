"""
List Renderer for Reports-Formater.

Renders bulleted, numbered, and Cyrillic alpha lists.
"""

import logging
from typing import List

from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src.renderers.base import BaseRenderer, RenderContext
from src.config.schemas import ListData
from src.utils.formatting import parse_inline_formatting
from src.utils.docx_utils import get_alignment_enum

logger = logging.getLogger(__name__)


# Cyrillic letters for alpha-style lists (DSTU requirement)
CYRILLIC_ALPHA = [
    'а', 'б', 'в', 'г', 'д', 'е', 'ж', 'и', 'к', 'л', 
    'м', 'н', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 
    'ш', 'щ', 'ю', 'я'
]

LATIN_ALPHA = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 
    'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 
    'u', 'v', 'w', 'x', 'y', 'z'
]



class ListRenderer(BaseRenderer):
    """
    Renderer for list content nodes.
    
    Handles:
    - Bullet lists (dash prefix)
    - Numbered lists (1. 2. 3.)
    - Cyrillic alpha lists (а) б) в) - style: alpha_cyrillic)
    - Latin alpha lists (a. b. c.) - style: alpha_latin)
    - Nested list levels
    """
    
    @property
    def node_type(self) -> str:
        """Return the node type this renderer handles."""
        return "list"
    
    def render(self, context: RenderContext, data: ListData) -> None:
        """
        Render list content to document.
        
        Args:
            context: Render context with container and config.
            data: Validated ListData model.
        """
        items = data.items
        style_type = data.style
        level = data.level
        
        # Get style config
        styles = context.config.styles
        style_config = styles.list_item
        fonts = context.config.fonts
        
        # Calculate indent
        # base_indent_cm should match normal paragraph indent for DSTU (1.25cm)
        base_indent_cm = styles.normal.first_line_indent_cm
        step_cm = style_config.list_level_step_cm or 1.0
        prefix_width_cm = style_config.list_prefix_width_cm or 0.75
        
        total_indent = base_indent_cm + (level - 1) * step_cm
        
        for i, item_text in enumerate(items):
            # Split item text into lines (Requirement: \n -> Paragraph)
            lines = item_text.split('\n')
            
            for line_idx, line in enumerate(lines):
                # Create paragraph
                p = context.container.add_paragraph()
                
                # Apply indentation and spacing
                pf = p.paragraph_format
                pf.line_spacing = style_config.line_spacing
                # Use reduced space between sub-paragraphs of the same list item
                pf.space_before = Pt(style_config.space_before_pt if line_idx == 0 else 0) # ?
                pf.space_after = Pt(style_config.space_after_pt)
                pf.left_indent = Cm(total_indent)
                
                if line_idx == 0:
                    # ONLY the first line of the item gets the prefix (bullet/number)
                    prefix = self._get_prefix(style_type, i)
                    pf.first_line_indent = Cm(-prefix_width_cm)
                    
                    prefix_run = p.add_run(f"{prefix} ")
                    prefix_run.font.name = style_config.font_name or fonts.default_name
                    prefix_run.font.size = Pt(style_config.font_size_pt)
                else:
                    # Subsequent lines are just indented to match the prefix-aligned text
                    pf.first_line_indent = Pt(style_config.first_line_indent_cm)
                
                p.alignment = get_alignment_enum(style_config.alignment)
                
                # Add item text with inline formatting
                parse_inline_formatting(
                    paragraph=p,
                    text=line,
                    default_font=fonts.default_name,
                    custom_font=style_config.font_name,
                    code_font=styles.inline_code.font_name if styles.inline_code else fonts.code_name,
                    base_size_pt=style_config.font_size_pt,
                )
    
    def _index_to_alpha(self, index: int, alphabet: List[str]) -> str:
        """
        Convert 0-based index to spreadsheet-like alpha string (a, b, ..., z, aa, ab, ...).
        """
        n = len(alphabet)
        res = ""
        while index >= 0:
            res = alphabet[index % n] + res
            index = (index // n) - 1
        return res

    def _get_prefix(self, style_type: str, index: int) -> str:
        """
        Generate list item prefix.
        
        Args:
            style_type: List style (bullet, numbered, alpha).
            index: Item index (0-based).
            
        Returns:
            Prefix string.
        """
        if style_type == 'numbered':
            return f"{index + 1}."
        elif style_type in ['alpha', 'alpha_cyrillic']:
            char_str = self._index_to_alpha(index, CYRILLIC_ALPHA)
            return f"{char_str})"
        elif style_type in ['latin', 'alpha_latin']:
            char_str = self._index_to_alpha(index, LATIN_ALPHA)
            return f"{char_str}."
        else:
            # Default bullet
            return "–"
