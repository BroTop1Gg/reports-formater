"""
Style Manager service for Reports-Formater.

Scans Word templates to map requested style names to actual XML style IDs.
Provides robust style resolution with fallback and logging.
"""

import logging
from typing import Dict, Optional

from docx import Document
from docx.styles.style import BaseStyle

logger = logging.getLogger(__name__)


class StyleManager:
    """
    Manages Word document style resolution.
    
    Scans the template at startup to map requested style names 
    to actual XML style IDs present in the document.
    
    Handles common issues:
    - Case sensitivity ("Heading 1" vs "heading 1")
    - Spacing variations ("Heading1" vs "Heading 1")
    - Missing styles (graceful fallback)
    """
    
    # Common style name variations for normalization
    NORMALIZATION_MAP = {
        "heading1": "Heading 1",
        "heading2": "Heading 2",
        "heading3": "Heading 3",
        "tablegrid": "Table Grid",
        "listparagraph": "List Paragraph",
    }
    
    def __init__(self, doc: Document):
        """
        Initialize StyleManager by scanning document styles.
        
        Args:
            doc: Word Document instance to scan for available styles.
        """
        self._doc = doc
        self._available_styles: Dict[str, BaseStyle] = {}
        self._normalized_map: Dict[str, str] = {}
        self._cache: Dict[str, str] = {}
        
        self._scan_styles()
    
    def _scan_styles(self) -> None:
        """Scan and index all available styles in the document."""
        for style in self._doc.styles:
            if style.name:
                self._available_styles[style.name] = style
                # Create normalized key for fuzzy matching
                normalized = self._normalize(style.name)
                self._normalized_map[normalized] = style.name
        
        logger.debug(f"StyleManager: Found {len(self._available_styles)} styles")
    
    @staticmethod
    def _normalize(name: str) -> str:
        """
        Normalize style name for comparison.
        
        Removes spaces, converts to lowercase.
        
        Args:
            name: Original style name.
            
        Returns:
            Normalized string for comparison.
        """
        return name.lower().replace(" ", "").replace("_", "")
    
    def get_style(
        self, 
        requested_name: str, 
        fallback: str = "Normal"
    ) -> Optional[BaseStyle]:
        """
        Get style object by name with fuzzy matching.
        
        Resolves style in the following order: exact match, normalized match
        (case-insensitive, no spaces), predefined variation mapping, and finally
        the fallback style.
        
        Args:
            requested_name: Requested style name.
            fallback: Fallback style name if not found.
            
        Returns:
            Style object or None if even fallback not found.
        """
        # Check cache first
        if requested_name in self._cache:
            cached_name = self._cache[requested_name]
            return self._available_styles.get(cached_name)
        
        resolved_name = self._resolve_name(requested_name, fallback)
        self._cache[requested_name] = resolved_name
        
        return self._available_styles.get(resolved_name)
    
    def get_style_name(
        self, 
        requested_name: str, 
        fallback: str = "Normal"
    ) -> str:
        """
        Resolve style name string for use in python-docx.
        
        Args:
            requested_name: Requested style name.
            fallback: Fallback style name if not found.
            
        Returns:
            Resolved style name string.
        """
        if requested_name in self._cache:
            return self._cache[requested_name]
        
        resolved = self._resolve_name(requested_name, fallback)
        self._cache[requested_name] = resolved
        return resolved
    
    def _resolve_name(self, requested_name: str, fallback: str) -> str:
        """
        Internal resolution logic.
        
        Args:
            requested_name: Requested style name.
            fallback: Fallback if not found.
            
        Returns:
            Best matching style name.
        """
        # Check for exact match
        if requested_name in self._available_styles:
            return requested_name
        
        # Check for normalized match
        normalized = self._normalize(requested_name)
        if normalized in self._normalized_map:
            actual_name = self._normalized_map[normalized]
            logger.debug(
                f"StyleManager: Normalized '{requested_name}' -> '{actual_name}'"
            )
            return actual_name
        
        # Check predefined variations
        if normalized in self.NORMALIZATION_MAP:
            mapped = self.NORMALIZATION_MAP[normalized]
            if mapped in self._available_styles:
                logger.debug(
                    f"StyleManager: Mapped '{requested_name}' -> '{mapped}'"
                )
                return mapped
        
        # Use fallback style
        logger.warning(
            f"StyleManager: Style '{requested_name}' not found. "
            f"Using fallback: '{fallback}'"
        )
        
        if fallback in self._available_styles:
            return fallback
        
        # Last resort: return first available style or "Normal"
        if self._available_styles:
            first_available = next(iter(self._available_styles.keys()))
            logger.warning(
                f"StyleManager: Even fallback '{fallback}' not found. "
                f"Using: '{first_available}'"
            )
            return first_available
        
        return "Normal"
    
    def has_style(self, name: str) -> bool:
        """
        Check if style exists (exact or fuzzy match).
        
        Args:
            name: Style name to check.
            
        Returns:
            True if style can be resolved.
        """
        if name in self._available_styles:
            return True
        
        normalized = self._normalize(name)
        return normalized in self._normalized_map
    
    def list_available(self) -> list[str]:
        """
        List all available style names.
        
        Returns:
            List of style names.
        """
        return list(self._available_styles.keys())
