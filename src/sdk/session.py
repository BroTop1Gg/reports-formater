"""
ReportSession API for incremental report building.

Provides a stateful interface for adding content chunks and finalizing reports.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import ValidationError

from src.config.schemas import parse_content_node
from src.report_factory import ReportFactory
from src.sdk.markdown_parser import parse_markdown_to_nodes

logger = logging.getLogger(__name__)


class ReportSession:
    """
    Stateful session for building reports incrementally.
    
    Accumulates validated content nodes and generates final reports
    through ReportFactory.
    """
    
    def __init__(self, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new report session.
        
        Args:
            metadata: Global report configuration (template mapping, placeholders, etc.)
        """
        self.nodes: List[Any] = []
        self.metadata: Dict[str, Any] = metadata or {}
        self.chunk_index: int = 0
    
    def add_chunk(self, yaml_string: str) -> Dict[str, Any]:
        """
        Parse and validate a YAML chunk, adding nodes if all pass validation.
        
        Implements all-or-nothing validation: if ANY node fails, the entire
        chunk is discarded and no nodes are added.
        
        Args:
            yaml_string: YAML string containing a list of content node dicts.
            
        Returns:
            Dict with 'status' key ('success' or 'error').
            On success: includes 'outline' list of headings/tables.
            On error: includes 'errors' list of error details.
        """
        # Parse YAML
        try:
            raw_nodes = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            return {
                "status": "error",
                "errors": [{"type": "yaml_parse_error", "message": str(e)}]
            }
        
        # Validate input is a list
        if not isinstance(raw_nodes, list):
            return {
                "status": "error",
                "errors": [{"type": "invalid_structure", "message": "YAML must be a list of nodes"}]
            }
        
        # All-or-nothing validation
        parsed_nodes = []
        errors = []
        
        for idx, node_dict in enumerate(raw_nodes):
            if not isinstance(node_dict, dict):
                errors.append({
                    "node_index": idx,
                    "type": "invalid_node",
                    "message": f"Node must be a dict, got {type(node_dict).__name__}"
                })
                continue
            
            try:
                # Validate using parse_content_node
                validated = parse_content_node(node_dict)
                
                # Additional check: if it's an image node, verify path exists
                if validated.type == "image" and not getattr(validated, 'placeholder', False):
                    image_path = Path(validated.path)
                    if not image_path.is_absolute():
                        # Relative paths are resolved at render time, so skip this check
                        pass
                    elif not image_path.exists():
                        raise FileNotFoundError(f"Image not found: {image_path}")
                
                parsed_nodes.append(validated)
                
            except ValidationError as e:
                errors.append({
                    "node_index": idx,
                    "type": "validation_error",
                    "message": str(e),
                    "node": node_dict
                })
            except FileNotFoundError as e:
                errors.append({
                    "node_index": idx,
                    "type": "file_not_found",
                    "message": str(e),
                    "node": node_dict
                })
            except (ValueError, Exception) as e:
                errors.append({
                    "node_index": idx,
                    "type": "parse_error",
                    "message": str(e),
                    "node": node_dict
                })
        
        # If any errors, discard entire chunk
        if errors:
            return {
                "status": "error",
                "errors": errors
            }
        
        # All nodes passed validation - extend session state
        self.nodes.extend(parsed_nodes)
        self.chunk_index += 1
        
        # Build outline (headings and tables only)
        outline = []
        for node in parsed_nodes:
            if node.type == "heading":
                outline.append({
                    "type": "heading",
                    "level": node.level,
                    "text": node.text
                })
            elif node.type == "table":
                caption = getattr(node, 'caption', None) or "Untitled Table"
                outline.append({
                    "type": "table",
                    "caption": caption
                })
        
        # Write backup to draft_report.yaml
        try:
            self._write_backup()
        except Exception as e:
            logger.warning(f"Failed to write backup: {e}")
        
        return {
            "status": "success",
            "outline": outline
        }
    
    def add_markdown_chunk(self, md_string: str) -> Dict[str, Any]:
        """
        Parse Markdown content and add validated nodes to the session.
        
        This method transpiles Pandoc-style academic Markdown into raw dictionary
        nodes, then passes them through the existing transaction-safe add_chunk()
        pipeline for Pydantic validation and state accumulation.
        
        Args:
            md_string: Markdown text string (Pandoc-style academic format).
            
        Returns:
            Dict with 'status' key ('success' or 'error').
            On success: includes 'outline' list of headings/tables.
            On error: includes 'errors' list of error details.
        """
        # Step 1: Parse Markdown to raw dict nodes
        try:
            raw_nodes = parse_markdown_to_nodes(md_string)
        except Exception as e:
            return {
                "status": "error",
                "errors": [{"type": "markdown_parse_error", "message": str(e)}]
            }
        
        if not raw_nodes:
            return {
                "status": "success",
                "outline": []
            }
        
        # Step 2: Convert raw dicts to YAML string
        yaml_string = yaml.dump(raw_nodes, default_flow_style=False, allow_unicode=True)
        
        # Step 3: Pass through existing transaction-safe pipeline
        return self.add_chunk(yaml_string)
    
    def finalize(
        self,
        output_path: Path,
        config_path: Optional[Path] = None,
        resource_path: Optional[Path] = None
    ) -> Path:
        """
        Generate the final report using ReportFactory.
        
        Constructs synthetic YAML data structure and delegates to ReportFactory.build().
        
        Args:
            output_path: Path where the final .docx will be saved.
            config_path: Optional path to report_styles.json config.
            resource_path: Optional base path for resolving relative resources.
            
        Returns:
            Actual path where document was saved.
        """
        output_path = Path(output_path)
        
        # Serialize Pydantic models back to dicts
        raw_content = []
        for node in self.nodes:
            try:
                # Pydantic V2
                raw_content.append(node.model_dump())
            except AttributeError:
                # Pydantic V1 fallback
                raw_content.append(node.dict())
        
        # Construct synthetic YAML data structure
        yaml_data = {
            "metadata": self.metadata,
            "content": raw_content
        }
        
        # Instantiate ReportFactory and build
        factory = ReportFactory(config_path=config_path)
        return factory.build(
            yaml_data=yaml_data,
            output_path=output_path,
            resource_path=resource_path
        )
    
    def _write_backup(self) -> None:
        """Write current session state to draft_report.yaml for recovery."""
        backup_data = {
            "metadata": self.metadata,
            "chunk_index": self.chunk_index,
            "content": []
        }
        
        # Serialize nodes
        for node in self.nodes:
            try:
                backup_data["content"].append(node.model_dump())
            except AttributeError:
                backup_data["content"].append(node.dict())
        
        # Write to draft_report.yaml in current directory
        backup_path = Path("draft_report.yaml")
        with open(backup_path, "w", encoding="utf-8") as f:
            yaml.dump(backup_data, f, default_flow_style=False, allow_unicode=True)
        
        logger.debug(f"Backup written to {backup_path}")
