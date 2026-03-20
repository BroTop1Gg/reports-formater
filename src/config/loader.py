"""
Configuration loader with deep merge support.

Implements layered configuration:
1. Layer 1: Hardcoded Pydantic defaults (Code)
2. Layer 2: report_styles.json (Base Config)
3. Layer 3: Input YAML (Runtime Overrides)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .models import ReportConfig

logger = logging.getLogger(__name__)


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge override dict into base dict.
    
    Args:
        base: Base dictionary (will not be mutated).
        override: Override dictionary to merge on top.
        
    Returns:
        New dictionary with merged values.
        
    Example:
        >>> base = {"margins": {"top": 2, "bottom": 2}}
        >>> override = {"margins": {"top": 3}}
        >>> deep_merge(base, override)
        {"margins": {"top": 3, "bottom": 2}}
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


class ConfigLoader:
    """
    Loads and merges configuration from multiple sources.
    
    Implements the layered configuration strategy:
    - Pydantic defaults provide baseline
    - JSON config file overrides defaults
    - YAML runtime overrides have highest priority
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to report_styles.json. If None, uses default location.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "report_styles.json"
        
        self._config_path = config_path
        self._base_config: Optional[Dict[str, Any]] = None
    
    def _load_json_config(self) -> Dict[str, Any]:
        """
        Load JSON configuration file.
        
        Returns:
            Parsed JSON as dictionary.
            
        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If JSON is malformed.
        """
        if self._base_config is not None:
            return self._base_config
        
        if not self._config_path.exists():
            logger.warning(
                f"Config file not found: {self._config_path}. Using defaults."
            )
            return {}
        
        with open(self._config_path, "r", encoding="utf-8") as f:
            self._base_config = json.load(f)
            logger.debug(f"Loaded config from {self._config_path}")
            return self._base_config
    
    def load(self, yaml_overrides: Optional[Dict[str, Any]] = None) -> ReportConfig:
        """
        Load configuration with all layers merged.
        
        Args:
            yaml_overrides: Optional runtime overrides from YAML input.
            
        Returns:
            Fully merged and validated ReportConfig.
        """
        # Layer 1: Pydantic defaults (implicit in model)
        # Layer 2: JSON config file
        json_config = self._load_json_config()
        
        # Layer 3: YAML runtime overrides
        if yaml_overrides:
            # Normalize YAML shorthand values before merge
            normalized = self._normalize_yaml_overrides(yaml_overrides)
            merged = deep_merge(json_config, normalized)
        else:
            merged = json_config
        
        # Validate and return typed config
        return ReportConfig.model_validate(merged)
    
    def _normalize_yaml_overrides(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize YAML shorthand values to proper config structure.
        
        Handles legacy/shorthand patterns like:
        - page_numbering: true -> page_numbering: {enabled: true}
        - header_text: "..." -> stored separately for header processing
        
        Args:
            data: Raw YAML data dict.
            
        Returns:
            Normalized config dict.
        """
        result = data.copy()
        
        # Handle page_numbering shorthand
        if "page_numbering" in result:
            pn_value = result["page_numbering"]
            if isinstance(pn_value, bool):
                result["page_numbering"] = {"enabled": pn_value}
        
        return result
    
    def load_raw(self) -> Dict[str, Any]:
        """
        Load raw JSON config without Pydantic validation.
        
        Useful for backward compatibility with legacy code.
        
        Returns:
            Raw dictionary from JSON file.
        """
        return self._load_json_config()
