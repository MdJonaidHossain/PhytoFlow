"""Plain-language explanations of biological concepts and results."""

from typing import Dict


class BiologicalExplainer:
    """Provides plain-language explanations with biological context."""
    
    @staticmethod
    def explain_xylem() -> str:
        """Explain xylem function."""
        return """
**Xylem: The Water Highway**

Xylem vessels transport water and minerals from roots to leaves. They work under **negative pressure** (tension), 
pulling water up like a straw. This tension is created by evaporation from leaves (transpiration).

- **Negative pressure** (e.g., -500 kPa) is normal and healthy
- **Very negative** (< -2000 kPa) risks **cavitation** (air bubbles that block flow)
- Larger vessels transport more water but are more prone to cavitation
        """
    
    @staticmethod
    def explain_phloem() -> str:
        """Explain phloem function."""
        return """
**Phloem: The Sugar Transport System**

Phloem sieve tubes transport sugars and nutrients from leaves (source) to growing regions (sink). 
They use the **Münch pressure-flow mechanism**:

1. High sugar concentration at source creates high osmotic pressure
2. Water flows in from xylem, building positive pressure
3. Pressure gradient drives bulk flow to sink
4. Sugar is unloaded, water returns to xylem

- **Positive pressure** (500-1500 kPa) is typical
- High sugar concentration increases sap viscosity, slowing flow
        """
    
    @staticmethod
    def explain_munch_mechanism() -> str:
        """Explain Münch pressure-flow hypothesis."""
        return """
**Münch Pressure-Flow Hypothesis**

Named after Ernst Münch (1930), this explains how phloem transports sugar without pumps:

1. **Loading Zone** (leaves): Photosynthesis produces sugar → high concentration → water enters → pressure builds
2. **Pressure Gradient**: High pressure at source, low at sink
3. **Bulk Flow**: Like squeezing a water balloon, pressure pushes sap through sieve tubes
4. **Unloading Zone** (roots/fruits): Sugar removed → concentration drops → water exits → pressure drops

**Key insight**: It's a passive physical process driven by osmosis, not active pumping!
        """
    
    @staticmethod
    def explain_cavitation() -> str:
        """Explain cavitation in xylem."""
        return """
**Cavitation: The Xylem's Enemy**

When xylem tension becomes too negative (< -2000 kPa in most plants):
- Dissolved gases can form bubbles (embolism)
- Bubbles block water transport in that vessel
- Plant must rely on remaining functional vessels

**Cavitation resistance varies**:
- Small vessels resist cavitation better (stronger walls)
- Large vessels transport more water but cavitate easier
- Plants make trade-offs between efficiency and safety

**Recovery**: Some plants can refill embolized vessels, others cannot.
        """
    
    @staticmethod
    def explain_viscosity() -> str:
        """Explain concentration-dependent viscosity."""
        return """
**Viscosity: How Thickness Affects Flow**

Sugar-rich phloem sap is thicker (more viscous) than water:
- **Water**: 1.0 mPa·s
- **10% sucrose**: ~1.3 mPa·s
- **30% sucrose**: ~3.5 mPa·s (like honey!)

**Why it matters**:
- High viscosity increases flow resistance
- More pressure needed to move same volume
- Trade-off: concentrated sap is harder to transport but carries more energy

Plants balance sugar concentration for efficient energy delivery.
        """
    
    @staticmethod
    def explain_parameter(param_name: str) -> str:
        """
        Provide explanation for specific parameter.
        
        Args:
            param_name: Parameter name
        
        Returns:
            Explanation string
        """
        explanations = {
            'stem_radius_mm': """
**Stem Radius**: Overall size of the stem cross-section. Larger stems can accommodate more vascular bundles 
and support larger plants. Typical range: 0.3-8 mm depending on species.
            """,
            
            'xylem_vessel_diameter_um': """
**Xylem Vessel Diameter**: Width of individual water-conducting cells. Larger vessels transport water faster 
but are more vulnerable to cavitation. Trade-off between efficiency and safety.
- Small (10-30 μm): Safe but slow (herbs, drought-adapted)
- Large (50-150 μm): Fast but risky (grasses, wet environments)
            """,
            
            'phloem_sieve_diameter_um': """
**Phloem Sieve Element Diameter**: Width of sugar-conducting cells. Affects flow resistance and capacity.
Typical range: 8-40 μm. Larger elements transport more but are harder to maintain.
            """,
            
            'xylem_vessel_density': """
**Vessel Density**: Number of xylem vessels per square millimeter. More vessels = more transport capacity 
but less mechanical strength. Plants balance transport needs with structural support.
            """,
            
            'phloem_density': """
**Phloem Density**: Number of phloem sieve elements per square millimeter. Higher density supports more 
sugar transport but requires more resources to maintain.
            """,
            
            'xylem_pressure_drop_kPa': """
**Xylem Pressure**: Negative pressure (tension) that pulls water upward. Created by leaf transpiration.
- Mild (-100 to -500 kPa): Typical for well-watered plants
- Moderate (-500 to -1500 kPa): Common during day or mild drought
- Severe (< -2000 kPa): Cavitation risk increases
            """,
            
            'phloem_pressure_kPa': """
**Phloem Pressure**: Positive pressure driving sugar flow from source to sink. Generated by osmosis.
- Low (400-600 kPa): Slower transport, may limit growth
- Moderate (800-1200 kPa): Typical healthy range
- High (> 1500 kPa): May stress cell membranes
            """,
            
            'sucrose_concentration_mM': """
**Sucrose Concentration**: Amount of sugar in phloem sap. Higher concentration = more energy transported 
but also higher viscosity (flow resistance).
- Low (200-400 mM): ~7-14% solution, low viscosity
- Medium (400-600 mM): ~14-20% solution, balanced
- High (600-1000 mM): ~20-35% solution, thick like syrup
            """,
            
            'viscosity_mPa_s': """
**Viscosity**: Measure of fluid thickness/resistance to flow. Water ≈ 1.0 mPa·s. Increases exponentially 
with sugar concentration. Higher viscosity requires more pressure to maintain flow.
            """,
            
            'membrane_permeability_m_s': """
**Membrane Permeability**: How easily water crosses cell membranes between xylem and phloem. Higher 
permeability allows faster osmotic coupling but may reduce pressure buildup. Regulated by aquaporin proteins.
            """,
        }
        
        return explanations.get(param_name, f"No explanation available for {param_name}")
    
    @staticmethod
    def explain_species(species: str) -> str:
        """
        Provide biological context for species.
        
        Args:
            species: Species identifier
        
        Returns:
            Species explanation
        """
        explanations = {
            'arabidopsis': """
**Arabidopsis thaliana** - The Lab Workhorse

A small flowering plant (mustard family) widely used in research:
- **Size**: Tiny (~30 cm), fast-growing (6-week life cycle)
- **Vascular**: Simple dicot ring arrangement, small vessels
- **Strategy**: R-selected (many seeds, rapid growth)
- **Research**: First plant with sequenced genome, genetic model

**Xylem/Phloem**: Small, safe vessels optimized for rapid growth in stable environments.
            """,
            
            'maize': """
**Zea mays (Maize/Corn)** - The Agricultural Giant

Major crop (monocot) with specialized C4 photosynthesis:
- **Size**: Large (2-3 m), thick stems, efficient water use
- **Vascular**: Scattered monocot bundles, large vessels for high transpiration
- **Strategy**: High biomass production, optimized for full sun
- **Agriculture**: Feed 4 billion+ people; drought research focus

**Xylem/Phloem**: Large vessels support high water demand for C4 photosynthesis.
            """,
            
            'wheat': """
**Triticum aestivum (Wheat)** - The Global Staple

Most widely grown food crop (monocot, C3 grass):
- **Size**: Medium (0.6-1.5 m), hollow stems
- **Vascular**: Scattered bundles, moderate vessels
- **Strategy**: Grain production, temperate adapted
- **Agriculture**: Feeds ~35% of humanity; breeding for drought tolerance

**Xylem/Phloem**: Moderate-sized vessels balance water transport with cavitation safety.
            """,
            
            'rice': """
**Oryza sativa (Rice)** - The Wetland Specialist

Staple crop grown in flooded paddies (monocot, C3):
- **Size**: Medium (0.5-1.8 m), adapted to waterlogged soil
- **Vascular**: Scattered bundles, aerenchyma (air channels)
- **Strategy**: Anaerobic tolerance, high water availability
- **Agriculture**: Feeds ~half of humanity; mostly Asian consumption

**Xylem/Phloem**: Smaller vessels reflect low water stress; aerenchyma provides oxygen to roots.
            """,
        }
        
        return explanations.get(species, f"No explanation available for {species}")
    
    @staticmethod
    def get_tutorial_text() -> str:
        """Return full tutorial/help text."""
        return """
# PhytoFlow Tutorial

## Quick Start

1. **Choose a Species**: Select from Arabidopsis, Maize, Wheat, or Rice. Each has literature-backed defaults.

2. **Set Complexity**: 
   - **Beginner**: Simple controls, auto-validation
   - **Advanced**: Full parameter control, expert mode

3. **Adjust Parameters**:
   - **Geometry**: Stem size, vessel diameters, density
   - **Physiology**: Pressures, concentrations, viscosity

4. **Generate Model**: Creates cross-section visualization

5. **Run Simulation**: Solves coupled transport equations

6. **Analyze Results**: View pressure, concentration, flow distributions

7. **Export**: Download SVG, PNG, CSV, STL, OBJ files

## Key Concepts

### The Two Transport Systems

**Xylem** (blue): Water + minerals, roots → leaves
- Powered by transpiration (evaporation)
- Negative pressure (tension)
- Dead cells (hollow tubes)

**Phloem** (red): Sugars + nutrients, leaves → growing regions
- Powered by osmosis (Münch mechanism)
- Positive pressure (turgor)
- Living cells (sieve tubes)

### What the Simulation Does

PhytoFlow solves coupled fluid dynamics and mass transport:
1. **Xylem**: Hagen-Poiseuille flow (laminar, pressure-driven)
2. **Phloem**: Münch osmotic flow with membrane coupling
3. **Coupling**: Water exchange between xylem/phloem via membranes

### Interpreting Results

- **Pressure plots**: Show driving forces for flow
- **Concentration plots**: Show sugar distribution
- **Viscosity plots**: Show how sugar affects flow resistance
- **Warnings**: Literature-validated bounds on parameters

## Advanced Features

### Image Upload
Upload microscopy images to create "digital twins" of real specimens:
1. Upload cross-section image
2. Adjust thresholding to detect bundles
3. System generates geometry from detected structures

### Optimization
Let AI suggest parameter improvements:
- Click "Optimize Design"
- Set target (e.g., uniform sugar delivery)
- System uses Bayesian/CMA-ES to find optimal geometry

### 3D Export
Generate 3D-printable models:
- Export STL/OBJ files
- Check printability warnings
- Use for education, prototypes, microfluidics

## Tips

- Start with default presets to understand typical values
- Watch for warnings (⚠️) about out-of-range parameters
- Red alerts (🚨) indicate physically impossible states
- Hover over plots for detailed values
- Export data (CSV) for analysis in Excel/Python

## References

Key papers behind PhytoFlow's physics:
- Münch (1930): Pressure-flow hypothesis
- Tyree & Sperry (1989): Xylem cavitation
- Thompson & Holbrook (2003): Phloem transport
- Jensen et al. (2016): Phloem viscosity

See species profiles for specific citations.
        """
