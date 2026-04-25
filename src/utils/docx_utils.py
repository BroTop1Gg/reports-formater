"""
Docx Utilities for Reports-Formater.

Provides OXML manipulation helpers, particularly for converting inline
shapes to floating anchors.
"""

import logging

from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)


# Anchor positioning constants (OOXML defaults)
DEFAULT_ANCHOR_DIST_LR = 114300
"""Default horizontal distance from surrounding text in EMU (~0.31 cm)."""

DEFAULT_RELATIVE_HEIGHT = 251658240
"""Default z-order index. Matches Word's auto-generated value for images."""


def convert_inline_to_floating(
    inline_shape,
    align_h: str = "center",
    align_v_rel: str = "paragraph",
    wrap_text: bool = True,
    wrap_style: str = "top_bottom",
) -> object | None:
    """Convert an inline shape (``wp:inline``) to a floating anchor (``wp:anchor``).

    Args:
        inline_shape: The ``<wp:inline>`` lxml element from a python‑docx run.
        align_h:      Horizontal alignment — ``'center'``, ``'left'``, or ``'right'``.
        align_v_rel:  Vertical relative reference — ``'paragraph'`` or ``'line'``.
        wrap_text:    If ``True``, applies the chosen ``wrap_style``.
                      If ``False``, forces ``wrapNone``.
        wrap_style:   Wrap mode: ``'top_bottom'``, ``'square'``, or ``'none'``.

    Returns:
        The newly created ``<wp:anchor>`` element, or ``None`` if conversion
        failed (missing core sub‑elements).
    """
    wp_ns = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
    a_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"

    extent = inline_shape.find(f".//{{{wp_ns}}}extent")
    doc_pr = inline_shape.find(f".//{{{wp_ns}}}docPr")
    graphic = inline_shape.find(f".//{{{a_ns}}}graphic")

    if extent is None or doc_pr is None or graphic is None:
        logger.warning(
            "convert_inline_to_floating: Missing required sub-element "
            "(extent=%s, docPr=%s, graphic=%s) — skipping conversion",
            extent is not None, doc_pr is not None, graphic is not None,
        )
        return None

    cx = extent.get("cx")
    cy = extent.get("cy")
    doc_id = doc_pr.get("id")
    doc_name = doc_pr.get("name")

    # Horizontal alignment
    alignment_map = {
        'center': '<wp:align>center</wp:align>',
        'right':  '<wp:align>right</wp:align>',
    }
    pos_h_xml = alignment_map.get(align_h, '<wp:align>left</wp:align>')

    # Vertical offset (0 EMU relative to paragraph)
    pos_v_xml = '<wp:posOffset>0</wp:posOffset>'

    # Wrap type
    if not wrap_text or wrap_style == "none":
        wrap_xml = '<wp:wrapNone/>'
    elif wrap_style == "square":
        wrap_xml = '<wp:wrapSquare wrapText="bothSides"/>'
    else:
        # Standard report style: text breaks above and below the image
        wrap_xml = '<wp:wrapTopAndBottom/>'

    # Anchor XML
    anchor_xml = (
        f'<wp:anchor '
        f'distT="0" distB="0" '
        f'distL="{DEFAULT_ANCHOR_DIST_LR}" distR="{DEFAULT_ANCHOR_DIST_LR}" '
        f'simplePos="0" relativeHeight="{DEFAULT_RELATIVE_HEIGHT}" '
        f'behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1" '
        f'{nsdecls("wp", "a", "pic", "r")}>'
        f'<wp:simplePos x="0" y="0"/>'
        f'<wp:positionH relativeFrom="column">'
        f'{pos_h_xml}'
        f'</wp:positionH>'
        f'<wp:positionV relativeFrom="{align_v_rel}">'
        f'{pos_v_xml}'
        f'</wp:positionV>'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:effectExtent b="0" l="0" r="0" t="0"/>'
        f'{wrap_xml}'
        f'<wp:docPr id="{doc_id}" name="{doc_name}"/>'
        f'<wp:cNvGraphicFramePr>'
        f'<a:graphicFrameLocks noChangeAspect="1"/>'
        f'</wp:cNvGraphicFramePr>'
        f'{graphic.xml}'
        f'</wp:anchor>'
    )

    anchor_element = parse_xml(anchor_xml)

    parent = inline_shape.getparent()
    if parent is not None:
        parent.replace(inline_shape, anchor_element)

    return anchor_element

def remove_table_borders(table) -> None:
    """Manipulate OXML to remove all borders from a table."""
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    
    # Define XML for 'nil' borders
    borders_xml = (
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="nil"/>'
        f'<w:left w:val="nil"/>'
        f'<w:bottom w:val="nil"/>'
        f'<w:right w:val="nil"/>'
        f'<w:insideH w:val="nil"/>'
        f'<w:insideV w:val="nil"/>'
        f'</w:tblBorders>'
    )
    
    # Remove existing borders node if present
    existing_borders = tbl_pr.find(f".//{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}tblBorders")
    if existing_borders is not None:
        tbl_pr.remove(existing_borders)
            
    # Append the new no-border definition
    tbl_pr.append(parse_xml(borders_xml))

def add_table_borders(table) -> None:
    """Manipulate OXML to explicitly add all standard grid borders to a table."""
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    
    # Define XML for 'single' standard borders
    borders_xml = (
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'<w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        f'</w:tblBorders>'
    )
    
    # Remove existing borders node if present
    existing_borders = tbl_pr.find(f".//{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}tblBorders")
    if existing_borders is not None:
        tbl_pr.remove(existing_borders)
            
    # Append the new borders definition in correct order
    tbl_pr.insert_element_before(parse_xml(borders_xml),
        'w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook', 'w:tblCaption')


