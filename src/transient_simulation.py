"""Time-dependent transient transport simulation with multi-molecular support."""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import pandas as pd


@dataclass
class CustomMolecule:
    """User-defined molecule with full properties."""
    name: str
    molecular_weight_g_mol: float
    concentration_mM: float
    diffusivity_m2_s: float
    solubility_mM: float = 10000.0
    charge: int = 0
    hydrophobic: bool = False
    phase_separation_tendency: float = 0.0  # 0-1, higher = more likely to phase separate
    interaction_coefficients: Dict[str, float] = None  # Interaction with other molecules
    color_hex: str = "#808080"  # For visualization
    
    def __post_init__(self):
        if self.interaction_coefficients is None:
            self.interaction_coefficients = {}


class EnhancedMoleculeLibrary:
    """Extended molecule library with more species and cellular details."""
    
    # Sugars
    SUCROSE = CustomMolecule("Sucrose", 342.3, 400.0, 5.2e-10, 10000, 0, False, 0.0, {}, "#4caf50")
    GLUCOSE = CustomMolecule("Glucose", 180.2, 100.0, 6.7e-10, 15000, 0, False, 0.0, {}, "#66bb6a")
    FRUCTOSE = CustomMolecule("Fructose", 180.2, 50.0, 6.5e-10, 15000, 0, False, 0.0, {}, "#81c784")
    
    # Amino Acids
    GLUTAMINE = CustomMolecule("Glutamine", 146.1, 30.0, 7.6e-10, 5000, 0, False, 0.0, {}, "#ff9800")
    ASPARAGINE = CustomMolecule("Asparagine", 132.1, 20.0, 8.0e-10, 4000, 0, False, 0.0, {}, "#ffb74d")
    ALANINE = CustomMolecule("Alanine", 89.1, 15.0, 9.1e-10, 8000, 0, False, 0.0, {}, "#ffcc80")
    
    # Hormones
    AUXIN = CustomMolecule("Auxin (IAA)", 175.2, 0.01, 8.5e-10, 1.0, 0, True, 0.3, {}, "#e91e63")
    CYTOKININ = CustomMolecule("Cytokinin", 215.2, 0.005, 7.8e-10, 0.5, 1, False, 0.2, {}, "#f06292")
    GIBBERELLIN = CustomMolecule("Gibberellin", 346.4, 0.002, 6.5e-10, 0.2, 0, True, 0.4, {}, "#f48fb1")
    ABSCISIC_ACID = CustomMolecule("Abscisic Acid", 264.3, 0.01, 7.2e-10, 1.0, 0, True, 0.3, {}, "#ec407a")
    
    # Ions
    POTASSIUM = CustomMolecule("K+", 39.1, 100.0, 2.0e-9, 50000, 1, False, 0.0, {}, "#2196f3")
    SODIUM = CustomMolecule("Na+", 23.0, 20.0, 1.3e-9, 50000, 1, False, 0.0, {}, "#42a5f5")
    CALCIUM = CustomMolecule("Ca2+", 40.1, 10.0, 7.9e-10, 10000, 2, False, 0.0, {}, "#64b5f6")
    CHLORIDE = CustomMolecule("Cl-", 35.5, 50.0, 2.0e-9, 50000, -1, False, 0.0, {}, "#90caf9")
    
    # Tracers
    FLUORESCEIN = CustomMolecule("Fluorescein", 376.3, 1.0, 4.3e-10, 100, -1, False, 0.0, {}, "#ffeb3b")
    
    @classmethod
    def get_all_molecules(cls) -> Dict[str, CustomMolecule]:
        """Get dictionary of all predefined molecules."""
        return {
            'sucrose': cls.SUCROSE,
            'glucose': cls.GLUCOSE,
            'fructose': cls.FRUCTOSE,
            'glutamine': cls.GLUTAMINE,
            'asparagine': cls.ASPARAGINE,
            'alanine': cls.ALANINE,
            'auxin': cls.AUXIN,
            'cytokinin': cls.CYTOKININ,
            'gibberellin': cls.GIBBERELLIN,
            'abscisic_acid': cls.ABSCISIC_ACID,
            'potassium': cls.POTASSIUM,
            'sodium': cls.SODIUM,
            'calcium': cls.CALCIUM,
            'chloride': cls.CHLORIDE,
            'fluorescein': cls.FLUORESCEIN,
        }
    
    @classmethod
    def create_user_molecule(cls, name: str, molecular_weight: float,
                            concentration: float, diffusivity: float = 1e-9,
                            charge: int = 0, hydrophobic: bool = False) -> CustomMolecule:
        """Create a user-defined molecule."""
        return CustomMolecule(
            name=name,
            molecular_weight_g_mol=molecular_weight,
            concentration_mM=concentration,
            diffusivity_m2_s=diffusivity,
            charge=charge,
            hydrophobic=hydrophobic,
            color_hex="#808080"
        )


