"""
Content node schemas for Reports-Formater.

Defines Pydantic models for YAML content nodes (paragraph, heading, list, etc.).
These models validate input data before rendering.
"""

from typing import List, Union, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================
# Base Content Node
# ============================================================

class ContentNode(BaseModel):
    """Base class for all content nodes."""
    
    type: str = Field(..., description="Node type identifier")


# ============================================================
# Text Content Nodes
# ============================================================

class ParagraphData(ContentNode):
    """Standard paragraph content."""
    
    type: Literal["paragraph"] = "paragraph"
    text: str = Field(..., description="Paragraph text (supports inline markdown)")
    align: Optional[str] = Field(default=None, description="Override alignment")
    style: str = Field(default="normal", description="Style key from config")


class HeadingData(ContentNode):
    """Heading content with TOC support."""
    
    type: Literal["heading"] = "heading"
    text: str = Field(..., description="Heading text")
    level: int = Field(default=1, ge=1, le=9, description="Heading level (1-9)")


class CodeBlockData(ContentNode):
    """Code block with monospace formatting."""
    
    type: Literal["code"] = "code"
    code: Optional[str] = Field(default=None, description="Code content")
    path: Optional[str] = Field(default=None, description="Absolute path to code file")
    caption: Optional[str] = Field(default=None, description="Caption above code")
    language: Optional[str] = Field(default=None, description="Language hint")

    @model_validator(mode="after")
    def validate_content_source(self) -> "CodeBlockData":
        """Ensure either code or path is provided."""
        if not self.code and not self.path:
            raise ValueError("CodeBlockData requires either 'code' or 'path' to be provided.")
        return self


# ============================================================
# List Content
# ============================================================

class ListData(ContentNode):
    """Bulleted or numbered list."""
    
    type: Literal["list"] = "list"
    items: List[str] = Field(default_factory=list, description="List items")
    style: str = Field(
        default="bullet", 
        description="List style: bullet, numbered, alpha (Cyrillic)"
    )
    level: int = Field(default=1, ge=1, description="Nesting level")
    
    @field_validator("style")
    @classmethod
    def validate_style(cls, v: str) -> str:
        """Normalize list style aliases."""
        allowed = {"bullet", "numbered", "alpha", "letters", "alpha_cyrillic", "latin", "alpha_latin"}
        if v not in allowed:
            return "bullet"
        if v == "letters":
            return "alpha"
        return v


# ============================================================
# Table Content
# ============================================================

class TableData(ContentNode):
    """Grid table with header row support."""
    
    type: Literal["table"] = "table"
    rows: List[List[Union[str, dict]]] = Field(
        default_factory=list, 
        description="Table rows (first row = header)"
    )
    style: str = Field(default="Table Grid", description="Word table style")
    repeat_header: bool = Field(default=True, description="Repeat first row as header on new pages")
    caption: Optional[str] = Field(default=None, description="Caption above table")


# ============================================================
# Image Content
# ============================================================

class ImageData(ContentNode):
    """Image with optional caption."""
    
    type: Literal["image"] = "image"
    path: str = Field(..., description="Path to image file")
    width_cm: Optional[float] = Field(default=None, description="Width in cm")
    height_cm: Optional[float] = Field(default=None, description="Height in cm")
    align: str = Field(default="center", description="Image alignment")
    caption: Optional[str] = Field(default=None, description="Caption below image")
    placeholder: bool = Field(default=False, description="Use placeholder instead of real image")


# ============================================================
# Formula Content
# ============================================================

class FormulaData(ContentNode):
    """Formula content (LaTeX)."""
    
    type: Literal["formula"] = "formula"
    content: str = Field(..., description="LaTeX content (without $ delimiters)")
    caption: Optional[str] = Field(default=None, description="Optional caption")
    align: str = Field(default="center", description="Alignment")


# ============================================================
# Special Nodes
# ============================================================

class PageBreakData(ContentNode):
    """Page break marker (Legacy, prefer BreakData)."""
    type: Literal["page_break"] = "page_break"


class BreakData(ContentNode):
    """Explicit break or separator."""
    
    type: Literal["break"] = "break"
    style: Literal["line", "page", "section"] = Field(
        default="line", 
        description="Type of break: 'line' (empty space), 'page' (ctrl+enter)"
    )
    count: int = Field(default=1, ge=1, description="Number of lines (for style=line)")


# ============================================================
# Union Type for Dispatch
# ============================================================

AnyContentNode = Union[
    ParagraphData,
    HeadingData,
    CodeBlockData,
    ListData,
    TableData,
    ImageData,
    FormulaData,
    PageBreakData,
    BreakData,
]


def parse_content_node(data: dict) -> AnyContentNode:
    """
    Parse raw dict to typed content node.
    
    Args:
        data: Raw dictionary from YAML content list.
        
    Returns:
        Typed Pydantic model instance.
        
    Raises:
        ValueError: If node type is unknown or validation fails.
    """
    node_type = data.get("type")
    
    type_map = {
        "paragraph": ParagraphData,
        "heading": HeadingData,
        "code": CodeBlockData,
        "list": ListData,
        "table": TableData,
        "image": ImageData,
        "formula": FormulaData,
        "page_break": PageBreakData,
        "break": BreakData,
    }
    
    model_class = type_map.get(node_type)
    if model_class is None:
        raise ValueError(f"Unknown content node type: '{node_type}'")
    
    return model_class.model_validate(data)
