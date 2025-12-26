"""Parameter validation, guardrails, and species presets for PhytoFlow."""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, List
import numpy as np


class ParameterValidator:
    """Validates parameters against species profiles and provides warnings."""
    
    def __init__(self, profiles_path: str = "data/species_profiles.json"):
        """Load species profiles from JSON."""
        self.profiles_path = Path(profiles_path)
        with open(self.profiles_path, 'r') as f:
            self.profiles = json.load(f)
    
    def get_species_list(self) -> List[str]:
        """Return list of available species."""
        return list(self.profiles.keys())
    
    def get_species_profile(self, species: str) -> Dict[str, Any]:
        """Get full profile for a species."""
        return self.profiles.get(species, {})
    
    def get_default_parameters(self, species: str) -> Dict[str, float]:
        """Extract default parameter values for a species."""
        profile = self.get_species_profile(species)
        params = {}
        
        for category in ['geometry', 'physiology']:
            if category in profile:
                for param_name, param_info in profile[category].items():
                    params[param_name] = param_info['default']
        
        return params
    
    def validate_parameter(self, species: str, param_name: str, value: float) -> Tuple[bool, str]:
        """
        Validate a parameter value against species profile ranges.
        
        Returns:
            (is_valid, warning_message)
        """
        profile = self.get_species_profile(species)
        
        # Search in both geometry and physiology
        for category in ['geometry', 'physiology']:
            if category in profile and param_name in profile[category]:
                param_info = profile[category][param_name]
                min_val = param_info['min']
                max_val = param_info['max']
                default_val = param_info['default']
                unit = param_info.get('unit', '')
                
                if value < min_val:
                    warning = (f"⚠️ {param_name} = {value} {unit} is below literature "
                             f"minimum ({min_val} {unit}) for {species}. "
                             f"Default: {default_val} {unit}")
                    return False, warning
                elif value > max_val:
                    warning = (f"⚠️ {param_name} = {value} {unit} exceeds literature "
                             f"maximum ({max_val} {unit}) for {species}. "
                             f"Default: {default_val} {unit}")
                    return False, warning
                else:
                    return True, ""
        
        # Parameter not found in profile
        return True, f"ℹ️ Parameter {param_name} not found in {species} profile."
    
    def validate_all_parameters(self, species: str, params: Dict[str, float]) -> List[str]:
        """Validate all parameters and return list of warnings."""
        warnings = []
        
        for param_name, value in params.items():
            is_valid, warning = self.validate_parameter(species, param_name, value)
            if not is_valid and warning:
                warnings.append(warning)
        
        return warnings
    
    def check_physical_constraints(self, params: Dict[str, float]) -> List[str]:
        """Check for physically impossible states."""
        warnings = []
        
        # Cavitation check (xylem pressure too negative)
        if 'xylem_pressure_drop_kPa' in params:
            if params['xylem_pressure_drop_kPa'] < -2500:
                warnings.append("🚨 Cavitation risk: xylem pressure extremely negative!")
        
        # Membrane integrity
        if 'phloem_pressure_kPa' in params:
            if params['phloem_pressure_kPa'] > 2000:
                warnings.append("🚨 Phloem pressure may exceed membrane integrity limits!")
        
        # Reynolds number check (should be low for laminar flow)
        if all(k in params for k in ['xylem_vessel_diameter_um', 'viscosity_mPa_s']):
            diameter_m = params['xylem_vessel_diameter_um'] * 1e-6
            viscosity = params['viscosity_mPa_s'] * 1e-3
            # Assume typical velocity ~1 mm/s
            velocity = 1e-3
            Re = (1000 * velocity * diameter_m) / viscosity  # density ~1000 kg/m³
            if Re > 2300:
                warnings.append(f"⚠️ Reynolds number ({Re:.0f}) suggests turbulent flow. "
                              f"Laminar assumption may not hold.")
        
        return warnings


class MoleculeManager:
    """Manage solute molecules in the phloem."""
    
    def __init__(self):
        """Initialize with default molecules."""
        self.molecules = {
            'sucrose': {
                'concentration_mM': 400,
                'diffusivity_m2_s': 5e-10,
                'molar_mass_g_mol': 342.3
            }
        }
        
        # Preset molecules that can be added
        self.presets = {
            'amino_acids': {
                'concentration_mM': 50,
                'diffusivity_m2_s': 8e-10,
                'molar_mass_g_mol': 150.0
            },
            'potassium': {
                'concentration_mM': 100,
                'diffusivity_m2_s': 2e-9,
                'molar_mass_g_mol': 39.1
            },
            'hormones': {
                'concentration_mM': 0.01,
                'diffusivity_m2_s': 6e-10,
                'molar_mass_g_mol': 300.0
            }
        }
    
    def add_molecule(self, name: str, concentration_mM: float, 
                    diffusivity_m2_s: float = 1e-9, molar_mass_g_mol: float = 100.0):
        """Add a custom molecule."""
        self.molecules[name] = {
            'concentration_mM': concentration_mM,
            'diffusivity_m2_s': diffusivity_m2_s,
            'molar_mass_g_mol': molar_mass_g_mol
        }
    
    def add_preset(self, name: str):
        """Add a preset molecule."""
        if name in self.presets:
            self.molecules[name] = self.presets[name].copy()
    
    def remove_molecule(self, name: str):
        """Remove a molecule."""
        if name in self.molecules and name != 'sucrose':  # Keep sucrose as default
            del self.molecules[name]
    
    def get_molecules(self) -> Dict[str, Dict[str, float]]:
        """Get all current molecules."""
        return self.molecules.copy()
    
    def get_total_osmotic_potential(self) -> float:
        """Calculate total osmotic potential (simplified van't Hoff)."""
        # π = iCRT, where i≈1 for non-ionizing solutes, R=8.314 J/(mol·K), T≈298K
        RT = 8.314 * 298 / 1000  # kPa·L/mol
        total_concentration = sum(m['concentration_mM'] for m in self.molecules.values())
        return total_concentration * RT  # Approximate, assumes i=1
