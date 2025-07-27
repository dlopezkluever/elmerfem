"""
Materials Service for ElmerFEM Educational Platform

This service handles loading, validation, and serving material properties
from the materials database (JSON file).
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class MaterialsService:
    """Service for managing material properties"""
    
    def __init__(self, data_dir: Path = None):
        """
        Initialize the materials service
        
        Args:
            data_dir: Directory containing materials.json and schema files
        """
        if data_dir is None:
            # Default to backend/data directory relative to this file
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
            
        self.materials_file = self.data_dir / "materials.json"
        
        # Cache for loaded materials
        self._materials_cache: Optional[List[Dict]] = None
        
        # Validate on initialization
        self._validate_data_files()
    
    def _validate_data_files(self) -> None:
        """Validate that required data files exist"""
        if not self.materials_file.exists():
            raise FileNotFoundError(f"Materials data file not found: {self.materials_file}")
    
    @lru_cache(maxsize=1)
    def load_materials(self) -> List[Dict]:
        """
        Load materials from JSON file
        
        Returns:
            List of material dictionaries
            
        Raises:
            FileNotFoundError: If materials file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        if self._materials_cache is not None:
            return self._materials_cache
            
        try:
            with open(self.materials_file, 'r') as f:
                data = json.load(f)
            
            # Cache the materials list
            self._materials_cache = data.get("materials", [])
            logger.info(f"Loaded {len(self._materials_cache)} materials from {self.materials_file}")
            
            # Basic validation of required fields
            for material in self._materials_cache:
                required_fields = ["id", "name", "E", "nu", "k", "rho"]
                for field in required_fields:
                    if field not in material:
                        raise ValueError(f"Material {material.get('name', 'unknown')} missing required field: {field}")
            
            return self._materials_cache
            
        except FileNotFoundError:
            logger.error(f"Materials file not found: {self.materials_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in materials file: {e}")
            raise
        except ValueError as e:
            logger.error(f"Materials data validation failed: {e}")
            raise
    
    def get_all_materials(self) -> List[Dict]:
        """
        Get all available materials
        
        Returns:
            List of all materials with their properties
        """
        return self.load_materials()
    
    def get_material_by_id(self, material_id: str) -> Optional[Dict]:
        """
        Get a specific material by its ID
        
        Args:
            material_id: The ID of the material to retrieve
            
        Returns:
            Material dictionary if found, None otherwise
        """
        materials = self.load_materials()
        for material in materials:
            if material.get("id") == material_id:
                return material
        return None
    
    def get_material_for_sif(self, material_id: str) -> Optional[Dict]:
        """
        Get material properties formatted for SIF file generation
        
        Args:
            material_id: The ID of the material
            
        Returns:
            Dictionary with SIF-formatted material properties
        """
        material = self.get_material_by_id(material_id)
        if not material:
            return None
            
        # Format properties for SIF file
        # Note: We keep the same property names as Elmer expects
        return {
            "Name": f'"{material["name"]}"',
            "Youngs Modulus": material["E"],
            "Poisson Ratio": material["nu"],
            "Density": material["rho"],
            "Heat Conductivity": material["k"]
        }
    
    def reload_materials(self) -> None:
        """
        Force reload of materials data from file
        Useful for development when materials.json is updated
        """
        self._materials_cache = None
        self.load_materials.cache_clear()
        logger.info("Materials cache cleared, will reload on next access")


# Create a singleton instance
materials_service = MaterialsService() 