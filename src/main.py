#!/usr/bin/env python3
"""
Reports-Formater CLI Entry Point.

Generate DSTU-compliant Word reports from YAML or Markdown content files.

Usage:
    python -m src.main input.yaml --output report.docx
    python -m src.main input.md --output report.docx
    python -m src.main input.yaml --template template.docx --output report.docx
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml

from src.report_factory import ReportFactory


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.
    
    Args:
        verbose: Enable debug-level logging if True.
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Generate DOCX reports from YAML or Markdown content.",
        prog="reports-formater",
    )
    
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to input YAML or Markdown file.",
    )
    
    parser.add_argument(
        "--template",
        type=Path,
        default=None,
        help="Path to template DOCX file.",
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output.docx"),
        help="Path to output file (default: output.docx).",
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to report_styles.json config file.",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging.",
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    
    # Validate input file
    if not args.input_file.exists():
        logger.error(f"Input file not found: {args.input_file}")
        return 1
    
    # Determine file type and load accordingly
    input_ext = args.input_file.suffix.lower()
    
    try:
        if input_ext in (".md", ".markdown"):
            # Markdown with YAML Front-Matter
            yaml_data = _load_markdown_file(args.input_file, logger)
            if yaml_data is None:
                return 1
        elif input_ext in (".yaml", ".yml"):
            # Legacy YAML pipeline
            yaml_data = _load_yaml_file(args.input_file, logger)
            if yaml_data is None:
                return 1
        else:
            logger.error(f"Unsupported file type: {input_ext}. Use .yaml, .yml, .md, or .markdown")
            return 1
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        return 1
    
    # Create factory
    factory = ReportFactory(
        config_path=args.config,
        template_path=args.template,
    )
    
    # Build report
    try:
        resource_path = args.input_file.parent
        actual_output = factory.build(
            yaml_data=yaml_data,
            output_path=args.output,
            resource_path=resource_path,
        )
        
        logger.info(f"Report generated: {actual_output}")
        print(f"Done. Saved to {actual_output}")
        return 0
        
    except Exception as e:
        logger.exception(f"Failed to generate report: {e}")
        return 1


def _load_yaml_file(path: Path, logger: logging.Logger) -> dict | None:
    """Load and parse a YAML file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML: {e}")
        return None


def _load_markdown_file(path: Path, logger: logging.Logger) -> dict | None:
    """
    Load a Markdown file with YAML Front-Matter.
    
    Format:
        ---
        metadata:
          VERSION: "1.0"
        page_numbering: false
        ---
        # Heading 1
        
        Content...
    
    Returns:
        dict with 'metadata', 'content', and any global overrides, or None on error.
    """
    from src.sdk.markdown_parser import parse_markdown_to_nodes
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read Markdown file: {e}")
        return None
    
    # Parse YAML Front-Matter
    front_matter = {}
    markdown_body = content
    
    if content.startswith("---"):
        # Find closing ---
        parts = content.split("---", 2)
        if len(parts) >= 3:
            front_matter_yaml = parts[1].strip()
            markdown_body = parts[2].strip()
            
            try:
                front_matter = yaml.safe_load(front_matter_yaml) or {}
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse YAML Front-Matter: {e}")
                return None
    
    # Transpile Markdown body to nodes
    nodes = parse_markdown_to_nodes(markdown_body)
    
    # Build yaml_data structure
    yaml_data = {
        "content": nodes
    }
    
    # Merge front-matter into yaml_data
    # Support both nested 'metadata' key and flat global overrides
    if "metadata" in front_matter:
        yaml_data["metadata"] = front_matter["metadata"]
    
    # Copy global overrides (page_numbering, header_text, etc.)
    for key in ("page_numbering", "header_text"):
        if key in front_matter:
            yaml_data[key] = front_matter[key]
    
    return yaml_data


if __name__ == "__main__":
    sys.exit(main())
