"""PhytoFlow: Streamlit GUI with Altair visualizations."""

import streamlit as st
import sys
import os
from pathlib import Path
import numpy as np
import pandas as pd
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Page config (must be first Streamlit command)
st.set_page_config(
    page_title="PhytoFlow - Plant Vascular Transport Simulator",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Show loading message while modules load
with st.spinner('⚙️ Loading PhytoFlow modules...'):
    # Lazy imports - only import when needed to speed up initial load
    @st.cache_resource
    def load_modules():
        """Lazy load heavy modules only when needed."""
        from parameters import ParameterValidator, MoleculeManager
        from geometry import StemGeometry
        from simulation import PhytoFlowSolver, MoleculeLibrary, LiteratureValidator
        from visualization import PhytoFlowVisualizer
        from explanations import BiologicalExplainer
        from optimization import DesignOptimizer
        from image_to_geom import ImageToGeometry
        from pinn import get_pinn_info
        from gnn import get_gnn_info
        
        return {
            'ParameterValidator': ParameterValidator,
            'MoleculeManager': MoleculeManager,
            'StemGeometry': StemGeometry,
            'PhytoFlowSolver': PhytoFlowSolver,
            'MoleculeLibrary': MoleculeLibrary,
            'LiteratureValidator': LiteratureValidator,
            'PhytoFlowVisualizer': PhytoFlowVisualizer,
            'BiologicalExplainer': BiologicalExplainer,
            'DesignOptimizer': DesignOptimizer,
            'ImageToGeometry': ImageToGeometry,
            'get_pinn_info': get_pinn_info,
            'get_gnn_info': get_gnn_info,
        }

    # Load modules with caching for faster subsequent runs
    modules = load_modules()
    ParameterValidator = modules['ParameterValidator']
    MoleculeManager = modules['MoleculeManager']
    StemGeometry = modules['StemGeometry']
    PhytoFlowSolver = modules['PhytoFlowSolver']
    MoleculeLibrary = modules['MoleculeLibrary']
    LiteratureValidator = modules['LiteratureValidator']
    PhytoFlowVisualizer = modules['PhytoFlowVisualizer']
    BiologicalExplainer = modules['BiologicalExplainer']
    DesignOptimizer = modules['DesignOptimizer']
    ImageToGeometry = modules['ImageToGeometry']
    get_pinn_info = modules['get_pinn_info']
    get_gnn_info = modules['get_gnn_info']

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2e7d32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #558b2f;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'geometry' not in st.session_state:
    st.session_state.geometry = None
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None
if 'warnings' not in st.session_state:
    st.session_state.warnings = []
if 'complexity_mode' not in st.session_state:
    st.session_state.complexity_mode = 'beginner'

# Title
st.markdown('<div class="main-header">🌿 PhytoFlow AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Biophysics Engine for Plant Vascular Transport</div>', unsafe_allow_html=True)

# Show hardware acceleration status
try:
    from accelerators import get_accelerator
    accel = get_accelerator()
    hw_info = accel.get_info()
    
    if accel.device_type != "cpu":
        st.success(f"🚀 GPU Acceleration: **{hw_info['device_name']}** + {hw_info['num_cpu_cores']} CPU cores")
    else:
        st.info(f"⚡ Multi-Core CPU: **{hw_info['num_cpu_cores']} cores** (Install GPU libraries for acceleration)")
except:
    pass  # Silently continue if accelerator not available

# Sidebar
st.sidebar.title("⚙️ Controls")

# Cache the validator and species data to avoid reloading on every interaction
@st.cache_resource
def get_validator():
    """Cache the parameter validator to avoid reloading species profiles."""
    return ParameterValidator("data/species_profiles.json")

validator = get_validator()
species_list = validator.get_species_list()
species_names = {
    'arabidopsis': 'Arabidopsis (Model Plant)',
    'maize': 'Maize (Corn)',
    'wheat': 'Wheat',
    'rice': 'Rice'
}

selected_species = st.sidebar.selectbox(
    "Select Species",
    species_list,
    format_func=lambda x: species_names.get(x, x)
)

# Beginner/Advanced toggle
st.sidebar.markdown("---")
complexity = st.sidebar.radio(
    "Complexity Mode",
    ['beginner', 'advanced'],
    format_func=lambda x: '🌱 Beginner' if x == 'beginner' else '🔬 Advanced'
)
st.session_state.complexity_mode = complexity

# Load species profile
species_profile = validator.get_species_profile(selected_species)
default_params = validator.get_default_parameters(selected_species)

# Display species info
with st.sidebar.expander("ℹ️ About This Species"):
    st.markdown(BiologicalExplainer.explain_species(selected_species))

st.sidebar.markdown("---")

# Geometry parameters
st.sidebar.subheader("📐 Geometry Parameters")

stem_radius = st.sidebar.slider(
    "Stem Radius (mm)",
    min_value=0.3, max_value=8.0,
    value=float(default_params.get('stem_radius_mm', 1.0)),
    step=0.1,
    help="Overall stem diameter"
)

xylem_diameter = st.sidebar.slider(
    "Xylem Vessel Diameter (μm)",
    min_value=5.0, max_value=200.0,
    value=float(default_params.get('xylem_vessel_diameter_um', 20.0)),
    step=5.0,
    help="Width of water-conducting vessels"
)

phloem_diameter = st.sidebar.slider(
    "Phloem Sieve Diameter (μm)",
    min_value=5.0, max_value=100.0,
    value=float(default_params.get('phloem_sieve_diameter_um', 15.0)),
    step=2.0,
    help="Width of sugar-conducting tubes"
)

if complexity == 'advanced':
    vessel_density = st.sidebar.slider(
        "Xylem Vessel Density (vessels/mm²)",
        min_value=10, max_value=150,
        value=int(default_params.get('xylem_vessel_density', 50)),
        step=5
    )
    
    n_bundles = st.sidebar.slider(
        "Number of Vascular Bundles",
        min_value=5, max_value=30,
        value=10,
        step=1
    )
else:
    vessel_density = int(default_params.get('xylem_vessel_density', 50))
    n_bundles = 8 if selected_species == 'arabidopsis' else 12

# Physiology parameters
st.sidebar.markdown("---")
st.sidebar.subheader("🔬 Physiology Parameters")

xylem_pressure = st.sidebar.slider(
    "Xylem Pressure (kPa)",
    min_value=-2500, max_value=-50,
    value=int(float(default_params.get('xylem_pressure_drop_kPa', -500))),
    step=50,
    help="Negative pressure pulling water upward"
)

phloem_pressure = st.sidebar.slider(
    "Phloem Pressure (kPa)",
    min_value=200, max_value=2000,
    value=int(float(default_params.get('phloem_pressure_kPa', 800))),
    step=50,
    help="Positive pressure driving sugar flow"
)

sucrose_conc = st.sidebar.slider(
    "Sucrose Concentration (mM)",
    min_value=100, max_value=1200,
    value=int(float(default_params.get('sucrose_concentration_mM', 400))),
    step=50,
    help="Sugar concentration in phloem"
)

if complexity == 'advanced':
    viscosity = st.sidebar.slider(
        "Base Viscosity (mPa·s)",
        min_value=1.0, max_value=5.0,
        value=float(default_params.get('viscosity_mPa_s', 1.5)),
        step=0.1
    )
    
    membrane_perm = st.sidebar.number_input(
        "Membrane Permeability (m/s)",
        min_value=1e-9, max_value=1e-5,
        value=float(default_params.get('membrane_permeability_m_s', 1e-7)),
        format="%.2e"
    )
else:
    viscosity = float(default_params.get('viscosity_mPa_s', 1.5))
    membrane_perm = float(default_params.get('membrane_permeability_m_s', 1e-7))

# Molecule manager
if complexity == 'advanced':
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧪 Molecule Manager")
    
    available_molecules = MoleculeLibrary.list_molecules()
    selected_molecules = st.sidebar.multiselect(
        "Add Molecules",
        available_molecules,
        default=['sucrose']
    )

# Action buttons
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Actions")

generate_btn = st.sidebar.button("🌿 Generate Stem Model", use_container_width=True)
simulate_btn = st.sidebar.button("▶️ Run Simulation", use_container_width=True)

# Main content area - Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Cross-Section",
    "📈 Simulation Results", 
    "🎯 Optimization",
    "📸 Image Upload",
    "📚 Help & Tutorial"
])

