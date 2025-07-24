"""
Unit tests for SIF Engine Jinja2 environment setup
"""

import pytest
from pathlib import Path

from app.sif_engine.env import get_env, format_float, format_boolean, reset_env


class TestFormatFilters:
    """Test custom format filters"""
    
    def test_format_float_small_values(self):
        """Test formatting very small float values"""
        assert format_float(0) == "0.0"
        assert format_float(1e-15) == "0.0"
        assert format_float(-1e-12) == "0.0"
    
    def test_format_float_normal_values(self):
        """Test formatting normal float values"""
        assert format_float(1.23456789) == "1.234568"
        assert format_float(100.0) == "100"
        assert format_float(0.001) == "0.001"
        assert format_float(0.999999) == "1"
    
    def test_format_float_large_values(self):
        """Test formatting large float values"""
        assert format_float(1e6) == "1.000000e+06"
        assert format_float(210e9) == "2.100000e+11"
        assert format_float(-5.67e8) == "-5.670000e+08"
    
    def test_format_float_custom_precision(self):
        """Test formatting with custom precision"""
        assert format_float(1.23456789, precision=2) == "1.23"
        assert format_float(1e6, precision=3) == "1.000e+06"
    
    def test_format_boolean(self):
        """Test boolean formatting"""
        assert format_boolean(True) == "True"
        assert format_boolean(False) == "False"
        assert format_boolean(1) == "True"  # Truthy value
        assert format_boolean(0) == "False"  # Falsy value


class TestJinja2Environment:
    """Test Jinja2 environment setup"""
    
    def test_get_env_singleton(self):
        """Test that get_env returns singleton instance"""
        env1 = get_env()
        env2 = get_env()
        assert env1 is env2
    
    def test_env_configuration(self):
        """Test environment configuration"""
        env = get_env()
        
        # Check loader configuration
        assert env.loader is not None
        assert not env.autoescape
        assert env.trim_blocks
        assert env.lstrip_blocks
        assert env.keep_trailing_newline
    
    def test_custom_filters(self):
        """Test custom filters are registered"""
        env = get_env()
        
        # Check filters exist
        assert 'format_float' in env.filters
        assert 'format_bool' in env.filters
        
        # Test filter functions
        assert env.filters['format_float'] is format_float
        assert env.filters['format_bool'] is format_boolean
    
    def test_global_functions(self):
        """Test global functions are available"""
        env = get_env()
        
        assert 'len' in env.globals
        assert 'enumerate' in env.globals
        assert env.globals['len'] is len
        assert env.globals['enumerate'] is enumerate
    
    def test_template_directory(self):
        """Test template directory is configured correctly"""
        env = get_env()
        
        # Get loader's search path
        search_paths = env.loader.searchpath
        assert len(search_paths) > 0
        
        template_dir = Path(search_paths[0])
        assert template_dir.exists()
        assert template_dir.name == "sif"
    
    def test_reset_env(self):
        """Test environment reset functionality"""
        # Get initial environment
        env1 = get_env()
        
        # Reset
        reset_env()
        
        # Get new environment
        env2 = get_env()
        
        # Should be different instances
        assert env1 is not env2
    
    def test_render_with_filters(self):
        """Test rendering with custom filters"""
        env = get_env()
        
        # Create inline template
        template = env.from_string("""
        Value: {{ value|format_float }}
        Flag: {{ flag|format_bool }}
        Length: {{ items|length }}
        """)
        
        result = template.render(
            value=123.456789,
            flag=True,
            items=[1, 2, 3]
        )
        
        assert "Value: 123.456789" in result
        assert "Flag: True" in result
        assert "Length: 3" in result 