def optimize_invisible_table(table) -> None:
    """
    Optimizes a table to act as an invisible layout container.
    
    Uses the exact XML pattern that LibreOffice expects:
    - Removes w:tblBorders from w:tblPr (instead uses empty w:tcBorders on cells)
    - Sets width to 100% (pct)
    - Sets table-level cell margins to 0 (w:tblCellMar)
    - No cell-level w:tcMar (LibreOffice ignores redundant overrides)
    - Centers table, removes indent
    """
    W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    tbl = table._tbl
    tblPr = tbl.tblPr

    # Table-Level Properties
    
    # Remove table-level borders entirely (LibreOffice doesn't like nil borders here)
    existing_borders = tblPr.find(f".//{{{W_NS}}}tblBorders")
    if existing_borders is not None:
        tblPr.remove(existing_borders)

    # Width 100%
    tblW = tblPr.find(f".//{{{W_NS}}}tblW")
    if tblW is not None:
        tblPr.remove(tblW)
    tblPr.insert_element_before(
        parse_xml(f'<w:tblW {nsdecls("w")} w:w="5000" w:type="pct"/>'),
        'w:jc', 'w:tblCellSpacing', 'w:tblInd', 'w:tblBorders', 'w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook', 'w:tblCaption'
    )

    # Center alignment
    old_jc = tblPr.find(f".//{{{W_NS}}}jc")
    if old_jc is not None: tblPr.remove(old_jc)
    tblPr.insert_element_before(
        parse_xml(f'<w:jc {nsdecls("w")} w:val="center"/>'),
        'w:tblCellSpacing', 'w:tblInd', 'w:tblBorders', 'w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook', 'w:tblCaption'
    )

    # Indent 0
    old_ind = tblPr.find(f".//{{{W_NS}}}tblInd")
    if old_ind is not None: tblPr.remove(old_ind)
    tblPr.insert_element_before(
        parse_xml(f'<w:tblInd {nsdecls("w")} w:w="0" w:type="dxa"/>'),
        'w:tblBorders', 'w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook', 'w:tblCaption'
    )

    # Cell Margins 0 at Table level (the ONLY place LibreOffice respects this)
    old_mar = tblPr.find(f".//{{{W_NS}}}tblCellMar")
    if old_mar is not None: tblPr.remove(old_mar)
    tblCellMar = parse_xml(
        f'<w:tblCellMar {nsdecls("w")}>'
        f'<w:top w:w="0" w:type="dxa"/>'
        f'<w:left w:w="0" w:type="dxa"/>'
        f'<w:bottom w:w="0" w:type="dxa"/>'
        f'<w:right w:w="0" w:type="dxa"/>'
        f'</w:tblCellMar>'
    )
    tblPr.insert_element_before(tblCellMar, 'w:tblLook', 'w:tblCaption')

    # --- Cell-Level Properties ---
    # Set empty tcBorders on each cell (LibreOffice pattern for borderless cells)
    # Do NOT set tcMar here — LibreOffice respects only the table-level tblCellMar
    for row in table.rows:
        for cell in row.cells:
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            
            # Remove any existing cell-level margins (redundancy confuses LibreOffice)
            tcMar = tcPr.find(f".//{{{W_NS}}}tcMar")
            if tcMar is not None: tcPr.remove(tcMar)
            
            # Replace any cell borders with empty tcBorders element
            tcBorders = tcPr.find(f".//{{{W_NS}}}tcBorders")
            if tcBorders is not None: tcPr.remove(tcBorders)
            tcPr.append(parse_xml(f'<w:tcBorders {nsdecls("w")}/>'))


def optimize_table_width_and_alignment(table) -> None:
    """
    Optimizes a typical visible table to correctly align with page margins.
    - Sets width to 100% (so it uses full page width)
    - Removes default left/right table indents
    - Sets center alignment
    """
    tblPr = table._tbl.tblPr
    
    # Width 100%
    tblW = tblPr.find(f".//{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}tblW")
    if tblW is not None:
        tblPr.remove(tblW)
    tblPr.insert_element_before(
        parse_xml(f'<w:tblW {nsdecls("w")} w:w="5000" w:type="pct"/>'),
        'w:jc', 'w:tblCellSpacing', 'w:tblInd', 'w:tblBorders', 'w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook', 'w:tblCaption'
    )

    # Center alignment
    old_jc = tblPr.find(f".//{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}jc")
    if old_jc is not None: tblPr.remove(old_jc)
    jc = parse_xml(f'<w:jc {nsdecls("w")} w:val="center"/>')
    tblPr.insert_element_before(
        jc,
        'w:tblCellSpacing', 'w:tblInd', 'w:tblBorders', 'w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook', 'w:tblCaption'
    )

    # Indent 0 (to align with left margin)
    old_ind = tblPr.find(f".//{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}tblInd")
    if old_ind is not None: tblPr.remove(old_ind)
    tblInd = parse_xml(f'<w:tblInd {nsdecls("w")} w:w="0" w:type="dxa"/>')
    tblPr.insert_element_before(
        tblInd,
        'w:tblBorders', 'w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook', 'w:tblCaption'
    )


def get_alignment_enum(alignment_str: str) -> WD_ALIGN_PARAGRAPH:
    """
    Convert string alignment name to docx enum.
    
    Args:
        alignment_str: Alignment name ('left', 'center', 'right', 'justify').
        
    Returns:
        Corresponding WD_ALIGN_PARAGRAPH enum value. Defaults to LEFT.
    """
    align_map = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY
    }
    return align_map.get(alignment_str.lower(), WD_ALIGN_PARAGRAPH.LEFT)