# Tab 1: Cross-Section
with tab1:
    st.header("Stem Cross-Section")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if generate_btn or st.session_state.geometry is not None:
            # Generate geometry
            geometry = StemGeometry(stem_radius_mm=stem_radius)
            
            # Determine arrangement
            if selected_species == 'arabidopsis':
                geometry.generate_dicot_ring(
                    xylem_diameter_um=xylem_diameter,
                    phloem_diameter_um=phloem_diameter,
                    n_bundles=n_bundles
                )
            else:  # monocot
                geometry.generate_monocot_scattered(
                    xylem_diameter_um=xylem_diameter,
                    phloem_diameter_um=phloem_diameter,
                    n_bundles=n_bundles,
                    seed=42
                )
            
            st.session_state.geometry = geometry
            
            # Get geometry data
            geom_data = geometry.get_cross_section_data()
            
            # Create interactive Altair chart
            chart = PhytoFlowVisualizer.plot_cross_section(geom_data)
            st.altair_chart(chart, use_container_width=True)
            
            # Printability check
            is_printable, print_warnings = geometry.check_printability(min_feature_size_mm=0.1)
            
            if is_printable:
                st.success("✅ Geometry is 3D-printable (min feature: 0.1 mm)")
            else:
                st.warning("⚠️ Printability Issues:")
                for warn in print_warnings:
                    st.warning(warn)
        
        else:
            st.info("👈 Click 'Generate Stem Model' to create cross-section visualization")
            st.markdown(BiologicalExplainer.explain_xylem())
            st.markdown(BiologicalExplainer.explain_phloem())
    
    with col2:
        st.subheader("Export Options")
        
        if st.session_state.geometry is not None:
            # SVG export
            if st.button("💾 Export SVG"):
                geom_data = st.session_state.geometry.get_cross_section_data()
                PhytoFlowVisualizer.export_cross_section_svg(
                    geom_data, 'cross_section.svg', width=800, height=800
                )
                st.success("Exported cross_section.svg")
                with open('cross_section.svg', 'r') as f:
                    st.download_button(
                        "⬇️ Download SVG",
                        f.read(),
                        file_name="phytoflow_cross_section.svg",
                        mime="image/svg+xml"
                    )
            
            # STL export
            if st.button("💾 Export STL"):
                extrusion_length = st.number_input(
                    "Extrusion Length (mm)", 
                    min_value=5.0, max_value=50.0, value=10.0, step=5.0,
                    key="stl_length"
                )
                st.session_state.geometry.export_stl('stem_model.stl', length_mm=extrusion_length)
                st.success("Exported stem_model.stl")
                with open('stem_model.stl', 'rb') as f:
                    st.download_button(
                        "⬇️ Download STL",
                        f.read(),
                        file_name="phytoflow_model.stl",
                        mime="application/octet-stream"
                    )
            
            # OBJ export
            if st.button("💾 Export OBJ"):
                extrusion_length = st.number_input(
                    "Extrusion Length (mm)", 
                    min_value=5.0, max_value=50.0, value=10.0, step=5.0,
                    key="obj_length"
                )
                st.session_state.geometry.export_obj('stem_model.obj', length_mm=extrusion_length)
                st.success("Exported stem_model.obj")
                with open('stem_model.obj', 'rb') as f:
                    st.download_button(
                        "⬇️ Download OBJ",
                        f.read(),
                        file_name="phytoflow_model.obj",
                        mime="application/octet-stream"
                    )
        
        # Explanations
        st.markdown("---")
        with st.expander("💡 Understanding Vascular Bundles"):
            st.markdown(BiologicalExplainer.explain_munch_mechanism())

