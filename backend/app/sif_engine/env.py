"""
Jinja2 Environment setup for SIF template rendering
"""

import logging
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Singleton environment instance
_env: Optional[Environment] = None


def format_float(value: float, precision: int = 6) -> str:
    """
    Format float value for SIF output
    
    Args:
        value: Float value to format
        precision: Number of decimal places (default: 6)
        
    Returns:
        Formatted string representation
    """
    if abs(value) < 1e-10:
        return "0.0"
    elif abs(value) >= 1e6 or abs(value) < 1e-3:
        return f"{value:.{precision}e}"
    else:
        return f"{value:.{precision}f}".rstrip('0').rstrip('.')


def format_boolean(value: bool) -> str:
    """
    Format boolean value for SIF output
    
    Args:
        value: Boolean value
        
    Returns:
        "True" or "False" string
    """
    return "True" if value else "False"


def get_env() -> Environment:
    """
    Get or create the Jinja2 environment for SIF rendering
    
    Returns:
        Configured Jinja2 Environment instance
    """
    global _env
    
    if _env is None:
        # Determine template directory
        template_dir = Path(__file__).parent.parent.parent / "templates" / "sif"
        
        if not template_dir.exists():
            logger.warning(f"Template directory not found: {template_dir}")
            template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create environment with optimized settings for SIF files
        _env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,  # SIF files are plain text
            trim_blocks=True,  # Remove newline after blocks
            lstrip_blocks=True,  # Remove leading spaces from blocks
            keep_trailing_newline=True,  # Keep final newline
        )
        
        # Register custom filters
        _env.filters['format_float'] = format_float
        _env.filters['format_bool'] = format_boolean
        
        # Add global functions
        _env.globals['len'] = len
        _env.globals['enumerate'] = enumerate
        
        logger.info(f"Jinja2 environment initialized with template directory: {template_dir}")
    
    return _env


def reset_env() -> None:
    """Reset the environment (mainly for testing)"""
    global _env
    _env = None 