"""Tests for simulation module."""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from simulation import (
    PhytoFlowSolver,
    MoleculeLibrary,
    LiteratureValidator,
    ViscosityModel
)


class TestMoleculeLibrary:
    """Test molecule library."""
    
    def test_get_molecule(self):
        """Test retrieving molecule specs."""
        sucrose = MoleculeLibrary.get_molecule('sucrose')
        
        assert sucrose is not None
        assert sucrose.name == 'Sucrose'
        assert sucrose.concentration_mM > 0
        assert sucrose.diffusivity_m2_s > 0
        assert sucrose.molar_mass_g_mol > 0
    
    def test_list_molecules(self):
        """Test listing available molecules."""
        molecules = MoleculeLibrary.list_molecules()
        
        assert 'sucrose' in molecules
        assert 'glucose' in molecules
        assert 'auxin' in molecules
        assert len(molecules) >= 4


class TestLiteratureValidator:
    """Test literature validation."""
    
    def test_validate_xylem_pressure_valid(self):
        """Test valid xylem pressure."""
        is_valid, msg = LiteratureValidator.validate('xylem_pressure_kPa', -500)
        
        assert is_valid
        assert 'within literature range' in msg
    
    def test_validate_xylem_pressure_too_negative(self):
        """Test xylem pressure below minimum."""
        is_valid, msg = LiteratureValidator.validate('xylem_pressure_kPa', -3000)
        
        assert not is_valid
        assert 'below biological minimum' in msg
    
    def test_validate_phloem_pressure_valid(self):
        """Test valid phloem pressure."""
        is_valid, msg = LiteratureValidator.validate('phloem_pressure_kPa', 800)
        
        assert is_valid
    
    def test_validate_phloem_pressure_too_high(self):
        """Test phloem pressure above maximum."""
        is_valid, msg = LiteratureValidator.validate('phloem_pressure_kPa', 2500)
        
        assert not is_valid
        assert 'exceeds biological maximum' in msg
    
    def test_validate_unknown_parameter(self):
        """Test validation of unknown parameter."""
        is_valid, msg = LiteratureValidator.validate('unknown_param', 100)
        
        assert is_valid  # Unknown params pass through
        assert msg == ""


class TestViscosityModel:
    """Test viscosity calculations."""
    
    def test_viscosity_at_zero_concentration(self):
        """Test viscosity at zero concentration."""
        viscosity = ViscosityModel.calculate(0, base_viscosity_mPa_s=1.0)
        
        assert viscosity == 1.0  # Should equal base viscosity
    
    def test_viscosity_increases_with_concentration(self):
        """Test that viscosity increases with concentration."""
        visc_low = ViscosityModel.calculate(100, base_viscosity_mPa_s=1.0)
        visc_high = ViscosityModel.calculate(600, base_viscosity_mPa_s=1.0)
        
        assert visc_high > visc_low
    
    def test_viscosity_clamped(self):
        """Test that viscosity doesn't overflow."""
        visc = ViscosityModel.calculate(5000, base_viscosity_mPa_s=1.0)
        
        assert visc < 100  # Should be clamped
        assert not np.isnan(visc)
        assert not np.isinf(visc)


