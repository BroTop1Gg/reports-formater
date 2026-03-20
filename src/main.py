#!/usr/bin/env python3
"""
Reports-Formater CLI Entry Point.

Generate DSTU-compliant Word reports from YAML content files.

Usage:
    python -m src.main input.yaml --output report.docx
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
        description="Generate DOCX reports from YAML content.",
        prog="reports-formater",
    )
    
    parser.add_argument(
        "input_yaml",
        type=Path,
        help="Path to input YAML file.",
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
    if not args.input_yaml.exists():
        logger.error(f"Input file not found: {args.input_yaml}")
        return 1
    
    # Load YAML data
    try:
        with open(args.input_yaml, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML: {e}")
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
        resource_path = args.input_yaml.parent
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


if __name__ == "__main__":
    sys.exit(main())
