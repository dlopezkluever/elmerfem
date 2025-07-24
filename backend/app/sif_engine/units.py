"""
Unit conversion utilities for ElmerFEM SIF generation
"""

from typing import Optional, Tuple, Union

# Define standard SI unit conversions
LENGTH_CONVERSIONS = {
    "m": 1.0,
    "meter": 1.0,
    "meters": 1.0,
    "cm": 0.01,
    "centimeter": 0.01,
    "centimeters": 0.01,
    "mm": 0.001,
    "millimeter": 0.001,
    "millimeters": 0.001,
    "km": 1000.0,
    "kilometer": 1000.0,
    "kilometers": 1000.0,
    "in": 0.0254,
    "inch": 0.0254,
    "inches": 0.0254,
    "ft": 0.3048,
    "foot": 0.3048,
    "feet": 0.3048,
    "yd": 0.9144,
    "yard": 0.9144,
    "yards": 0.9144,
}

TEMPERATURE_CONVERSIONS = {
    "K": lambda x: x,
    "kelvin": lambda x: x,
    "C": lambda x: x + 273.15,
    "celsius": lambda x: x + 273.15,
    "F": lambda x: (x - 32) * 5/9 + 273.15,
    "fahrenheit": lambda x: (x - 32) * 5/9 + 273.15,
}

PRESSURE_CONVERSIONS = {
    "Pa": 1.0,
    "pascal": 1.0,
    "kPa": 1000.0,
    "kilopascal": 1000.0,
    "MPa": 1e6,
    "megapascal": 1e6,
    "GPa": 1e9,
    "gigapascal": 1e9,
    "bar": 1e5,
    "atm": 101325.0,
    "atmosphere": 101325.0,
    "psi": 6894.76,
}

FORCE_CONVERSIONS = {
    "N": 1.0,
    "newton": 1.0,
    "kN": 1000.0,
    "kilonewton": 1000.0,
    "MN": 1e6,
    "meganewton": 1e6,
    "lbf": 4.44822,
    "pound": 4.44822,
}

ENERGY_CONVERSIONS = {
    "J": 1.0,
    "joule": 1.0,
    "kJ": 1000.0,
    "kilojoule": 1000.0,
    "MJ": 1e6,
    "megajoule": 1e6,
    "cal": 4.184,
    "calorie": 4.184,
    "kcal": 4184.0,
    "kilocalorie": 4184.0,
}


def parse_value_with_unit(value_str: str) -> Tuple[float, Optional[str]]:
    """
    Parse a string containing a value and optional unit
    
    Args:
        value_str: String like "100", "100.5 mm", "25 C", etc.
        
    Returns:
        Tuple of (value, unit) where unit may be None
    """
    value_str = str(value_str).strip()
    
    # Try to parse as pure number
    try:
        return float(value_str), None
    except ValueError:
        pass
    
    # Split into value and unit parts
    parts = value_str.split(maxsplit=1)
    if len(parts) != 2:
        raise ValueError(f"Cannot parse value with unit: {value_str}")
    
    try:
        value = float(parts[0])
        unit = parts[1].strip()
        return value, unit
    except ValueError:
        raise ValueError(f"Invalid numeric value in: {value_str}")


def to_SI(value: Union[float, str], unit_type: str) -> float:
    """
    Convert a value to SI units based on the unit type
    
    Args:
        value: Either a float or a string like "100 mm"
        unit_type: Type of unit ("length", "temperature", "pressure", "force", "energy")
        
    Returns:
        Value converted to SI units
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    numeric_value, unit = parse_value_with_unit(value)
    
    if unit is None:
        return numeric_value
    
    # Get appropriate conversion dictionary
    conversion_dict = {
        "length": LENGTH_CONVERSIONS,
        "temperature": TEMPERATURE_CONVERSIONS,
        "pressure": PRESSURE_CONVERSIONS,
        "force": FORCE_CONVERSIONS,
        "energy": ENERGY_CONVERSIONS,
    }.get(unit_type.lower())
    
    if conversion_dict is None:
        raise ValueError(f"Unknown unit type: {unit_type}")
    
    # Handle temperature conversions (functions) differently
    if unit_type.lower() == "temperature":
        converter = conversion_dict.get(unit.lower())
        if converter is None:
            raise ValueError(f"Unknown temperature unit: {unit}")
        return converter(numeric_value)
    
    # Handle other conversions (multiplication factors)
    factor = conversion_dict.get(unit.lower())
    if factor is None:
        raise ValueError(f"Unknown {unit_type} unit: {unit}")
    
    return numeric_value * factor


def convert_length(value: Union[float, str]) -> float:
    """Convert length value to meters"""
    return to_SI(value, "length")


def convert_temperature(value: Union[float, str]) -> float:
    """Convert temperature value to Kelvin"""
    return to_SI(value, "temperature")


def convert_pressure(value: Union[float, str]) -> float:
    """Convert pressure value to Pascal"""
    return to_SI(value, "pressure")


def convert_force(value: Union[float, str]) -> float:
    """Convert force value to Newton"""
    return to_SI(value, "force")


def convert_energy(value: Union[float, str]) -> float:
    """Convert energy value to Joule"""
    return to_SI(value, "energy") 