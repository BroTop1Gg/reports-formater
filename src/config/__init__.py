"""Config package for Reports-Formater."""

from .models import (
    ReportConfig,
    PageSetupConfig,
    FontConfig,
    StyleConfig,
    StylesConfig,
    PageNumberingConfig,
)
from .loader import ConfigLoader, deep_merge
from .schemas import (
    ContentNode,
    ParagraphData,
    HeadingData,
    CodeBlockData,
    ListData,
    TableData,
    ImageData,
    PageBreakData,
    AnyContentNode,
    parse_content_node,
)

__all__ = [
    # Models
    "ReportConfig",
    "PageSetupConfig",
    "FontConfig",
    "StyleConfig",
    "StylesConfig",
    "PageNumberingConfig",
    # Loader
    "ConfigLoader",
    "deep_merge",
    # Schemas
    "ContentNode",
    "ParagraphData",
    "HeadingData",
    "CodeBlockData",
    "ListData",
    "TableData",
    "ImageData",
    "PageBreakData",
    "AnyContentNode",
    "parse_content_node",
]
