"""Design optimization using Bayesian and CMA-ES approaches."""

import numpy as np
from scipy.optimize import minimize, differential_evolution
from typing import Dict, Callable, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class DesignOptimizer:
    """Optimize vascular geometry for performance targets."""
    
    def __init__(self, simulation_func: Callable):
        """
        Initialize optimizer.
        
        Args:
            simulation_func: Function that takes parameters and returns (results, warnings)
        """
        self.simulation_func = simulation_func
        self.best_params = None
        self.best_score = float('inf')
        self.history = []
    
    def objective_uniform_delivery(self, params_array: np.ndarray, 
                                   param_names: List[str],
                                   base_params: Dict) -> float:
        """
        Objective function for uniform sugar delivery.
        
        Minimizes variation in concentration and flow rate.
        """
        # Convert array to parameter dict
        params = base_params.copy()
        for i, name in enumerate(param_names):
            params[name] = params_array[i]
        
        try:
            results, warnings = self.simulation_func(params)
            
            # Penalize warnings
            penalty = len(warnings) * 1000
            
            # Calculate uniformity metrics
            concentration = results['concentration_mM']
            flow = results['phloem_flow_nL_s']
            
            # Standard deviation (lower is better)
            conc_std = np.std(concentration)
            flow_std = np.std(flow[flow > 0]) if np.any(flow > 0) else 1000
            
            # Combined score
            score = conc_std + flow_std * 0.1 + penalty
            
            return score
        
        except Exception as e:
            return 1e6  # Large penalty for failed simulations
    
    def objective_max_flow(self, params_array: np.ndarray,
                          param_names: List[str],
                          base_params: Dict) -> float:
        """
        Objective function for maximizing phloem flow rate.
        """
        params = base_params.copy()
        for i, name in enumerate(param_names):
            params[name] = params_array[i]
        
        try:
            results, warnings = self.simulation_func(params)
            
            penalty = len(warnings) * 500
            avg_flow = np.mean(results['phloem_flow_nL_s'])
            
            # Negative because we're minimizing (want max flow)
            score = -avg_flow + penalty
            
            return score
        
        except Exception as e:
            return 1e6
    
    def objective_printability(self, params_array: np.ndarray,
                              param_names: List[str],
                              base_params: Dict,
                              min_feature_mm: float = 0.1) -> float:
        """
        Objective function for 3D printability.
        
        Ensures features are above minimum printable size.
        """
        params = base_params.copy()
        for i, name in enumerate(param_names):
            params[name] = params_array[i]
        
        penalty = 0
        
        # Check vessel diameters
        if 'xylem_vessel_diameter_um' in params:
            if params['xylem_vessel_diameter_um'] / 1000 < min_feature_mm:
                penalty += 1000
        
        if 'phloem_sieve_diameter_um' in params:
            if params['phloem_sieve_diameter_um'] / 1000 < min_feature_mm:
                penalty += 1000
        
        try:
            results, warnings = self.simulation_func(params)
            penalty += len(warnings) * 200
            
            # Prefer moderate flow (not too fast or slow)
            avg_flow = np.mean(results['phloem_flow_nL_s'])
            target_flow = 1e-3  # Target ~0.001 nL/s
            flow_penalty = abs(np.log10(avg_flow + 1e-10) - np.log10(target_flow))
            
            return penalty + flow_penalty * 100
        
        except Exception as e:
            return 1e6
    
    def optimize_scipy(self, objective: str, param_names: List[str],
                      bounds: List[Tuple[float, float]], base_params: Dict,
                      method: str = 'L-BFGS-B', max_iter: int = 50) -> Dict:
        """
        Optimize using scipy.optimize methods.
        
        Args:
            objective: 'uniform_delivery', 'max_flow', or 'printability'
            param_names: List of parameter names to optimize
            bounds: List of (min, max) tuples for each parameter
            base_params: Base parameter dictionary
            method: Optimization method ('L-BFGS-B', 'TNC', etc.)
            max_iter: Maximum iterations
        
        Returns:
            Dictionary with optimized parameters and results
        """
        # Select objective function
        if objective == 'uniform_delivery':
            obj_func = self.objective_uniform_delivery
        elif objective == 'max_flow':
            obj_func = self.objective_max_flow
        elif objective == 'printability':
            obj_func = self.objective_printability
        else:
            raise ValueError(f"Unknown objective: {objective}")
        
        # Initial guess (midpoint of bounds)
        x0 = np.array([(b[0] + b[1]) / 2 for b in bounds])
        
        # Optimize
        result = minimize(
            lambda x: obj_func(x, param_names, base_params),
            x0,
            method=method,
            bounds=bounds,
            options={'maxiter': max_iter}
        )
        
        # Extract optimized parameters
        optimized_params = base_params.copy()
        for i, name in enumerate(param_names):
            optimized_params[name] = result.x[i]
        
        return {
            'success': result.success,
            'parameters': optimized_params,
            'score': result.fun,
            'iterations': result.nit,
            'message': result.message
        }
    
    def optimize_differential_evolution(self, objective: str, param_names: List[str],
                                       bounds: List[Tuple[float, float]], 
                                       base_params: Dict,
                                       max_iter: int = 30, population: int = 10) -> Dict:
        """
        Optimize using differential evolution (global optimizer).
        
        More robust but slower than local methods.
        """
        if objective == 'uniform_delivery':
            obj_func = self.objective_uniform_delivery
        elif objective == 'max_flow':
            obj_func = self.objective_max_flow
        elif objective == 'printability':
            obj_func = self.objective_printability
        else:
            raise ValueError(f"Unknown objective: {objective}")
        
        result = differential_evolution(
            lambda x: obj_func(x, param_names, base_params),
            bounds,
            maxiter=max_iter,
            popsize=population,
            seed=42,
            workers=1
        )
        
        optimized_params = base_params.copy()
        for i, name in enumerate(param_names):
            optimized_params[name] = result.x[i]
        
        return {
            'success': result.success,
            'parameters': optimized_params,
            'score': result.fun,
            'iterations': result.nit,
            'message': result.message
        }
    
    def suggest_improvements(self, current_params: Dict, species_profile: Dict) -> Dict:
        """
        Provide quick heuristic suggestions for parameter improvements.
        
        Args:
            current_params: Current parameter values
            species_profile: Species profile with ranges
        
        Returns:
            Dictionary with suggestions
        """
        suggestions = {
            'changes': [],
            'reasoning': []
        }
        
        # Check xylem vessel diameter
        if 'xylem_vessel_diameter_um' in current_params:
            diameter = current_params['xylem_vessel_diameter_um']
            if diameter < 15:
                suggestions['changes'].append({
                    'parameter': 'xylem_vessel_diameter_um',
                    'current': diameter,
                    'suggested': 20,
                    'change': '+5 to +10 μm'
                })
                suggestions['reasoning'].append(
                    "Increase xylem vessel diameter to improve water transport capacity"
                )
        
        # Check phloem pressure
        if 'phloem_pressure_kPa' in current_params:
            pressure = current_params['phloem_pressure_kPa']
            if pressure < 600:
                suggestions['changes'].append({
                    'parameter': 'phloem_pressure_kPa',
                    'current': pressure,
                    'suggested': 800,
                    'change': '+200 kPa'
                })
                suggestions['reasoning'].append(
                    "Increase phloem pressure to enhance sugar transport"
                )
            elif pressure > 1500:
                suggestions['changes'].append({
                    'parameter': 'phloem_pressure_kPa',
                    'current': pressure,
                    'suggested': 1200,
                    'change': '-300 kPa'
                })
                suggestions['reasoning'].append(
                    "Reduce phloem pressure to prevent membrane stress"
                )
        
        # Check sucrose concentration
        if 'sucrose_concentration_mM' in current_params:
            concentration = current_params['sucrose_concentration_mM']
            if concentration > 800:
                suggestions['changes'].append({
                    'parameter': 'sucrose_concentration_mM',
                    'current': concentration,
                    'suggested': 600,
                    'change': '-200 mM'
                })
                suggestions['reasoning'].append(
                    "Reduce sugar concentration to lower viscosity and improve flow"
                )
            elif concentration < 300:
                suggestions['changes'].append({
                    'parameter': 'sucrose_concentration_mM',
                    'current': concentration,
                    'suggested': 400,
                    'change': '+100 mM'
                })
                suggestions['reasoning'].append(
                    "Increase sugar concentration to boost osmotic driving force"
                )
        
        # Check vessel density
        if 'xylem_vessel_density' in current_params:
            density = current_params['xylem_vessel_density']
            if density < 30:
                suggestions['changes'].append({
                    'parameter': 'xylem_vessel_density',
                    'current': density,
                    'suggested': 50,
                    'change': '+20 vessels/mm²'
                })
                suggestions['reasoning'].append(
                    "Increase vessel density to improve redundancy and total flow capacity"
                )
        
        return suggestions