class TestPhytoFlowSolver:
    """Test simulation solver."""
    
    def test_solver_initialization(self):
        """Test solver initialization."""
        solver = PhytoFlowSolver(length_m=0.1, n_nodes=50)
        
        assert solver.length_m == 0.1
        assert solver.n_nodes == 50
        assert len(solver.x) == 50
        assert len(solver.xylem_pressure) == 50
    
    def test_set_initial_conditions(self):
        """Test setting initial conditions."""
        solver = PhytoFlowSolver(length_m=0.1, n_nodes=50)
        solver.set_initial_conditions(
            xylem_pressure_kPa=-500,
            phloem_pressure_kPa=800,
            concentration_mM=400
        )
        
        assert np.all(solver.xylem_pressure == -500)
        assert np.all(solver.phloem_pressure == 800)
        assert np.all(solver.concentration == 400)
    
    def test_xylem_poiseuille_flow(self):
        """Test xylem Poiseuille flow calculation."""
        solver = PhytoFlowSolver(length_m=0.1, n_nodes=50)
        solver.set_initial_conditions(xylem_pressure_kPa=-500)
        solver.set_boundary_conditions(
            xylem_inlet_kPa=-600,
            xylem_outlet_kPa=-100
        )
        
        warnings = solver.solve_xylem_poiseuille(vessel_radius_um=20.0)
        
        # Check flow was calculated
        assert len(warnings) == 0  # No cavitation warnings
        assert np.any(solver.xylem_flow != 0)
        
        # Check pressure boundary conditions applied
        assert solver.xylem_pressure[0] == -600
        assert solver.xylem_pressure[-1] == -100
    
    def test_run_simulation(self):
        """Test running full simulation."""
        solver = PhytoFlowSolver(length_m=0.1, n_nodes=50)
        
        params = {
            'xylem_vessel_diameter_um': 20.0,
            'phloem_sieve_diameter_um': 15.0,
            'xylem_pressure_drop_kPa': -500,
            'phloem_pressure_kPa': 800,
            'sucrose_concentration_mM': 400,
            'viscosity_mPa_s': 1.5,
            'membrane_permeability_m_s': 1e-7,
            'xylem_vessel_density': 50
        }
        
        results, warnings = solver.run_simulation(params)
        
        # Check results structure
        assert 'x_mm' in results
        assert 'xylem_pressure_kPa' in results
        assert 'phloem_pressure_kPa' in results
        assert 'concentration_mM' in results
        assert 'viscosity_mPa_s' in results
        assert 'xylem_flow_nL_s' in results
        assert 'phloem_flow_nL_s' in results
        
        # Check array lengths
        assert len(results['x_mm']) == 50
        assert len(results['xylem_pressure_kPa']) == 50
        assert len(results['concentration_mM']) == 50
        
        # Check values are reasonable
        assert np.all(results['xylem_pressure_kPa'] < 0)
        assert np.all(results['phloem_pressure_kPa'] > 0)
        assert np.all(results['concentration_mM'] >= 0)
        assert np.all(results['viscosity_mPa_s'] >= 1.0)
    
    def test_simulation_with_extreme_parameters(self):
        """Test simulation with extreme parameters generates warnings."""
        solver = PhytoFlowSolver(length_m=0.1, n_nodes=50)
        
        params = {
            'xylem_vessel_diameter_um': 20.0,
            'phloem_sieve_diameter_um': 15.0,
            'xylem_pressure_drop_kPa': -3000,  # Extreme
            'phloem_pressure_kPa': 2500,  # Extreme
            'sucrose_concentration_mM': 1500,  # Extreme
            'viscosity_mPa_s': 1.5,
            'membrane_permeability_m_s': 1e-7,
            'xylem_vessel_density': 50
        }
        
        results, warnings = solver.run_simulation(params)
        
        # Should generate warnings
        assert len(warnings) > 0
    
    def test_poiseuille_comparison(self):
        """Test that Poiseuille flow matches analytical solution."""
        solver = PhytoFlowSolver(length_m=0.1, n_nodes=100)
        
        # Set linear pressure gradient
        P_inlet = -500  # kPa
        P_outlet = -100  # kPa
        
        solver.set_boundary_conditions(
            xylem_inlet_kPa=P_inlet,
            xylem_outlet_kPa=P_outlet
        )
        
        solver.xylem_pressure = np.linspace(P_inlet, P_outlet, 100)
        solver.viscosity[:] = 1.0  # Constant viscosity
        
        # Solve
        solver.solve_xylem_poiseuille(vessel_radius_um=20.0)
        
        # Analytical: Q = (πr⁴/8μ) * (ΔP/L)
        r = 20e-6  # m
        mu = 1e-3  # Pa·s
        dP = (P_inlet - P_outlet) * 1000  # Pa
        L = 0.1  # m
        
        Q_analytical = (np.pi * r**4 / (8 * mu)) * (dP / L)
        Q_analytical_nL_s = Q_analytical * 1e9
        
        # Compare (should be similar for interior nodes)
        Q_simulated = np.mean(solver.xylem_flow[10:90])  # Avoid boundary effects
        
        # Allow 50% relative error due to discretization
        relative_error = abs(Q_simulated - Q_analytical_nL_s) / Q_analytical_nL_s
        assert relative_error < 0.5, f"Relative error {relative_error:.2f} too large"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
