"""
Base abstractions for Reports-Formater renderers.

Defines core protocols and interfaces:
- ContentContainer: Polymorphic write target (Document, Cell, Header)
- RenderContext: State and dependency carrier for rendering
- BaseRenderer: Abstract base for all content renderers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Protocol, runtime_checkable

from pydantic import BaseModel

if TYPE_CHECKING:
    from docx import Document
    from src.config.models import ReportConfig
    from src.services.style_manager import StyleManager


# ============================================================
# ContentContainer Protocol
# ============================================================

@runtime_checkable
class ContentContainer(Protocol):
    """
    Protocol for objects that can receive content.
    
    Abstracts the difference between writing to:
    - Document body
    - Table cells
    - Headers/Footers
    
    This enables recursive rendering into nested structures.
    """
    
    def add_paragraph(self, text: str = "", style: Any = None) -> Any:
        """
        Add a paragraph to the container.
        
        Args:
            text: Initial paragraph text.
            style: Optional style name or object.
            
        Returns:
            Paragraph object.
        """
        ...
    
    def add_table(self, rows: int, cols: int, style: Any = None) -> Any:
        """
        Add a table to the container.
        
        Args:
            rows: Number of rows.
            cols: Number of columns.
            style: Optional table style.
            
        Returns:
            Table object.
        """
        ...


# ============================================================
# RenderContext
# ============================================================

@dataclass
class RenderContext:
    """
    Context object for rendering operations.
    
    Carries state, dependencies, and resources through the render tree.
    The `container` reference changes during recursion (document → cell → etc).
    
    Attributes:
        doc: Root Document reference (for styles, sections, numbering).
        container: Current write target (changes during recursion).
        config: Global ReportConfig.
        style_manager: Style resolution service.
        resource_path: Base path for resolving relative image/file links.
        dispatch: Callback to RenderingService for nested node rendering.
        list_level: Current list nesting depth.
    """
    
    doc: "Document"
    container: ContentContainer
    config: "ReportConfig"
    style_manager: "StyleManager"
    resource_path: Path
    dispatch: Callable[[Dict[str, Any]], None]
    
    # State markers
    list_level: int = field(default=0)
    
    def with_container(self, new_container: ContentContainer) -> "RenderContext":
        """
        Create new context with different container (for recursion).
        
        Args:
            new_container: New write target (e.g., table cell).
            
        Returns:
            New RenderContext with updated container.
        """
        return RenderContext(
            doc=self.doc,
            container=new_container,
            config=self.config,
            style_manager=self.style_manager,
            resource_path=self.resource_path,
            dispatch=self.dispatch,
            list_level=self.list_level,
        )
    
    def with_list_level(self, level: int) -> "RenderContext":
        """
        Create new context with updated list level.
        
        Args:
            level: New list nesting level.
            
        Returns:
            New RenderContext with updated list_level.
        """
        return RenderContext(
            doc=self.doc,
            container=self.container,
            config=self.config,
            style_manager=self.style_manager,
            resource_path=self.resource_path,
            dispatch=self.dispatch,
            list_level=level,
        )


# ============================================================
# BaseRenderer
# ============================================================

class BaseRenderer(ABC):
    """
    Abstract base class for all content renderers.
    
    Each renderer handles one content type (paragraph, heading, table, etc.).
    Renderers are stateless; all state is carried via RenderContext.
    
    Subclasses must implement the `render()` method.
    """
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        """
        Content node type this renderer handles.
        
        Returns:
            String type identifier (e.g., "paragraph", "heading").
        """
        ...
    
    @abstractmethod
    def render(self, context: RenderContext, data: BaseModel) -> None:
        """
        Render content node to document.
        
        Args:
            context: Render context with container, config, and state.
            data: Validated Pydantic model for the content node.
        """
        ...
