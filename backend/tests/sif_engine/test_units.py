"""
Unit tests for SIF Engine unit conversion utilities
"""

import pytest

from app.sif_engine.units import (
    parse_value_with_unit,
    to_SI,
    convert_length,
    convert_temperature,
    convert_pressure,
    convert_force,
    convert_energy
)


class TestParseValueWithUnit:
    """Test value and unit parsing"""
    
    def test_parse_pure_number(self):
        """Test parsing pure numbers without units"""
        assert parse_value_with_unit("100") == (100.0, None)
        assert parse_value_with_unit("100.5") == (100.5, None)
        assert parse_value_with_unit("-25.7") == (-25.7, None)
        assert parse_value_with_unit("1e6") == (1e6, None)
    
    def test_parse_with_unit(self):
        """Test parsing values with units"""
        assert parse_value_with_unit("100 mm") == (100.0, "mm")
        assert parse_value_with_unit("25.5 C") == (25.5, "C")
        assert parse_value_with_unit("1000 kPa") == (1000.0, "kPa")
        assert parse_value_with_unit("50 N") == (50.0, "N")
    
    def test_parse_with_whitespace(self):
        """Test parsing with various whitespace"""
        assert parse_value_with_unit("  100  mm  ") == (100.0, "mm")
        assert parse_value_with_unit("25.5\tC") == (25.5, "C")
    
    def test_parse_invalid_format(self):
        """Test parsing invalid formats"""
        with pytest.raises(ValueError):
            parse_value_with_unit("mm 100")  # Wrong order
        
        with pytest.raises(ValueError):
            parse_value_with_unit("abc")  # Not a number
        
        with pytest.raises(ValueError):
            parse_value_with_unit("100 200 mm")  # Too many parts


class TestLengthConversion:
    """Test length unit conversions"""
    
    def test_metric_conversions(self):
        """Test metric length conversions"""
        assert convert_length(1000) == 1000  # Pure number = meters
        assert convert_length("1000 mm") == 1.0
        assert convert_length("100 cm") == 1.0
        assert convert_length("1 km") == 1000.0
        assert convert_length("1 m") == 1.0
    
    def test_imperial_conversions(self):
        """Test imperial length conversions"""
        assert convert_length("1 in") == pytest.approx(0.0254)
        assert convert_length("1 ft") == pytest.approx(0.3048)
        assert convert_length("1 yd") == pytest.approx(0.9144)
    
    def test_length_aliases(self):
        """Test unit name aliases"""
        assert convert_length("1 meter") == convert_length("1 m")
        assert convert_length("2 inches") == convert_length("2 in")
        assert convert_length("3 feet") == convert_length("3 ft")


class TestTemperatureConversion:
    """Test temperature unit conversions"""
    
    def test_kelvin_conversion(self):
        """Test Kelvin conversions"""
        assert convert_temperature("300 K") == 300.0
        assert convert_temperature("0 K") == 0.0
        assert convert_temperature("300 kelvin") == 300.0
    
    def test_celsius_conversion(self):
        """Test Celsius to Kelvin conversions"""
        assert convert_temperature("0 C") == 273.15
        assert convert_temperature("100 C") == 373.15
        assert convert_temperature("-273.15 C") == 0.0
        assert convert_temperature("25 celsius") == 298.15
    
    def test_fahrenheit_conversion(self):
        """Test Fahrenheit to Kelvin conversions"""
        assert convert_temperature("32 F") == pytest.approx(273.15)
        assert convert_temperature("212 F") == pytest.approx(373.15)
        assert convert_temperature("0 F") == pytest.approx(255.372, abs=0.001)
        assert convert_temperature("70 fahrenheit") == pytest.approx(294.261, abs=0.001)


class TestPressureConversion:
    """Test pressure unit conversions"""
    
    def test_pascal_conversions(self):
        """Test Pascal-based conversions"""
        assert convert_pressure("1000 Pa") == 1000.0
        assert convert_pressure("1 kPa") == 1000.0
        assert convert_pressure("1 MPa") == 1e6
        assert convert_pressure("1 GPa") == 1e9
    
    def test_other_pressure_units(self):
        """Test other pressure unit conversions"""
        assert convert_pressure("1 bar") == 1e5
        assert convert_pressure("1 atm") == 101325.0
        assert convert_pressure("1 psi") == pytest.approx(6894.76)


class TestForceConversion:
    """Test force unit conversions"""
    
    def test_newton_conversions(self):
        """Test Newton-based conversions"""
        assert convert_force("100 N") == 100.0
        assert convert_force("1 kN") == 1000.0
        assert convert_force("1 MN") == 1e6
    
    def test_pound_force_conversion(self):
        """Test pound-force conversions"""
        assert convert_force("1 lbf") == pytest.approx(4.44822)
        assert convert_force("10 pound") == pytest.approx(44.4822)


class TestEnergyConversion:
    """Test energy unit conversions"""
    
    def test_joule_conversions(self):
        """Test Joule-based conversions"""
        assert convert_energy("100 J") == 100.0
        assert convert_energy("1 kJ") == 1000.0
        assert convert_energy("1 MJ") == 1e6
    
    def test_calorie_conversions(self):
        """Test calorie conversions"""
        assert convert_energy("1 cal") == pytest.approx(4.184)
        assert convert_energy("1 kcal") == pytest.approx(4184.0)


class TestGeneralConversion:
    """Test general to_SI function"""
    
    def test_direct_numbers(self):
        """Test that direct numbers are returned as-is"""
        assert to_SI(100, "length") == 100.0
        assert to_SI(273.15, "temperature") == 273.15
        assert to_SI(1e5, "pressure") == 1e5
    
    def test_unknown_unit_type(self):
        """Test error handling for unknown unit types"""
        with pytest.raises(ValueError, match="Unknown unit type"):
            to_SI("100 mm", "unknown_type")
    
    def test_unknown_unit(self):
        """Test error handling for unknown units"""
        with pytest.raises(ValueError, match="Unknown length unit"):
            to_SI("100 parsecs", "length")
        
        with pytest.raises(ValueError, match="Unknown temperature unit"):
            to_SI("100 R", "temperature")  # Rankine not supported 