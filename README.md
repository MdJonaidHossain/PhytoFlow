# 🌿 PhytoFlow AI

**Biophysics Engine for Plant Vascular Transport Simulation**

PhytoFlow is a GUI-first, literature-validated platform for simulating water and sugar transport in plant vascular systems. Built with Streamlit and interactive Altair visualizations, it combines parametric geometry generation, coupled Münch-Horwitz physics, AI image processing, design optimization, and 3D export capabilities.

![PhytoFlow](https://img.shields.io/badge/version-1.0-green)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

### 🎨 Interactive GUI
- **Species Presets**: Arabidopsis, Maize, Wheat, Rice with literature-backed defaults
- **Beginner/Advanced Modes**: Simplified or full parameter control
- **Real-time Validation**: Guardrails with warnings for out-of-range values
- **Interactive Visualizations**: Altair-based charts with hover tooltips and zoom/pan

### 📐 Geometry Generation
- **Parametric Generation**: Dicot ring or monocot scattered vascular bundle arrangements
- **AI Image Processing**: Upload microscopy images → automatic bundle detection (Digital Twin)
- **3D Export**: STL/OBJ files for 3D printing, microfluidics, education
- **Printability Checks**: Validates minimum feature sizes

### 🔬 Biophysics Simulation
- **Coupled Transport**: Xylem (Hagen-Poiseuille) + Phloem (Münch osmotic flow)
- **GPU Acceleration**: Auto-detects Apple Metal, NVIDIA CUDA, AMD ROCm, Intel oneAPI (5-100x faster)
- **Multi-Core CPU**: Automatic parallelization using all CPU cores (3-4x faster)
- **Concentration-Dependent Viscosity**: μ = μ₀ exp(k·C) modeling
- **Membrane Coupling**: Water exchange between xylem and phloem
- **Multi-Solute Support**: Sucrose, glucose, amino acids, auxin, K⁺, fluorescein
- **Literature Validation**: Automatic checks against published biological ranges

### 📊 Visualization & Export
- **Altair Interactive Charts**: Cross-sections, pressure, concentration, viscosity, flow rates
- **Plain-Language Explanations**: Biological interpretation of results
- **Export Formats**: SVG, PNG, CSV, JSON, STL, OBJ
- **Hover Tooltips**: Detailed information on all plots

### 🎯 AI Optimization
- **Design Objectives**: Uniform delivery, max flow, printability
- **Methods**: Scipy.optimize (L-BFGS-B, differential evolution)
- **Suggestions**: Heuristic parameter improvement recommendations

### 🧠 Advanced Scaffolds
- **PINN (Physics-Informed Neural Networks)**: DeepXDE template for coupled PDEs
- **GNN (Graph Neural Networks)**: PyTorch Geometric scaffold for network predictions
- **Digital Twin Fitting**: Inverse problem hooks for parameter estimation

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Quick Install

```bash
# Clone repository
git clone https://github.com/MdJonaidHossain/PhytoFlow.git
cd PhytoFlow

# Install dependencies
pip install -r requirements.txt

# Optional: Install GPU support (auto-detects your hardware)
# First, update pip (IMPORTANT for Apple Silicon!)
pip install --upgrade pip setuptools wheel

# Then install GPU library for your hardware:
# Apple Silicon (M1/M2/M3/M4):  pip install mlx
# NVIDIA GPU:                   pip install cupy-cuda12x
# AMD GPU:                      pip install cupy-rocm-5-0
# Intel GPU:                    pip install dpnp dpctl

# Diagnose GPU setup (optional)
python diagnose_gpu.py

# Launch application
./run_app.sh
# Or: streamlit run src/app.py
```

**Troubleshooting GPU Installation**:
- See `GPU_SETUP.md` for detailed instructions
- Run `python diagnose_gpu.py` to check your setup
- Most common issue: outdated pip → Run `pip install --upgrade pip setuptools wheel` first!

### Conda Install (Recommended)

```bash
# Create environment
conda create -n phytoflow python=3.10
conda activate phytoflow

# Install dependencies
pip install -r requirements.txt

# Launch
streamlit run src/app.py
```

The app will open in your browser at `http://localhost:8501`

## Quick Start

1. **Select Species**: Choose from dropdown (Arabidopsis, Maize, Wheat, Rice)
2. **Adjust Parameters**: Use sliders for geometry (vessel sizes, density) and physiology (pressures, concentrations)
3. **Generate Model**: Click "Generate Stem Model" to create cross-section
4. **Run Simulation**: Click "Run Simulation" to solve coupled transport equations
5. **View Results**: Explore interactive pressure, concentration, viscosity, and flow charts
6. **Export**: Download SVG, CSV, STL, or OBJ files

## Usage Examples

### Example 1: Arabidopsis Default Simulation

```python
# Defaults from species profile:
# - Stem radius: 0.5 mm
# - Xylem vessels: 20 μm diameter, 50 vessels/mm²
# - Phloem sieve tubes: 15 μm diameter
# - Xylem pressure: -500 kPa
# - Phloem pressure: 800 kPa
# - Sucrose: 400 mM

# Results show:
# - Negative xylem tension pulls water upward
# - Positive phloem pressure drives sugar flow
# - Viscosity increases with sugar concentration
```

### Example 2: Image-Based Digital Twin

1. Upload microscopy image (PNG/JPEG/TIFF)
2. Adjust segmentation threshold (Otsu/Adaptive/Multi-Otsu)
3. Set calibration (pixels per mm)
4. Click "Detect Bundles"
5. Review detected geometry
6. Click "Use This Geometry" → Run Simulation

### Example 3: Optimization for Printability

1. Generate geometry (e.g., Maize with large vessels)
2. Go to "Optimization" tab
3. Select "3D Printability" objective
4. Check parameters to optimize (vessel diameters, pressures)
5. Click "Run Optimization"
6. Review suggested parameter changes
7. Export optimized STL

## Parameter Ranges (Literature-Validated)

| Parameter | Arabidopsis | Maize | Wheat | Rice | Reference |
|-----------|-------------|-------|-------|------|-----------|
| Xylem Vessel Diameter | 10-40 μm | 40-150 μm | 25-90 μm | 20-70 μm | Hacke et al. 2001 |
| Phloem Sieve Diameter | 8-25 μm | 15-40 μm | 12-35 μm | 10-30 μm | van Bel 2003 |
| Xylem Pressure | -1500 to -100 kPa | -2000 to -200 kPa | -1800 to -150 kPa | -1200 to -100 kPa | Tyree & Sperry 1989 |
| Phloem Pressure | 400-1200 kPa | 600-1500 kPa | 500-1400 kPa | 450-1300 kPa | Thompson & Holbrook 2003 |
| Sucrose Concentration | 200-800 mM | 300-900 mM | 250-850 mM | 220-820 mM | Turgeon & Wolf 2009 |

## Project Structure

```
PhytoFlow/
├── src/
│   ├── app.py                  # Streamlit GUI entrypoint
│   ├── parameters.py           # Validation, guardrails, species profiles
│   ├── geometry.py             # Cross-section generation, 3D export
│   ├── simulation.py           # Münch-Horwitz solver, viscosity model
│   ├── visualization.py        # Altair charts, SVG export
│   ├── explanations.py         # Plain-language biological context
│   ├── image_to_geom.py        # Image segmentation → geometry
│   ├── optimization.py         # Design optimization (scipy, CMA-ES)
│   ├── pinn.py                 # DeepXDE PINN template (optional)
│   └── gnn.py                  # PyTorch Geometric GNN scaffold (optional)
├── data/
│   └── species_profiles.json   # Literature-backed parameter ranges
├── tests/
│   ├── test_geometry.py        # Geometry packing, reproducibility
│   ├── test_parameters.py      # Guardrails, validation
│   └── test_simulation.py      # Solver sanity, Poiseuille comparison
├── requirements.txt            # Dependencies
├── run_app.sh                  # Launch script
└── README.md                   # This file
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_geometry.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Key Concepts

### Xylem (Water Transport)
- **Mechanism**: Negative pressure (tension) pulls water from roots to leaves
- **Physics**: Hagen-Poiseuille flow (laminar, low Reynolds number)
- **Risk**: Cavitation (air bubble formation) at extreme tension (< -2000 kPa)

### Phloem (Sugar Transport)
- **Mechanism**: Münch pressure-flow hypothesis (osmotic driving force)
- **Physics**: Coupled Poiseuille + advection-diffusion + membrane exchange
- **Viscosity**: Increases exponentially with sugar concentration (μ ∝ e^(k·C))

### Münch Mechanism
1. **Source (Leaves)**: High sugar → high osmotic potential → water in → pressure builds
2. **Pressure Gradient**: Drives bulk flow from source to sink
3. **Sink (Roots/Fruits)**: Sugar unloaded → osmotic potential drops → water out

## Dependencies

### Core
- `streamlit>=1.28.0` - Web GUI framework
- `numpy>=1.24.0` - Numerical computing
- `scipy>=1.11.0` - Scientific computing, optimization
- `pandas>=2.0.0` - Data manipulation

### Visualization
- `altair>=5.0.0` - Interactive declarative visualizations
- `svgwrite>=1.4.3` - SVG export
- `plotly>=5.17.0` - Alternative 3D visualizations

### Geometry
- `shapely>=2.0.0` - Computational geometry
- `trimesh>=4.0.0` - 3D mesh processing

### Image Processing
- `opencv-python>=4.8.0` - Image I/O and processing
- `scikit-image>=0.21.0` - Segmentation algorithms
- `Pillow>=10.0.0` - Image format support

### Optimization
- `scikit-optimize>=0.9.0` - Bayesian optimization
- `cma>=3.3.0` - CMA-ES algorithm

### AI/ML (Optional)
- `torch>=2.0.0` - PyTorch framework
- `deepxde>=1.10.0` - PINN library
- `torch-geometric>=2.4.0` - GNN library

## References

### Key Papers
1. **Münch (1930)**: Die Stoffbewegungen in der Pflanze (Pressure-flow hypothesis)
2. **Tyree & Sperry (1989)**: Vulnerability of xylem to cavitation and embolism
3. **Thompson & Holbrook (2003)**: Phloem transport: from basic mechanisms to ecosystem
4. **Hacke et al. (2001)**: Trends in wood density and structure are linked to prevention of xylem implosion
5. **Jensen et al. (2016)**: Sap flow and sugar transport in plants
6. **Turgeon & Wolf (2009)**: Phloem transport: cellular pathways and molecular trafficking
7. **van Bel (2003)**: The phloem, a miracle of ingenuity

### Species-Specific
- **Arabidopsis**: Nieminen et al. 2004 (Plant J), Lucas et al. 2013 (Front Plant Sci)
- **Maize**: Shane et al. 2000 (New Phytol), Heinen et al. 2009 (Plant Cell Environ)
- **Wheat**: Wardlaw 1990 (Bot Rev), Patrick & Offler 2001 (Aust J Plant Physiol)
- **Rice**: Hoshikawa 1989 (Rice Anatomy), Fukumorita & Chino 1982 (Plant Cell Physiol)

## Roadmap

### Future Features
- [ ] PySide6 desktop GUI option
- [ ] Multi-segment simulations (roots → stem → leaves)
- [ ] Diurnal cycle modeling (day/night transpiration)
- [ ] Drought stress scenarios
- [ ] Real-time sensor integration (digital twin fitting)
- [ ] Multi-species comparative analysis
- [ ] Educational modules with quizzes

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Citation

If you use PhytoFlow in research, please cite:

```bibtex
@software{phytoflow2024,
  title = {PhytoFlow: Interactive Plant Vascular Transport Simulation},
  author = {PhytoFlow Contributors},
  year = {2024},
  url = {https://github.com/MdJonaidHossain/PhytoFlow}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/MdJonaidHossain/PhytoFlow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MdJonaidHossain/PhytoFlow/discussions)
- **Documentation**: See in-app "Help & Tutorial" tab

---

Built with ❤️ for plant biophysics research, education, and engineering