"""
Image Renderer for Reports-Formater.

Renders images with optional captions and alignment.
"""

import io
import hashlib
import logging
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from docx.shared import Cm, Mm, Emu, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_ALIGN_VERTICAL

from src.renderers.base import BaseRenderer, RenderContext
from src.config.schemas import ImageData
from src.utils.formatting import parse_inline_formatting
from src.utils.docx_utils import optimize_invisible_table

logger = logging.getLogger(__name__)

ALIGNMENT_MAP = {
    'justify': WD_ALIGN_PARAGRAPH.JUSTIFY,
    'center': WD_ALIGN_PARAGRAPH.CENTER,
    'left': WD_ALIGN_PARAGRAPH.LEFT,
    'right': WD_ALIGN_PARAGRAPH.RIGHT,
}


class ImageRenderer(BaseRenderer):
    """
    Renderer for image content nodes.
    
    Handles:
    - Image insertion with width/height control
    - Image alignment
    - Optional captions below image
    """
    
    @property
    def node_type(self) -> str:
        """Return the node type this renderer handles."""
        return "image"
    
    def render(self, context: RenderContext, data: ImageData) -> None:
        """
        Render image content to document.
        """
        # Determine Max Width dynamically
        # Calculate available width based on page setup
        page_setup = context.config.page_setup
        # Word default A4 is 21.0 cm width
        # available_width = total_width - (left_margin + right_margin)
        total_page_width_cm = 21.0 
        available_width_cm = total_page_width_cm - (page_setup.margin_left_cm + page_setup.margin_right_cm)
        
        item_width = Cm(available_width_cm)
        
        try:
            # Try to get actual width from first section if available
            section = context.doc.sections[0]
            actual_avail_width = section.page_width - section.left_margin - section.right_margin
            if actual_avail_width > 0:
                item_width = actual_avail_width
        except Exception:
            logger.debug(f"ImageRenderer: Using calculated fallback width {available_width_cm}cm")
            
        # Determine image source
        image_to_insert = None
        missing = False
        
        if getattr(data, 'placeholder', False):
            image_to_insert = self._generate_placeholder_image("IMAGE PLACEHOLDER", '#fff2cc', '#d6b656')
        else:
            image_path = self._resolve_path(data.path, context.resource_path)
            if not image_path.exists():
                logger.error(f"ImageRenderer: Image not found: {image_path}")
                image_to_insert = self._generate_placeholder_image(f"MISSING IMAGE:\n{data.path}", '#ffebe6', 'red')
                missing = True
            else:
                image_to_insert = str(image_path)
                
        # Persist generated placeholder to temp file if necessary
        if isinstance(image_to_insert, io.BytesIO):
            temp_dir = context.resource_path / ".temp_images"
            temp_dir.mkdir(exist_ok=True)
            name_hash = hashlib.md5(str(data.path).encode()).hexdigest()
            temp_file = temp_dir / f"placeholder_{name_hash}.png"
            temp_file.write_bytes(image_to_insert.getvalue())
            image_to_insert = str(temp_file.resolve())

        # Create Layout Table
        rows = 2 if data.caption else 1
        table = context.container.add_table(rows=rows, cols=1)
        table.autofit = False
        table.columns[0].width = item_width
        optimize_invisible_table(table)
        
        # Populate Image Cell (Row 0)
        cell_img = table.cell(0, 0)
        p_img = cell_img.paragraphs[0]
        # remove spacing for clean table fit
        p_img.paragraph_format.left_indent = Pt(0)
        p_img.paragraph_format.right_indent = Pt(0)
        p_img.paragraph_format.space_before = Pt(0)
        p_img.paragraph_format.space_after = Pt(0)
        p_img.paragraph_format.first_line_indent = Pt(0)
        
        p_img.alignment = ALIGNMENT_MAP.get(data.align, WD_ALIGN_PARAGRAPH.CENTER)
        p_img.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        
        run_img = p_img.add_run()
        
        try:
            if data.width_cm:
                shape = run_img.add_picture(image_to_insert, width=Cm(data.width_cm))
            elif data.height_cm:
                shape = run_img.add_picture(image_to_insert, height=Cm(data.height_cm))
            else:
                shape = run_img.add_picture(image_to_insert, width=item_width)
                
            # IMPORTANT: LibreOffice Custom Image Margin Fix
            # By default, python-docx does not insert `distT`, `distB`, `distL`, `distR` 
            # attributes on the `<wp:inline>` XML element for images.
            # MS Word handles this gracefully, but LibreOffice Writer assumes a default 
            # internal padding (~0.31 cm) around the image if these attributes are missing.
            # This causes images to be cropped/clipped when placed inside tables that 
            # restrict their width.
            #
            # To fix this, we MUST explicitly set these distances to "0" on the 
            # underlying OXML element `shape._inline`.
            inline = shape._inline
            inline.set('distT', "0")
            inline.set('distB', "0")
            inline.set('distL', "0")
            inline.set('distR', "0")
        except Exception as e:
            logger.error(f"ImageRenderer: Failed to insert image: {e}")
            return
            
        # Add caption if provided (Row 1)
        if data.caption:
            cell_caption = table.cell(1, 0)
            p_caption = cell_caption.paragraphs[0]
            p_caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            p_caption.paragraph_format.left_indent = Pt(0)
            p_caption.paragraph_format.right_indent = Pt(0)
            p_caption.paragraph_format.space_before = Pt(0)
            p_caption.paragraph_format.space_after = Pt(0)
            p_caption.paragraph_format.first_line_indent = Pt(0)
            
            parse_inline_formatting(
                paragraph=p_caption,
                text=data.caption,
                default_font=context.config.fonts.default_name,
                code_font=context.config.fonts.code_name,
                first_line_indent=0.0
            )

    @staticmethod
    def _generate_placeholder_image(text: str, bg_color: str, edge_color: str) -> io.BytesIO:
        """Generate a placeholder image for missing or explicitly placeholder images."""
        fig = plt.figure(figsize=(6, 2), dpi=100)
        fig.text(
            0.5, 0.5, text, 
            fontsize=12, color=edge_color, family='monospace',
            ha='center', va='center',
            bbox=dict(facecolor=bg_color, edgecolor=edge_color, boxstyle='square,pad=1.0', linewidth=2)
        )
        plt.axis('off')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        plt.close(fig)
        buf.seek(0)
        return buf

    def _resolve_path(self, path_str: str, resource_path: Path) -> Path:
        """Resolve image path."""
        path = Path(path_str)
        if path.is_absolute():
            return path
        return resource_path / path