# Tab 2: Simulation Results
with tab2:
    st.header("Simulation Results")
    
    if simulate_btn:
        if st.session_state.geometry is None:
            st.error("⚠️ Please generate geometry first!")
        else:
            # Collect parameters
            sim_params = {
                'xylem_vessel_diameter_um': xylem_diameter,
                'phloem_sieve_diameter_um': phloem_diameter,
                'xylem_pressure_drop_kPa': xylem_pressure,
                'phloem_pressure_kPa': phloem_pressure,
                'sucrose_concentration_mM': sucrose_conc,
                'viscosity_mPa_s': viscosity,
                'membrane_permeability_m_s': membrane_perm,
                'xylem_vessel_density': vessel_density
            }
            
            # Run simulation
            with st.spinner("🔄 Running coupled transport simulation..."):
                solver = PhytoFlowSolver(length_m=0.1, n_nodes=50)
                results, warnings = solver.run_simulation(sim_params)
                
                st.session_state.simulation_results = results
                st.session_state.warnings = warnings
            
            st.success("✅ Simulation complete!")
    
    # Display results
    if st.session_state.simulation_results is not None:
        results = st.session_state.simulation_results
        warnings = st.session_state.warnings
        
        # Display warnings
        if warnings:
            st.warning("⚠️ Warnings:")
            for warn in warnings:
                st.warning(warn)
        
        # Pressure plot
        st.subheader("Pressure Distribution")
        pressure_chart = PhytoFlowVisualizer.plot_simulation_results(results, 'pressure')
        st.altair_chart(pressure_chart, use_container_width=True)
        
        # Concentration plot
        st.subheader("Sugar Concentration")
        conc_chart = PhytoFlowVisualizer.plot_simulation_results(results, 'concentration')
        st.altair_chart(conc_chart, use_container_width=True)
        
        # Viscosity plot
        st.subheader("Viscosity (Concentration-Dependent)")
        visc_chart = PhytoFlowVisualizer.plot_simulation_results(results, 'viscosity')
        st.altair_chart(visc_chart, use_container_width=True)
        
        # Flow rates
        st.subheader("Flow Rates")
        flow_chart = PhytoFlowVisualizer.plot_flow_rates(results)
        st.altair_chart(flow_chart, use_container_width=True)
        
        # Summary
        st.markdown("---")
        st.subheader("📋 Summary")
        summary = PhytoFlowVisualizer.create_summary_text(results, warnings)
        st.markdown(summary)
        
        # Export data
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Export Data (CSV)"):
                df = pd.DataFrame(results)
                csv = df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    file_name="phytoflow_results.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("💾 Export Data (JSON)"):
                # Convert numpy arrays to lists for JSON serialization
                results_json = {k: v.tolist() if isinstance(v, np.ndarray) else v 
                              for k, v in results.items()}
                json_str = json.dumps(results_json, indent=2)
                st.download_button(
                    "⬇️ Download JSON",
                    json_str,
                    file_name="phytoflow_results.json",
                    mime="application/json"
                )
    else:
        st.info("👈 Click 'Run Simulation' to see results")
        st.markdown(BiologicalExplainer.explain_viscosity())

