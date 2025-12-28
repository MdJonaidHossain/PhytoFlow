"""Interactive Altair-based visualizations for PhytoFlow."""

import altair as alt
import pandas as pd
import numpy as np
from typing import Dict, List
import svgwrite


class PhytoFlowVisualizer:
    """Altair-based interactive visualization engine."""
    
    @staticmethod
    def plot_cross_section(geometry_data: Dict) -> alt.Chart:
        """
        Create interactive Altair chart of stem cross-section with hover tooltips.
        
        Args:
            geometry_data: Dictionary with 'stem' and 'bundles' information
        
        Returns:
            Altair chart object
        """
        stem_radius = geometry_data['stem']['radius']
        bundles = geometry_data['bundles']
        
        # Prepare data for Altair
        data_points = []
        
        # Add stem outline as background circle
        data_points.append({
            'x': 0,
            'y': 0,
            'radius': stem_radius,
            'tissue_type': 'Stem',
            'size': stem_radius * 1000,  # Calibrated for visual accuracy
            'color': '#e8f5e9'
        })
        
        # Add vascular bundles
        for bundle in bundles:
            # Xylem (blue)
            data_points.append({
                'x': bundle['center_x'],
                'y': bundle['center_y'],
                'radius': bundle['xylem_radius'],
                'tissue_type': 'Xylem',
                'size': bundle['xylem_radius'] * 2000,  # Calibrated scale
                'color': '#1976d2'
            })
            
            # Phloem (red)
            data_points.append({
                'x': bundle['center_x'],
                'y': bundle['center_y'],
                'radius': bundle['phloem_radius'],
                'tissue_type': 'Phloem',
                'size': bundle['phloem_radius'] * 2000,  # Calibrated scale
                'color': '#d32f2f'
            })
        
        df = pd.DataFrame(data_points)
        
        # Create interactive Altair chart
        chart = alt.Chart(df).mark_circle().encode(
            x=alt.X('x:Q', scale=alt.Scale(domain=[-stem_radius*1.1, stem_radius*1.1]),
                   axis=alt.Axis(title='X (mm)')),
            y=alt.Y('y:Q', scale=alt.Scale(domain=[-stem_radius*1.1, stem_radius*1.1]),
                   axis=alt.Axis(title='Y (mm)')),
            size=alt.Size('size:Q', scale=alt.Scale(range=[100, 10000]), legend=None),
            color=alt.Color('color:N', scale=None, legend=alt.Legend(title='Tissue Type')),
            tooltip=[
                alt.Tooltip('tissue_type:N', title='Tissue'),
                alt.Tooltip('radius:Q', title='Radius (mm)', format='.3f'),
                alt.Tooltip('x:Q', title='X (mm)', format='.2f'),
                alt.Tooltip('y:Q', title='Y (mm)', format='.2f')
            ]
        ).properties(
            width=500,
            height=500,
            title='Interactive Stem Cross-Section'
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            grid=True,
            gridOpacity=0.3
        )
        
        return chart
    
    @staticmethod
    def plot_simulation_results(results: Dict, plot_type: str = 'pressure') -> alt.Chart:
        """
        Create interactive Altair chart for simulation results.
        
        Args:
            results: Dictionary with simulation data
            plot_type: 'pressure', 'concentration', or 'viscosity'
        
        Returns:
            Altair chart object
        """
        x_mm = results['x_mm']
        
        # Prepare data based on plot type
        if plot_type == 'pressure':
            df = pd.DataFrame({
                'Position (mm)': np.concatenate([x_mm, x_mm]),
                'Pressure (kPa)': np.concatenate([
                    results['xylem_pressure_kPa'],
                    results['phloem_pressure_kPa']
                ]),
                'Tissue': ['Xylem'] * len(x_mm) + ['Phloem'] * len(x_mm)
            })
            
            chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X('Position (mm):Q', axis=alt.Axis(title='Position along stem (mm)')),
                y=alt.Y('Pressure (kPa):Q', axis=alt.Axis(title='Pressure (kPa)')),
                color=alt.Color('Tissue:N', 
                              scale=alt.Scale(domain=['Xylem', 'Phloem'],
                                            range=['#1976d2', '#d32f2f']),
                              legend=alt.Legend(title='Tissue Type')),
                tooltip=[
                    alt.Tooltip('Position (mm):Q', format='.1f'),
                    alt.Tooltip('Pressure (kPa):Q', format='.1f'),
                    alt.Tooltip('Tissue:N')
                ]
            ).properties(
                width=700,
                height=400,
                title='Pressure Distribution Along Stem'
            ).interactive()
        
        elif plot_type == 'concentration':
            df = pd.DataFrame({
                'Position (mm)': x_mm,
                'Concentration (mM)': results['concentration_mM']
            })
            
            chart = alt.Chart(df).mark_line(point=True, color='#388e3c').encode(
                x=alt.X('Position (mm):Q', axis=alt.Axis(title='Position along stem (mm)')),
                y=alt.Y('Concentration (mM):Q', axis=alt.Axis(title='Sucrose Concentration (mM)')),
                tooltip=[
                    alt.Tooltip('Position (mm):Q', format='.1f'),
                    alt.Tooltip('Concentration (mM):Q', format='.1f')
                ]
            ).properties(
                width=700,
                height=400,
                title='Sucrose Concentration Distribution'
            ).interactive()
        
        elif plot_type == 'viscosity':
            df = pd.DataFrame({
                'Position (mm)': x_mm,
                'Viscosity (mPa·s)': results['viscosity_mPa_s']
            })
            
            chart = alt.Chart(df).mark_line(point=True, color='#f57c00').encode(
                x=alt.X('Position (mm):Q', axis=alt.Axis(title='Position along stem (mm)')),
                y=alt.Y('Viscosity (mPa·s):Q', axis=alt.Axis(title='Viscosity (mPa·s)')),
                tooltip=[
                    alt.Tooltip('Position (mm):Q', format='.1f'),
                    alt.Tooltip('Viscosity (mPa·s):Q', format='.2f')
                ]
            ).properties(
                width=700,
                height=400,
                title='Viscosity Distribution (Concentration-Dependent)'
            ).interactive()
        
        else:
            raise ValueError(f"Unknown plot_type: {plot_type}")
        
        # Apply consistent theme
        chart = chart.configure_axis(
            labelFontSize=12,
            titleFontSize=14
        ).configure_title(
            fontSize=16,
            anchor='start'
        ).configure_legend(
            labelFontSize=12,
            titleFontSize=13
        )
        
        return chart
    
    @staticmethod
    def plot_flow_rates(results: Dict) -> alt.Chart:
        """
        Create interactive chart for flow rates.
        
        Args:
            results: Dictionary with simulation data
        
        Returns:
            Altair chart object
        """
        x_mm = results['x_mm'][:-1]  # Flow defined at edges
        
        df = pd.DataFrame({
            'Position (mm)': np.concatenate([x_mm, x_mm]),
            'Flow Rate (nL/s)': np.concatenate([
                results['xylem_flow_nL_s'][:-1],
                results['phloem_flow_nL_s'][:-1]
            ]),
            'Tissue': ['Xylem'] * len(x_mm) + ['Phloem'] * len(x_mm)
        })
        
        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X('Position (mm):Q', axis=alt.Axis(title='Position along stem (mm)')),
            y=alt.Y('Flow Rate (nL/s):Q', axis=alt.Axis(title='Flow Rate (nL/s)')),
            color=alt.Color('Tissue:N',
                          scale=alt.Scale(domain=['Xylem', 'Phloem'],
                                        range=['#1976d2', '#d32f2f']),
                          legend=alt.Legend(title='Tissue Type')),
            tooltip=[
                alt.Tooltip('Position (mm):Q', format='.1f'),
                alt.Tooltip('Flow Rate (nL/s):Q', format='.2e'),
                alt.Tooltip('Tissue:N')
            ]
        ).properties(
            width=700,
            height=400,
            title='Flow Rate Distribution'
        ).interactive()
        
        chart = chart.configure_axis(
            labelFontSize=12,
            titleFontSize=14
        ).configure_title(
            fontSize=16,
            anchor='start'
        )
        
        return chart
    
    @staticmethod
    def export_cross_section_svg(geometry_data: Dict, filepath: str, 
                                 width: int = 500, height: int = 500) -> None:
        """
        Export cross-section as SVG file.
        
        Args:
            geometry_data: Dictionary with 'stem' and 'bundles'
            filepath: Output SVG file path
            width: SVG width in pixels
            height: SVG height in pixels
        """
        stem_radius = geometry_data['stem']['radius']
        bundles = geometry_data['bundles']
        
        # Create SVG drawing
        dwg = svgwrite.Drawing(filepath, size=(width, height))
        
        # Calculate scaling factor
        scale = min(width, height) / (2.2 * stem_radius)
        center_x = width / 2
        center_y = height / 2
        
        # Draw stem outline
        dwg.add(dwg.circle(
            center=(center_x, center_y),
            r=stem_radius * scale,
            fill='#e8f5e9',
            stroke='#4caf50',
            stroke_width=2
        ))
        
        # Draw vascular bundles
        for bundle in bundles:
            # Convert coordinates
            x = center_x + bundle['center_x'] * scale
            y = center_y - bundle['center_y'] * scale  # Flip y-axis
            
            # Draw xylem (blue)
            dwg.add(dwg.circle(
                center=(x, y),
                r=bundle['xylem_radius'] * scale,
                fill='#1976d2',
                stroke='#0d47a1',
                stroke_width=1
            ))
            
            # Draw phloem (red, smaller, offset)
            offset = (bundle['xylem_radius'] + bundle['phloem_radius']) * scale * 0.5
            dwg.add(dwg.circle(
                center=(x + offset, y),
                r=bundle['phloem_radius'] * scale,
                fill='#d32f2f',
                stroke='#b71c1c',
                stroke_width=1
            ))
        
        # Add legend
        legend_x = 20
        legend_y = height - 80
        
        dwg.add(dwg.circle(center=(legend_x, legend_y), r=8, fill='#1976d2'))
        dwg.add(dwg.text('Xylem', insert=(legend_x + 15, legend_y + 5), 
                        font_size='14px', fill='black'))
        
        dwg.add(dwg.circle(center=(legend_x, legend_y + 25), r=8, fill='#d32f2f'))
        dwg.add(dwg.text('Phloem', insert=(legend_x + 15, legend_y + 30),
                        font_size='14px', fill='black'))
        
        dwg.add(dwg.circle(center=(legend_x, legend_y + 50), r=8, 
                          fill='#e8f5e9', stroke='#4caf50'))
        dwg.add(dwg.text('Stem', insert=(legend_x + 15, legend_y + 55),
                        font_size='14px', fill='black'))
        
        dwg.save()
    
    @staticmethod
    def create_summary_text(results: Dict, warnings: List[str]) -> str:
        """
        Generate plain-language summary of simulation results.
        
        Args:
            results: Simulation results dictionary
            warnings: List of warning messages
        
        Returns:
            Formatted summary text
        """
        # Calculate key metrics
        avg_xylem_pressure = np.mean(results['xylem_pressure_kPa'])
        avg_phloem_pressure = np.mean(results['phloem_pressure_kPa'])
        avg_concentration = np.mean(results['concentration_mM'])
        avg_viscosity = np.mean(results['viscosity_mPa_s'])
        
        # Flow rates
        if len(results['phloem_flow_nL_s']) > 0:
            avg_phloem_flow = np.mean(results['phloem_flow_nL_s'])
        else:
            avg_phloem_flow = 0
        
        summary = f"""
## Simulation Summary

### Pressure Distribution
- **Xylem**: Average {avg_xylem_pressure:.0f} kPa (negative pressure drives water uptake)
- **Phloem**: Average {avg_phloem_pressure:.0f} kPa (positive pressure drives sugar transport)

### Sugar Transport
- **Concentration**: Average {avg_concentration:.0f} mM sucrose
- **Viscosity**: Average {avg_viscosity:.2f} mPa·s (increases with sugar concentration)
- **Flow Rate**: Average {avg_phloem_flow:.2e} nL/s in phloem

### Biological Interpretation
"""
        
        # Add interpretation
        if avg_phloem_pressure > 1500:
            summary += "- ⚠️ High phloem pressure may stress membrane integrity.\n"
        elif avg_phloem_pressure < 400:
            summary += "- ⚠️ Low phloem pressure may reduce transport efficiency.\n"
        else:
            summary += "- ✓ Phloem pressure within healthy range for active transport.\n"
        
        if avg_concentration > 800:
            summary += "- ⚠️ Very high sugar concentration increases viscosity, slowing flow.\n"
        elif avg_concentration < 200:
            summary += "- ⚠️ Low sugar concentration reduces osmotic driving force.\n"
        else:
            summary += "- ✓ Sugar concentration supports efficient osmotic flow.\n"
        
        if avg_xylem_pressure < -2000:
            summary += "- 🚨 Severe xylem tension risks cavitation (air bubble formation).\n"
        else:
            summary += "- ✓ Xylem tension within safe range for water transport.\n"
        
        # Add warnings if any
        if warnings:
            summary += "\n### Warnings\n"
            for warning in warnings:
                summary += f"- {warning}\n"
        
        return summary
