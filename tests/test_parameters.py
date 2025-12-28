"""Tests for parameter validation and guardrails."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parameters import ParameterValidator, MoleculeManager


class TestParameterValidator:
    """Test parameter validation."""
    
    def test_validator_initialization(self):
        """Test loading species profiles."""
        validator = ParameterValidator("data/species_profiles.json")
        assert len(validator.profiles) > 0
    
    def test_get_species_list(self):
        """Test getting list of species."""
        validator = ParameterValidator("data/species_profiles.json")
        species = validator.get_species_list()
        
        assert 'arabidopsis' in species
        assert 'maize' in species
        assert 'wheat' in species
        assert 'rice' in species
    
    def test_get_species_profile(self):
        """Test retrieving species profile."""
        validator = ParameterValidator("data/species_profiles.json")
        profile = validator.get_species_profile('arabidopsis')
        
        assert 'name' in profile
        assert 'geometry' in profile
        assert 'physiology' in profile
        assert profile['name'] == 'Arabidopsis thaliana'
    
    def test_get_default_parameters(self):
        """Test extracting default parameters."""
        validator = ParameterValidator("data/species_profiles.json")
        params = validator.get_default_parameters('arabidopsis')
        
        assert 'stem_radius_mm' in params
        assert 'xylem_vessel_diameter_um' in params
        assert 'phloem_sieve_diameter_um' in params
        assert 'xylem_pressure_drop_kPa' in params
        assert 'sucrose_concentration_mM' in params
        
        # Check values are reasonable
        assert params['stem_radius_mm'] > 0
        assert params['xylem_pressure_drop_kPa'] < 0
    
    def test_validate_parameter_in_range(self):
        """Test validation for parameter within range."""
        validator = ParameterValidator("data/species_profiles.json")
        is_valid, msg = validator.validate_parameter(
            'arabidopsis',
            'xylem_vessel_diameter_um',
            25.0  # Within 10-40 range
        )
        
        assert is_valid
        assert msg == ""
    
    def test_validate_parameter_below_min(self):
        """Test validation for parameter below minimum."""
        validator = ParameterValidator("data/species_profiles.json")
        is_valid, msg = validator.validate_parameter(
            'arabidopsis',
            'xylem_vessel_diameter_um',
            5.0  # Below min of 10
        )
        
        assert not is_valid
        assert "below literature minimum" in msg
    
    def test_validate_parameter_above_max(self):
        """Test validation for parameter above maximum."""
        validator = ParameterValidator("data/species_profiles.json")
        is_valid, msg = validator.validate_parameter(
            'arabidopsis',
            'xylem_vessel_diameter_um',
            50.0  # Above max of 40
        )
        
        assert not is_valid
        assert "exceeds literature maximum" in msg
    
    def test_validate_all_parameters(self):
        """Test validating multiple parameters."""
        validator = ParameterValidator("data/species_profiles.json")
        
        params = {
            'xylem_vessel_diameter_um': 25.0,  # OK
            'phloem_sieve_diameter_um': 5.0,   # Too low (min 8)
            'sucrose_concentration_mM': 1000.0  # Too high (max 800)
        }
        
        warnings = validator.validate_all_parameters('arabidopsis', params)
        
        assert len(warnings) == 2  # Two out-of-range parameters
    
    def test_check_physical_constraints_cavitation(self):
        """Test cavitation warning."""
        validator = ParameterValidator("data/species_profiles.json")
        
        params = {
            'xylem_pressure_drop_kPa': -3000  # Extreme cavitation risk
        }
        
        warnings = validator.check_physical_constraints(params)
        
        assert len(warnings) > 0
        assert any('Cavitation' in w for w in warnings)
    
    def test_check_physical_constraints_membrane(self):
        """Test membrane integrity warning."""
        validator = ParameterValidator("data/species_profiles.json")
        
        params = {
            'phloem_pressure_kPa': 2500  # Too high
        }
        
        warnings = validator.check_physical_constraints(params)
        
        assert len(warnings) > 0
        assert any('membrane' in w.lower() for w in warnings)


class TestMoleculeManager:
    """Test molecule management."""
    
    def test_initialization(self):
        """Test molecule manager initialization."""
        manager = MoleculeManager()
        
        molecules = manager.get_molecules()
        assert 'sucrose' in molecules
        assert molecules['sucrose']['concentration_mM'] > 0
    
    def test_add_molecule(self):
        """Test adding custom molecule."""
        manager = MoleculeManager()
        manager.add_molecule('custom', concentration_mM=100.0, diffusivity_m2_s=1e-9)
        
        molecules = manager.get_molecules()
        assert 'custom' in molecules
        assert molecules['custom']['concentration_mM'] == 100.0
    
    def test_add_preset(self):
        """Test adding preset molecule."""
        manager = MoleculeManager()
        manager.add_preset('amino_acids')
        
        molecules = manager.get_molecules()
        assert 'amino_acids' in molecules
        assert molecules['amino_acids']['concentration_mM'] == 50.0
    
    def test_remove_molecule(self):
        """Test removing molecule."""
        manager = MoleculeManager()
        manager.add_molecule('temp', concentration_mM=50.0)
        
        molecules = manager.get_molecules()
        assert 'temp' in molecules
        
        manager.remove_molecule('temp')
        molecules = manager.get_molecules()
        assert 'temp' not in molecules
    
    def test_cannot_remove_sucrose(self):
        """Test that sucrose cannot be removed."""
        manager = MoleculeManager()
        manager.remove_molecule('sucrose')
        
        molecules = manager.get_molecules()
        assert 'sucrose' in molecules  # Should still be there
    
    def test_osmotic_potential(self):
        """Test osmotic potential calculation."""
        manager = MoleculeManager()
        
        # Add additional molecules
        manager.add_preset('amino_acids')
        manager.add_preset('potassium')
        
        osmotic_potential = manager.get_total_osmotic_potential()
        
        # Should be positive and reasonable
        assert osmotic_potential > 0
        assert osmotic_potential < 5000  # Reasonable kPa range


def test_species_profile_completeness():
    """Test that all species have complete profiles."""
    validator = ParameterValidator("data/species_profiles.json")
    
    required_geometry = [
        'stem_radius_mm',
        'xylem_vessel_diameter_um',
        'phloem_sieve_diameter_um',
        'xylem_vessel_density',
        'phloem_density',
        'membrane_thickness_nm'
    ]
    
    required_physiology = [
        'xylem_pressure_drop_kPa',
        'phloem_pressure_kPa',
        'phloem_osmotic_kPa',
        'sucrose_concentration_mM',
        'amino_acids_mM',
        'viscosity_mPa_s',
        'membrane_permeability_m_s'
    ]
    
    for species in validator.get_species_list():
        profile = validator.get_species_profile(species)
        
        # Check geometry parameters
        for param in required_geometry:
            assert param in profile['geometry'], f"{species} missing {param}"
            param_info = profile['geometry'][param]
            assert 'default' in param_info
            assert 'min' in param_info
            assert 'max' in param_info
            assert param_info['min'] < param_info['default']
            assert param_info['default'] < param_info['max']
        
        # Check physiology parameters
        for param in required_physiology:
            assert param in profile['physiology'], f"{species} missing {param}"
            param_info = profile['physiology'][param]
            assert 'default' in param_info
            assert 'min' in param_info
            assert 'max' in param_info


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
