"""
Heading Renderer for Reports-Formater.

Renders headings with Word styles and TOC support.
"""

import logging

from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src.renderers.base import BaseRenderer, RenderContext
from src.config.schemas import HeadingData
from src.utils.docx_utils import get_alignment_enum

logger = logging.getLogger(__name__)




class HeadingRenderer(BaseRenderer):
    """
    Renderer for heading content nodes.
    
    Handles:
    - Heading levels 1-9
    - Word built-in heading styles for TOC
    - Custom formatting from config
    """
    
    @property
    def node_type(self) -> str:
        """Return the node type this renderer handles."""
        return "heading"
    
    def render(self, context: RenderContext, data: HeadingData) -> None:
        """
        Render heading content to document.
        
        Args:
            context: Render context with container and config.
            data: Validated HeadingData model.
        """
        level = data.level
        text = data.text
        
        # Add paragraph with text
        h = context.container.add_paragraph(text)
        
        # Try to apply Word built-in heading style for TOC support
        style_name = f"Heading {level}"
        resolved_style = context.style_manager.get_style_name(style_name, fallback="Normal")
        
        try:
            h.style = resolved_style
        except (KeyError, ValueError) as e:
            logger.debug(f"Could not apply style '{resolved_style}': {e}")
        
        # Get style config (heading_1, heading_2, ... or heading_base)
        styles = context.config.styles
        style_key = f"heading_{level}"
        style_config = getattr(styles, style_key, None) or styles.heading_base
        
        # Apply custom formatting to runs
        fonts = context.config.fonts
        for run in h.runs:
            run.font.name = style_config.font_name or fonts.default_name
            run.font.size = Pt(style_config.font_size_pt)
            # Again implict logic?
            # run.font.color.rgb = RGBColor(0, 0, 0) # ???
            run.bold = style_config.bold
        
        # Apply paragraph formatting
        pf = h.paragraph_format
        pf.space_before = Pt(style_config.space_before_pt)
        pf.space_after = Pt(style_config.space_after_pt)
        pf.alignment = get_alignment_enum(style_config.alignment)
        pf.first_line_indent = Cm(style_config.first_line_indent_cm)  # HELL MAGIC NUMBERS AND IMPLICT LOGIC! NEVER DO THAT!