# Tab 3: Optimization
with tab3:
    st.header("AI Design Optimization")
    
    st.markdown("""
    Let AI suggest parameter improvements to achieve your goals:
    - **Uniform Delivery**: Minimize variation in sugar concentration
    - **Max Flow**: Maximize phloem transport capacity
    - **Printability**: Ensure geometry is 3D-printable
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        objective = st.selectbox(
            "Optimization Objective",
            ['uniform_delivery', 'max_flow', 'printability'],
            format_func=lambda x: {
                'uniform_delivery': '📊 Uniform Sugar Delivery',
                'max_flow': '⚡ Maximize Flow Rate',
                'printability': '🖨️ 3D Printability'
            }[x]
        )
        
        optimize_btn = st.button("🎯 Run Optimization", use_container_width=True)
    
    with col2:
        st.markdown("**Parameters to Optimize:**")
        opt_phloem_diameter = st.checkbox("Phloem Diameter", value=True)
        opt_pressure = st.checkbox("Phloem Pressure", value=True)
        opt_concentration = st.checkbox("Sugar Concentration", value=True)
    
    if optimize_btn:
        if st.session_state.geometry is None:
            st.error("⚠️ Please generate geometry first!")
        else:
            # Prepare optimization
            param_names = []
            bounds = []
            base_params = {
                'xylem_vessel_diameter_um': xylem_diameter,
                'phloem_sieve_diameter_um': phloem_diameter,
                'xylem_pressure_drop_kPa': xylem_pressure,
                'phloem_pressure_kPa': phloem_pressure,
                'sucrose_concentration_mM': sucrose_conc,
                'viscosity_mPa_s': viscosity,
                'membrane_permeability_m_s': membrane_perm,
                'xylem_vessel_density': vessel_density
            }
            
            if opt_phloem_diameter:
                param_names.append('phloem_sieve_diameter_um')
                bounds.append((10.0, 50.0))
            
            if opt_pressure:
                param_names.append('phloem_pressure_kPa')
                bounds.append((400, 1500))
            
            if opt_concentration:
                param_names.append('sucrose_concentration_mM')
                bounds.append((200, 1000))
            
            if not param_names:
                st.warning("⚠️ Please select at least one parameter to optimize")
            else:
                with st.spinner("🔄 Running optimization..."):
                    # Create simulation function wrapper
                    def sim_func(params):
                        solver = PhytoFlowSolver(length_m=0.1, n_nodes=50)
                        return solver.run_simulation(params)
                    
                    optimizer = DesignOptimizer(sim_func)
                    
                    # Run optimization
                    result = optimizer.optimize_scipy(
                        objective=objective,
                        param_names=param_names,
                        bounds=bounds,
                        base_params=base_params,
                        method='L-BFGS-B',
                        max_iter=20
                    )
                
                st.success("✅ Optimization complete!")
                
                # Display results
                st.subheader("Optimized Parameters")
                
                comp_df = pd.DataFrame({
                    'Parameter': param_names,
                    'Original': [base_params[p] for p in param_names],
                    'Optimized': [result['parameters'][p] for p in param_names],
                    'Change': [result['parameters'][p] - base_params[p] for p in param_names]
                })
                st.dataframe(comp_df, use_container_width=True)
                
                st.metric("Optimization Score", f"{result['score']:.2f}", 
                         help="Lower is better")
                
                if result['success']:
                    st.success(f"✅ {result['message']}")
                else:
                    st.warning(f"⚠️ {result['message']}")
                
                # Quick suggestions
                st.markdown("---")
                st.subheader("💡 Quick Suggestions")
                suggestions = optimizer.suggest_improvements(base_params, species_profile)
                
                if suggestions['changes']:
                    for i, change in enumerate(suggestions['changes']):
                        st.info(f"**{change['parameter']}**: {change['current']:.1f} → "
                               f"{change['suggested']:.1f} ({change['change']})")
                        if i < len(suggestions['reasoning']):
                            st.markdown(f"*{suggestions['reasoning'][i]}*")
                else:
                    st.success("✅ Current parameters look good!")

# Tab 4: Image Upload
with tab4:
    st.header("📸 Image to Geometry (Digital Twin)")
    
    st.markdown("""
    Upload a microscopy image of a plant stem cross-section to automatically detect vascular bundles 
    and create a digital twin model.
    """)
    
    uploaded_file = st.file_uploader(
        "Upload Cross-Section Image",
        type=['png', 'jpg', 'jpeg', 'tif', 'tiff'],
        help="Upload microscopy image showing vascular bundles"
    )
    
    if uploaded_file is not None:
        # Save uploaded file
        with open("temp_image.png", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Image")
            st.image(uploaded_file, use_column_width=True)
        
        with col2:
            st.subheader("Processing Controls")
            
            threshold_method = st.selectbox(
                "Segmentation Method",
                ['otsu', 'multiotsu', 'adaptive'],
                help="Algorithm for detecting bundles"
            )
            
            min_size = st.slider(
                "Min Bundle Size (pixels)",
                min_value=10, max_value=200, value=50, step=10
            )
            
            pixels_per_mm = st.number_input(
                "Calibration (pixels/mm)",
                min_value=10.0, max_value=500.0, value=100.0, step=10.0,
                help="Image scale factor"
            )
            
            process_btn = st.button("🔬 Detect Bundles")
        
        if process_btn:
            with st.spinner("Processing image..."):
                # Process image
                img_processor = ImageToGeometry()
                gray = img_processor.load_image("temp_image.png")
                preprocessed = img_processor.preprocess(gray, blur_sigma=1.0)
                binary = img_processor.segment_threshold(preprocessed, method=threshold_method)
                cleaned = img_processor.clean_mask(binary, min_size=min_size)
                bundles = img_processor.extract_bundles(cleaned, pixels_per_mm=pixels_per_mm)
                classified_bundles = img_processor.classify_bundles(bundles)
                
                stats = img_processor.bundle_statistics(classified_bundles)
                geom_data = img_processor.to_geometry_format(classified_bundles)
            
            st.success(f"✅ Detected {stats['n_bundles']} vascular bundles!")
            
            # Display statistics
            st.subheader("Detection Statistics")
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                st.metric("Bundles Detected", stats['n_bundles'])
            with stat_col2:
                st.metric("Mean Radius", f"{stats['mean_radius_mm']:.3f} mm")
            with stat_col3:
                st.metric("Total Area", f"{stats['total_area_mm2']:.2f} mm²")
            
            # Visualize detected geometry
            st.subheader("Detected Geometry")
            chart = PhytoFlowVisualizer.plot_cross_section(geom_data)
            st.altair_chart(chart, use_container_width=True)
            
            # Save to session state
            if st.button("✅ Use This Geometry"):
                # Create geometry object from detected data
                geometry = StemGeometry(stem_radius_mm=geom_data['stem']['radius'])
                geometry.bundles = []
                
                from geometry import VascularBundle
                for bundle in geom_data['bundles']:
                    vb = VascularBundle(
                        center=(bundle['center_x'], bundle['center_y']),
                        xylem_radius=bundle['xylem_radius'],
                        phloem_radius=bundle['phloem_radius'],
                        bundle_type='detected'
                    )
                    geometry.bundles.append(vb)
                
                geometry.arrangement = 'image_based'
                st.session_state.geometry = geometry
                st.success("✅ Geometry loaded! Go to 'Simulation Results' to run analysis.")

# Tab 5: Help & Tutorial
with tab5:
    st.header("📚 Help & Tutorial")
    
    tutorial_tab1, tutorial_tab2, tutorial_tab3 = st.tabs([
        "Quick Start",
        "Concepts",
        "Advanced Features"
    ])
    
    with tutorial_tab1:
        st.markdown(BiologicalExplainer.get_tutorial_text())
    
    with tutorial_tab2:
        st.subheader("Key Biological Concepts")
        
        with st.expander("🔵 Xylem - Water Transport"):
            st.markdown(BiologicalExplainer.explain_xylem())
        
        with st.expander("🔴 Phloem - Sugar Transport"):
            st.markdown(BiologicalExplainer.explain_phloem())
        
        with st.expander("💧 Münch Pressure-Flow Mechanism"):
            st.markdown(BiologicalExplainer.explain_munch_mechanism())
        
        with st.expander("💥 Cavitation Risk"):
            st.markdown(BiologicalExplainer.explain_cavitation())
        
        with st.expander("🌊 Viscosity Effects"):
            st.markdown(BiologicalExplainer.explain_viscosity())
    
    with tutorial_tab3:
        st.subheader("Advanced Features")
        
        st.markdown("### 🤖 AI/ML Scaffolds")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Physics-Informed Neural Networks (PINN)**")
            pinn_info = get_pinn_info()
            st.write(f"Status: {'✅ Available' if pinn_info['available'] else '❌ Not installed'}")
            st.write(pinn_info['description'])
            with st.expander("Learn More"):
                st.write("**Features:**")
                for feat in pinn_info['features']:
                    st.write(f"- {feat}")
                st.write("**References:**")
                for ref in pinn_info['references']:
                    st.write(f"- {ref}")
        
        with col2:
            st.markdown("**Graph Neural Networks (GNN)**")
            gnn_info = get_gnn_info()
            st.write(f"Status: {'✅ Available' if gnn_info['available'] else '❌ Not installed'}")
            st.write(gnn_info['description'])
            with st.expander("Learn More"):
                st.write("**Use Cases:**")
                for use_case in gnn_info['use_cases']:
                    st.write(f"- {use_case}")
                st.write("**References:**")
                for ref in gnn_info['references']:
                    st.write(f"- {ref}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>PhytoFlow v1.0 | Built with Streamlit & Altair | 
    <a href='https://github.com/MdJonaidHossain/PhytoFlow'>GitHub</a></p>
    <p>Literature-validated biophysics for plant vascular transport simulation</p>
</div>
""", unsafe_allow_html=True)
