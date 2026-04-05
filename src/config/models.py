"""
Configuration models for the Reports-Formater.

Defines Pydantic models for type-safe configuration management.
These models map directly to `report_styles.json` structure.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SpacingRuleConfig(BaseModel):
    """Configuration for automatic spacing around specific nodes."""
    before: int = Field(default=0, description="Empty lines to inject before the node")
    after: int = Field(default=0, description="Empty lines to inject after the node")
    skip_if_first: bool = Field(default=False, description="Do not inject before space if it's the first node")
    skip_if_last: bool = Field(default=False, description="Do not inject after space if it's the last node")


class SpacingRulesConfig(BaseModel):
    """Collection of rules for dynamic spacing engine."""
    heading: SpacingRuleConfig = Field(default_factory=lambda: SpacingRuleConfig(before=1, after=1, skip_if_first=True))
    heading_1: Optional[SpacingRuleConfig] = None
    heading_2: Optional[SpacingRuleConfig] = None
    heading_3: Optional[SpacingRuleConfig] = None
    image: SpacingRuleConfig = Field(default_factory=lambda: SpacingRuleConfig(before=1, after=1, skip_if_first=True, skip_if_last=True))
    code: SpacingRuleConfig = Field(default_factory=lambda: SpacingRuleConfig(before=1, after=1, skip_if_first=True))
    table: SpacingRuleConfig = Field(default_factory=lambda: SpacingRuleConfig(before=1, after=1, skip_if_first=True))
    formula: SpacingRuleConfig = Field(default_factory=lambda: SpacingRuleConfig(before=1, after=1, skip_if_first=False))
    caption: SpacingRuleConfig = Field(default_factory=lambda: SpacingRuleConfig(before=1, after=0, skip_if_first=False))


class PageSetupConfig(BaseModel):
    """Page margin and layout configuration (DSTU 3008-2015 defaults)."""
    
    """Page layout configuration."""
    margin_top_cm: float = Field(default=2.0, description="Top margin in cm")
    margin_bottom_cm: float = Field(default=2.0, description="Bottom margin in cm")
    margin_left_cm: float = Field(default=3.0, description="Left margin in cm")
    margin_right_cm: float = Field(default=1.5, description="Right margin in cm")
    header_distance_cm: float = Field(default=1.25, description="Distance from top of page to header")
    footer_distance_cm: float = Field(default=1.25, description="Distance from bottom of page to footer")
    image_fit_padding_cm: float = Field(default=0, description="Vertical padding/reserve subtracted from page height when fit_to_page is active")


class FontConfig(BaseModel):
    """Font family configuration."""
    
    default_name: str = Field(default="Times New Roman", description="Default body font")
    code_name: str = Field(default="Consolas", description="Monospace font for code")


class StyleConfig(BaseModel):
    """Individual style definition for paragraphs, headings, lists."""
    
    font_size_pt: int = Field(default=14, description="Font size in points")
    line_spacing: float = Field(default=1.5, description="Line spacing multiplier")
    first_line_indent_cm: float = Field(default=0, description="First line indent in cm")
    left_indent_cm: Optional[float] = Field(default=None, description="Left indent")
    hanging_indent_cm: Optional[float] = Field(default=None, description="Hanging indent")
    space_before_pt: int = Field(default=0, description="Space before paragraph")
    space_after_pt: int = Field(default=0, description="Space after paragraph")
    alignment: str = Field(default="left", description="Text alignment") # mb make it 'justify'? 'justify' used more often in reports than 'left'.
    bold: bool = Field(default=False, description="Bold text")
    font_name: Optional[str] = Field(default=None, description="Font family name (overrides default)")
    list_level_step_cm: Optional[float] = Field(default=None, description="List level indent step")
    list_prefix_width_cm: Optional[float] = Field(default=None, description="Width allocated for list prefix (bullet/number)")


class PageNumberingConfig(BaseModel):
    """Page numbering configuration."""
    
    enabled: bool = Field(default=False, description="Enable page numbering")
    position: str = Field(default="header", description="Position: header or footer")
    alignment: str = Field(default="right", description="Alignment: left, center, right")
    font_size_pt: int = Field(default=12, description="Font size for page headers and footers")


class StylesConfig(BaseModel):
    """Collection of all style definitions."""
    
    normal: StyleConfig = Field(default_factory=lambda: StyleConfig(
        font_size_pt=14,
        line_spacing=1.5,
        first_line_indent_cm=1.25,
        alignment="justify"
    ))
    code_block: StyleConfig = Field(default_factory=lambda: StyleConfig(
        font_size_pt=12,
        line_spacing=1.0,
        first_line_indent_cm=0.0,
        alignment="left"
    ))
    inline_code: StyleConfig = Field(default_factory=lambda: StyleConfig(
        font_size_pt=12
    ))
    heading_base: StyleConfig = Field(default_factory=lambda: StyleConfig(
        font_size_pt=14,
        bold=True,
        alignment="center",
        first_line_indent_cm=0.0
    ))
    heading_1: Optional[StyleConfig] = None
    heading_2: Optional[StyleConfig] = None
    heading_3: StyleConfig = Field(default_factory=StyleConfig)
    list_item: StyleConfig = Field(default_factory=lambda: StyleConfig(
        font_size_pt=14,
        line_spacing=1.5,
        alignment="justify",
        left_indent_cm=2.25,
        first_line_indent_cm=0
    ))
    caption: StyleConfig = Field(default_factory=lambda: StyleConfig(
        font_size_pt=14,
        line_spacing=1.5,
        alignment="left",
        first_line_indent_cm=1.25
    ))
    header_footer: StyleConfig = Field(default_factory=lambda: StyleConfig(font_size_pt=12, alignment="right"))


class ReportConfig(BaseModel):
    """
    Root configuration model.
    
    Represents the complete `report_styles.json` structure with
    type validation and sensible defaults.
    """
    
    page_setup: PageSetupConfig = Field(default_factory=PageSetupConfig)
    fonts: FontConfig = Field(default_factory=FontConfig)
    styles: StylesConfig = Field(default_factory=StylesConfig)
    page_numbering: PageNumberingConfig = Field(default_factory=PageNumberingConfig)
    spacing_rules: SpacingRulesConfig = Field(default_factory=SpacingRulesConfig)
