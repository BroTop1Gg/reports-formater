"""
Paragraph Renderer for Reports-Formater.

Renders standard text paragraphs with inline formatting support.
"""

import logging
from typing import Optional

from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src.renderers.base import BaseRenderer, RenderContext
from src.config.schemas import ParagraphData
from src.utils.formatting import parse_inline_formatting
from src.utils.docx_utils import get_alignment_enum

logger = logging.getLogger(__name__)



class ParagraphRenderer(BaseRenderer):
    """
    Renderer for paragraph content nodes.
    
    Handles:
    - Text with inline formatting (**bold**, *italic*, `code`)
    - Paragraph alignment overrides
    - Style-based formatting from config
    """
    
    @property
    def node_type(self) -> str:
        """Return the node type this renderer handles."""
        return "paragraph"
    
    def render(self, context: RenderContext, data: ParagraphData) -> None:
        """
        Render paragraph content to document.
        
        Args:
            context: Render context with container and config.
            data: Validated ParagraphData model.
        """
        # Get style configuration
        styles = context.config.styles
        style_config = getattr(styles, data.style, styles.normal)
        fonts = context.config.fonts
        
        # Split text into lines to support multi-paragraph nodes (Requirement: \n -> Paragraph)
        # We strip trailing whitespace for each line to avoid empty runs, but 
        # keep empty lines if intended (e.g. \n\n).
        text_lines = data.text.split('\n')
        
        for line in text_lines:
            # Create paragraph in current container
            p = context.container.add_paragraph()
            
            # Apply paragraph formatting
            self._apply_formatting(p, style_config, data.align)
            
            # Parse and add formatted text
            parse_inline_formatting(
                paragraph=p,
                text=line,
                default_font=fonts.default_name,
                custom_font=style_config.font_name,
                code_font=styles.inline_code.font_name if styles.inline_code else fonts.code_name,
                base_size_pt=style_config.font_size_pt,
                code_size_pt=styles.inline_code.font_size_pt if styles.inline_code else 12,
            )
    
    def _apply_formatting(
        self, 
        paragraph, 
        style_config, 
        align_override: Optional[str],
    ) -> None:
        """
        Apply paragraph formatting from style config.
        
        Args:
            paragraph: Paragraph object to format.
            style_config: StyleConfig with formatting values.
            align_override: Optional alignment override from node data.
        """
        pf = paragraph.paragraph_format
        
        # Line spacing
        pf.line_spacing = style_config.line_spacing
        
        # Spacing before/after
        pf.space_before = Pt(style_config.space_before_pt)
        pf.space_after = Pt(style_config.space_after_pt)
        
        # Indents
        if style_config.first_line_indent_cm is not None:
            pf.first_line_indent = Cm(style_config.first_line_indent_cm)
        
        if style_config.left_indent_cm is not None:
            pf.left_indent = Cm(style_config.left_indent_cm)
        
        if style_config.hanging_indent_cm is not None:
            pf.first_line_indent = Cm(-style_config.hanging_indent_cm)
        
        # Alignment
        align_str = align_override or style_config.alignment
        paragraph.alignment = get_alignment_enum(align_str)
        
        # Centered text should not have first-line indent
        if align_str == 'center':
            pf.first_line_indent = Cm(0)
