"""
Rendering Service for Reports-Formater.

Orchestrates content rendering with renderer registry and dispatch.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from docx import Document

from src.renderers.base import BaseRenderer, RenderContext, ContentContainer
from src.config.models import ReportConfig
from src.config.schemas import parse_content_node
from src.services.style_manager import StyleManager

logger = logging.getLogger(__name__)


class RenderingService:
    """
    Central service for rendering content nodes.
    
    Features:
    - Renderer registry (Strategy pattern)
    - Node dispatch based on type
    - Context management for recursion
    """
    
    def __init__(self):
        """Initialize RenderingService with empty registry."""
        self._renderers: Dict[str, BaseRenderer] = {}
    
    def register(self, renderer: BaseRenderer) -> None:
        """
        Register a renderer for its node type.
        
        Args:
            renderer: Renderer instance to register.
        """
        node_type = renderer.node_type
        self._renderers[node_type] = renderer
        logger.debug(f"RenderingService: Registered renderer for '{node_type}'")
    
    def register_all(self, renderers: List[BaseRenderer]) -> None:
        """
        Register multiple renderers.
        
        Args:
            renderers: List of renderer instances.
        """
        for renderer in renderers:
            self.register(renderer)
    
    def create_context(
        self,
        doc: Document,
        container: ContentContainer,
        config: ReportConfig,
        style_manager: StyleManager,
        resource_path: Path,
    ) -> RenderContext:
        """
        Create initial render context.
        
        Args:
            doc: Root Document object.
            container: Initial write target.
            config: Report configuration.
            style_manager: Style resolution service.
            resource_path: Base path for resources.
            
        Returns:
            Configured RenderContext.
        """
        return RenderContext(
            doc=doc,
            container=container,
            config=config,
            style_manager=style_manager,
            resource_path=resource_path,
            dispatch=lambda data: self.dispatch(
                RenderContext(
                    doc=doc,
                    container=container,
                    config=config,
                    style_manager=style_manager,
                    resource_path=resource_path,
                    dispatch=lambda d: None,  # Placeholder, will be set properly
                ),
                data
            ),
        )
    
    def dispatch(self, context: RenderContext, data: Any) -> None:
        """
        Dispatch content node to appropriate renderer.
        
        Args:
            context: Current render context.
            data: Raw content node dictionary or parsed Pydantic model.
            
        Raises:
            ValueError: If node type is unknown.
        """
        if isinstance(data, dict):
            node_type = data.get("type")
            try:
                typed_data = parse_content_node(data)
            except Exception as e:
                logger.error(f"RenderingService: Failed to parse node: {e}")
                return
        else:
            node_type = getattr(data, "type", None)
            typed_data = data
        
        if node_type not in self._renderers:
            logger.warning(f"RenderingService: No renderer for type '{node_type}'")
            return
        
        renderer = self._renderers[node_type]
        
        # Render
        renderer.render(context, typed_data)
    
    def render_content(
        self,
        context: RenderContext,
        content: List[Any],
    ) -> None:
        """
        Render list of content nodes.
        
        Args:
            context: Render context.
            content: List of raw content node dictionaries or Pydantic models.
        """
        for node_data in content:
            self.dispatch(context, node_data)