class TimeDependent Solver:
    """
    Time-dependent transient simulation for multi-molecular transport.
    
    Solves coupled advection-diffusion-reaction for multiple species over time.
    """
    
    def __init__(self, length_m: float = 0.1, n_nodes: int = 50, n_timesteps: int = 100):
        """
        Initialize time-dependent solver.
        
        Args:
            length_m: Length of stem segment
            n_nodes: Spatial discretization
            n_timesteps: Number of time steps to simulate
        """
        self.length_m = length_m
        self.n_nodes = n_nodes
        self.n_timesteps = n_timesteps
        self.dx = length_m / (n_nodes - 1)
        self.x = np.linspace(0, length_m, n_nodes)
        
        # State variables (will be 2D: [time, space])
        self.molecules: Dict[str, CustomMolecule] = {}
        self.concentrations: Dict[str, np.ndarray] = {}
        self.velocity_profile = np.zeros(n_nodes)
        
        # Time tracking
        self.time_array = None
        self.current_timestep = 0
    
    def add_molecule(self, molecule: CustomMolecule, initial_concentration: np.ndarray = None):
        """
        Add a molecule to the simulation.
        
        Args:
            molecule: CustomMolecule instance
            initial_concentration: Initial spatial distribution (if None, uses molecule default)
        """
        self.molecules[molecule.name] = molecule
        
        if initial_concentration is None:
            # Default: uniform at molecule's default concentration
            initial_concentration = np.ones(self.n_nodes) * molecule.concentration_mM
        
        # Storage: [timestep, spatial_position]
        self.concentrations[molecule.name] = np.zeros((self.n_timesteps, self.n_nodes))
        self.concentrations[molecule.name][0, :] = initial_concentration
    
    def set_velocity_profile(self, velocity_m_s: float = 1e-3):
        """
        Set velocity profile (simplified as uniform for now).
        
        Args:
            velocity_m_s: Flow velocity in m/s
        """
        self.velocity_profile[:] = velocity_m_s
    
    def solve_transient(self, total_time_s: float = 60.0, method: str = 'explicit') -> Dict:
        """
        Solve time-dependent advection-diffusion for all molecules.
        
        ∂C/∂t + v·∇C = D∇²C + R
        
        Args:
            total_time_s: Total simulation time in seconds
            method: 'explicit' (Euler) or 'implicit' (Crank-Nicolson)
        
        Returns:
            Dictionary with time series data
        """
        dt = total_time_s / (self.n_timesteps - 1)
        self.time_array = np.linspace(0, total_time_s, self.n_timesteps)
        
        # Stability check for explicit method (CFL condition)
        if method == 'explicit':
            max_D = max(m.diffusivity_m2_s for m in self.molecules.values())
            max_v = np.max(np.abs(self.velocity_profile))
            
            dt_stable_diff = 0.5 * self.dx**2 / max_D
            dt_stable_adv = 0.5 * self.dx / max_v if max_v > 0 else np.inf
            dt_stable = min(dt_stable_diff, dt_stable_adv)
            
            if dt > dt_stable:
                print(f"⚠️ Warning: dt={dt:.2e} s may be unstable. Suggested max: {dt_stable:.2e} s")
        
        # Time stepping
        for t in range(1, self.n_timesteps):
            for mol_name, molecule in self.molecules.items():
                C_old = self.concentrations[mol_name][t-1, :]
                C_new = np.zeros(self.n_nodes)
                
                if method == 'explicit':
                    C_new = self._explicit_step(C_old, molecule.diffusivity_m2_s, dt)
                elif method == 'implicit':
                    C_new = self._implicit_step(C_old, molecule.diffusivity_m2_s, dt)
                else:
                    raise ValueError(f"Unknown method: {method}")
                
                # Apply molecular interactions (simplified)
                C_new = self._apply_interactions(mol_name, C_new, t)
                
                # Store
                self.concentrations[mol_name][t, :] = np.clip(C_new, 0, molecule.solubility_mM)
        
        return self._package_results()
    
    def _explicit_step(self, C_old: np.ndarray, D: float, dt: float) -> np.ndarray:
        """Explicit Euler advection-diffusion step."""
        C_new = C_old.copy()
        v = self.velocity_profile
        
        for i in range(1, self.n_nodes - 1):
            # Advection (upwind scheme)
            if v[i] > 0:
                dC_dx = (C_old[i] - C_old[i-1]) / self.dx
            else:
                dC_dx = (C_old[i+1] - C_old[i]) / self.dx
            advection = -v[i] * dC_dx
            
            # Diffusion (central difference)
            d2C_dx2 = (C_old[i-1] - 2*C_old[i] + C_old[i+1]) / self.dx**2
            diffusion = D * d2C_dx2
            
            # Update
            C_new[i] = C_old[i] + dt * (advection + diffusion)
        
        # Boundary conditions (Dirichlet for now)
        # C_new[0] and C_new[-1] remain from C_old
        
        return C_new
    
    def _implicit_step(self, C_old: np.ndarray, D: float, dt: float) -> np.ndarray:
        """Implicit (Crank-Nicolson) step - simplified version."""
        # For simplicity, use explicit for now
        # Full implicit would require solving linear system
        return self._explicit_step(C_old, D, dt)
    
    def _apply_interactions(self, mol_name: str, C: np.ndarray, timestep: int) -> np.ndarray:
        """
        Apply molecular interactions (simplified).
        
        Could include:
        - Co-transport
        - Competitive inhibition
        - Phase separation
        - Enzymatic reactions
        """
        molecule = self.molecules[mol_name]
        
        # Example: Simple interaction with other molecules
        for other_name, coeff in molecule.interaction_coefficients.items():
            if other_name in self.concentrations:
                C_other = self.concentrations[other_name][timestep, :]
                # Interaction effect (simplified)
                C += coeff * C_other * 0.01  # Small coupling
        
        return C
    
    def _package_results(self) -> Dict:
        """Package results for export/visualization."""
        results = {
            'time_s': self.time_array,
            'x_mm': self.x * 1000,
            'molecules': {}
        }
        
        for mol_name in self.molecules:
            results['molecules'][mol_name] = {
                'concentration_time_series': self.concentrations[mol_name],
                'color': self.molecules[mol_name].color_hex,
                'final_concentration': self.concentrations[mol_name][-1, :]
            }
        
        return results
    
    def export_animation_frames(self, output_dir: str = 'frames', fps: int = 10):
        """
        Export animation frames for time-lapse visualization.
        
        Args:
            output_dir: Directory to save frames
            fps: Frames per second for animation
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Sample frames at target FPS
        frame_indices = np.linspace(0, self.n_timesteps-1, 
                                   min(self.n_timesteps, int(self.time_array[-1] * fps)),
                                   dtype=int)
        
        frames_data = []
        for idx in frame_indices:
            frame = {
                'time_s': self.time_array[idx],
                'molecules': {}
            }
            for mol_name in self.molecules:
                frame['molecules'][mol_name] = self.concentrations[mol_name][idx, :]
            frames_data.append(frame)
        
        return frames_data


class ExperimentalProtocol:
    """Generate experimental validation protocols for 3D printed models."""
    
    @staticmethod
    def map_simulation_to_experiment(simulation_params: Dict, 
                                    print_scale: float = 1.0) -> Dict:
        """
        Map simulation parameters to experimental conditions.
        
        Args:
            simulation_params: Simulation parameter dictionary
            print_scale: Scale factor for 3D printing (1.0 = 1:1)
        
        Returns:
            Experimental protocol dictionary
        """
        protocol = {
            'title': 'Experimental Validation Protocol for PhytoFlow Model',
            'print_specifications': {},
            'fluid_conditions': {},
            'measurement_protocol': {},
            'expected_results': {}
        }
        
        # Print specifications
        xylem_diam = simulation_params.get('xylem_vessel_diameter_um', 20) * print_scale
        phloem_diam = simulation_params.get('phloem_sieve_diameter_um', 15) * print_scale
        
        protocol['print_specifications'] = {
            'scale': print_scale,
            'xylem_channel_diameter_um': xylem_diam,
            'phloem_channel_diameter_um': phloem_diam,
            'material': 'Clear resin (SLA) or PDMS (soft lithography)',
            'min_feature_check': xylem_diam >= 100,  # Typical SLA limit ~100 μm
            'recommended_printer': 'Formlabs Form 3+ or Anycubic Photon' if xylem_diam >= 100 else 'Nanoscribe (for sub-100 μm)'
        }
        
        # Fluid conditions
        xylem_pressure = simulation_params.get('xylem_pressure_drop_kPa', -500)
        phloem_pressure = simulation_params.get('phloem_pressure_kPa', 800)
        sucrose_conc = simulation_params.get('sucrose_concentration_mM', 400)
        
        # Convert pressures to experimental setup (height, pump settings)
        # 1 kPa ≈ 10.2 cm water column
        xylem_height_cm = abs(xylem_pressure) * 10.2 / 100  # Negative pressure → vacuum/suction
        phloem_height_cm = phloem_pressure * 10.2 / 100
        
        protocol['fluid_conditions'] = {
            'xylem_inlet_pressure_kPa': xylem_pressure,
            'xylem_vacuum_setup': f'Apply suction: {xylem_height_cm:.1f} cm H2O equivalent or syringe pump at calculated flow rate',
            'phloem_inlet_pressure_kPa': phloem_pressure,
            'phloem_pressure_setup': f'Elevate reservoir {phloem_height_cm:.1f} cm or use syringe pump',
            'sucrose_solution': f'{sucrose_conc} mM ({sucrose_conc * 0.342:.1f} g/L) in water',
            'temperature_C': 25,
            'buffer': 'Optional: 10 mM phosphate buffer pH 7.0'
        }
        
        # Measurement protocol
        protocol['measurement_protocol'] = {
            'flow_rate_measurement': [
                '1. Collect outflow over 1 minute',
                '2. Weigh collected fluid (assume density ≈ 1 g/mL)',
                '3. Calculate flow rate in μL/min',
                '4. Compare to simulation prediction'
            ],
            'concentration_measurement': [
                '1. Sample outflow at inlet, middle, and outlet',
                '2. Measure sucrose concentration via refractometer or HPLC',
                '3. Plot concentration profile',
                '4. Compare to simulation'
            ],
            'visualization': [
                '1. Add fluorescent tracer (fluorescein, 1 μM)',
                '2. Image flow using fluorescence microscopy',
                '3. Track tracer velocity',
                '4. Measure residence time distribution'
            ],
            'pressure_monitoring': [
                '1. Install pressure sensors at inlet and outlet (if available)',
                '2. Monitor pressure drop across model',
                '3. Compare to theoretical Poiseuille calculation'
            ]
        }
        
        # Expected results (from simulation)
        protocol['expected_results'] = {
            'xylem_flow_rate_uL_min': 'Calculate from simulation',
            'phloem_flow_rate_uL_min': 'Calculate from simulation',
            'concentration_gradient': 'Should match simulation profile',
            'residence_time_s': 'Estimate from length/velocity',
            'pressure_drop_Pa': abs(xylem_pressure) * 1000
        }
        
        return protocol
    
    @staticmethod
    def suggest_validation_experiments(model_type: str = 'basic') -> List[Dict]:
        """
        Suggest experiments for different validation levels.
        
        Args:
            model_type: 'basic', 'intermediate', or 'advanced'
        
        Returns:
            List of experiment suggestions
        """
        experiments = []
        
        if model_type == 'basic':
            experiments.extend([
                {
                    'name': 'Flow Rate Validation',
                    'goal': 'Verify Poiseuille flow matches theory',
                    'difficulty': 'Easy',
                    'equipment': ['Syringe pump', 'Scale', 'Timer'],
                    'duration': '30 minutes',
                    'protocol': 'Apply known pressure, measure flow rate, compare to Hagen-Poiseuille prediction'
                },
                {
                    'name': 'Tracer Visualization',
                    'goal': 'Visualize flow paths',
                    'difficulty': 'Easy',
                    'equipment': ['Food dye or fluorescein', 'Camera'],
                    'duration': '15 minutes',
                    'protocol': 'Inject dye, photograph time series, measure front velocity'
                }
            ])
        
        if model_type in ['intermediate', 'advanced']:
            experiments.extend([
                {
                    'name': 'Concentration Gradient Measurement',
                    'goal': 'Validate diffusion and advection balance',
                    'difficulty': 'Moderate',
                    'equipment': ['Refractometer or HPLC', 'Sampling syringes'],
                    'duration': '2 hours',
                    'protocol': 'Establish steady-state flow, sample at multiple points, measure concentration'
                },
                {
                    'name': 'Membrane Coupling Test',
                    'goal': 'Test selective permeability',
                    'difficulty': 'Moderate',
                    'equipment': ['Semi-permeable membrane (dialysis tubing)', 'Concentration sensors'],
                    'duration': '3 hours',
                    'protocol': 'Insert membrane between xylem/phloem channels, measure osmotic coupling'
                }
            ])
        
        if model_type == 'advanced':
            experiments.extend([
                {
                    'name': 'Multi-Molecular Competition',
                    'goal': 'Test co-transport and interference',
                    'difficulty': 'Hard',
                    'equipment': ['HPLC or LC-MS', 'Multiple molecular species'],
                    'duration': '1 day',
                    'protocol': 'Flow mixture of sucrose + amino acids, measure transport rates, compare to single-species baseline'
                },
                {
                    'name': 'Digital Twin Parameter Fitting',
                    'goal': 'Fit simulation parameters to match experimental data',
                    'difficulty': 'Hard',
                    'equipment': ['All above equipment', 'Optimization software'],
                    'duration': '1 week',
                    'protocol': 'Run multiple experiments, use inverse modeling to find best-fit parameters, validate with new experiments'
                }
            ])
        
        return experiments
