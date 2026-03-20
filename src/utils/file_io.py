"""
File I/O utilities for Reports-Formater.

Provides robust file saving with retry logic and error handling.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# Default retry configuration
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_DELAY_SECONDS = 2.0


@runtime_checkable
class Saveable(Protocol):
    """Protocol for objects that can be saved to a file path."""
    
    def save(self, path: str) -> None:
        """Save to file path."""
        ...


class FailSafeSaver:
    """
    Fail-safe document saver with retry and renaming capabilities.
    
    Handles common issues:
    - PermissionError when file is open in Word/LibreOffice
    - OSError for disk/path issues
    - Automatic timestamp-based rename on persistent failures
    
    Usage:
        saver = FailSafeSaver()
        actual_path = saver.save(document, Path("output.docx"))
    """
    
    def __init__(
        self, 
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY_SECONDS,
    ):
        """
        Initialize FailSafeSaver.
        
        Args:
            max_retries: Number of retry attempts before renaming.
            retry_delay: Delay between retries in seconds.
        """
        self._max_retries = max_retries
        self._retry_delay = retry_delay
    
    def save(self, document: Saveable, output_path: Path) -> Path:
        """
        Save document with retry logic.
        
        Args:
            document: Document object with save() method.
            output_path: Target output path.
            
        Returns:
            Actual path where document was saved (may differ if renamed).
            
        Raises:
            OSError: If all save attempts fail.
        """
        output_path = Path(output_path)
        
        # Ensure the parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Attempt normal save with retries
        for attempt in range(self._max_retries + 1):
            try:
                document.save(str(output_path))
                logger.info(f"Document saved: {output_path}")
                return output_path
            
            except PermissionError as e:
                if attempt < self._max_retries:
                    logger.warning(
                        f"Save attempt {attempt + 1} failed (file locked?). "
                        f"Retrying in {self._retry_delay}s..."
                    )
                    time.sleep(self._retry_delay)
                else:
                    logger.warning(
                        f"All {self._max_retries + 1} save attempts failed. "
                        "Attempting timestamp rename..."
                    )
                    return self._save_with_timestamp(document, output_path, e)
            
            except OSError as e:
                logger.error(f"OSError during save: {e}")
                return self._save_with_timestamp(document, output_path, e)
        
        # Should not reach here, but just in case
        raise OSError(f"Failed to save document to {output_path}")
    
    def _save_with_timestamp(
        self, 
        document: Saveable, 
        original_path: Path,
        original_error: Exception,
    ) -> Path:
        """
        Save document with timestamp suffix as fallback.
        
        Args:
            document: Document to save.
            original_path: Original intended path.
            original_error: The error that triggered fallback.
            
        Returns:
            New path with timestamp.
            
        Raises:
            OSError: If timestamp save also fails.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = original_path.stem
        suffix = original_path.suffix
        parent = original_path.parent
        
        new_name = f"{stem}_{timestamp}{suffix}"
        new_path = parent / new_name
        
        try:
            document.save(str(new_path))
            logger.warning(
                f"Document saved with timestamp rename: {new_path} "
                f"(original: {original_path})"
            )
            return new_path
        
        except Exception as e:
            logger.error(
                f"Timestamp rename save also failed: {e}. "
                f"Original error was: {original_error}"
            )
            raise OSError(
                f"Failed to save document. "
                f"Original path: {original_path}, "
                f"Timestamp path: {new_path}"
            ) from e
