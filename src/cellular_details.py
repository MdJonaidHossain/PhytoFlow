"""Cellular-level anatomical details: secondary walls, pits, plasmodesmata, companion cells."""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class SecondaryWall:
    """Secondary cell wall properties for xylem vessels."""
    thickness_nm: float = 200.0  # Typical 50-500 nm
    lignin_content_percent: float = 25.0  # 20-35% for angiosperms
    cellulose_microfibril_angle_deg: float = 10.0  # S2 layer typical: 5-30°
    layers: List[str] = None  # ['S1', 'S2', 'S3']
    
    def __post_init__(self):
        if self.layers is None:
            self.layers = ['S1', 'S2', 'S3']
    
    def get_mechanical_strength(self) -> float:
        """
        Estimate mechanical strength (relative units).
        
        Based on thickness and lignin content.
        """
        return (self.thickness_nm / 200.0) * (self.lignin_content_percent / 25.0)
    
    def get_pit_resistance(self) -> float:
        """
        Estimate flow resistance contribution from pit membranes.
        
        Returns:
            Relative resistance factor (1.0 = baseline)
        """
        # Thicker walls typically have smaller pit apertures
        return 1.0 + (self.thickness_nm - 200) / 1000


@dataclass
class Pit:
    """Pit structure connecting adjacent xylem vessels."""
    diameter_um: float = 5.0  # Typical 1-15 μm
    pit_type: str = 'bordered'  # 'simple' or 'bordered'
    membrane_present: bool = True
    membrane_thickness_nm: float = 100.0
    membrane_porosity: float = 0.3  # 0-1, higher = more permeable
    
    def get_flow_conductance(self) -> float:
        """
        Calculate pit conductance for water flow.
        
        Returns:
            Relative conductance (dimensionless)
        """
        # Area factor
        area_factor = (self.diameter_um / 5.0) ** 2
        
        # Membrane resistance
        if self.membrane_present:
            membrane_factor = self.membrane_porosity
        else:
            membrane_factor = 1.0
        
        # Bordered pits have higher resistance than simple
        type_factor = 0.7 if self.pit_type == 'bordered' else 1.0
        
        return area_factor * membrane_factor * type_factor


@dataclass
class Plasmodesma:
    """Plasmodesmata: cell-to-cell connections."""
    diameter_nm: float = 40.0  # Typical 20-60 nm
    density_per_um2: float = 5.0  # Typical 0.1-15 per μm²
    conductance_pS: float = 3.0  # Picosiemens, for ion transport
    size_exclusion_limit_kDa: float = 10.0  # Molecular weight cutoff
    
    def can_transport(self, molecular_weight_kDa: float) -> bool:
        """Check if molecule can pass through plasmodesmata."""
        return molecular_weight_kDa < self.size_exclusion_limit_kDa
    
    def get_total_conductance(self, cell_area_um2: float) -> float:
        """
        Calculate total plasmodesmatal conductance for a cell.
        
        Args:
            cell_area_um2: Cell wall area in μm²
        
        Returns:
            Total conductance in pS
        """
        n_plasmodesmata = self.density_per_um2 * cell_area_um2
        return n_plasmodesmata * self.conductance_pS


@dataclass
class CompanionCell:
    """Companion cell associated with phloem sieve element."""
    diameter_um: float = 10.0
    length_um: float = 50.0
    metabolic_activity: float = 1.0  # Relative to parenchyma
    plasmodesmata_to_sieve: Plasmodesma = None
    
    def __post_init__(self):
        if self.plasmodesmata_to_sieve is None:
            # High density connection to sieve element
            self.plasmodesmata_to_sieve = Plasmodesma(
                diameter_nm=50.0,
                density_per_um2=10.0,  # High for companion-sieve connection
                size_exclusion_limit_kDa=50.0  # More permeable
            )
    
    def get_loading_capacity(self) -> float:
        """
        Estimate sugar loading capacity.
        
        Returns:
            Relative loading rate
        """
        # Based on metabolic activity and plasmodesmatal connections
        surface_area = np.pi * self.diameter_um * self.length_um
        conductance = self.plasmodesmata_to_sieve.get_total_conductance(surface_area)
        
        return self.metabolic_activity * (conductance / 1000)  # Normalized


@dataclass
class ParenchymaCell:
    """Parenchyma cells (storage, support)."""
    diameter_um: float = 20.0
    wall_thickness_nm: float = 100.0  # Primary wall, thinner than secondary
    starch_content_percent: float = 5.0
    water_content_percent: float = 85.0
    
    def get_storage_capacity(self) -> float:
        """Estimate storage capacity for sugars/starch."""
        volume_um3 = (4/3) * np.pi * (self.diameter_um / 2) ** 3
        return volume_um3 * self.starch_content_percent / 100


class CellularAnatomyModel:
    """Integrate cellular-level details into vascular model."""
    
    def __init__(self, species: str = 'arabidopsis'):
        """
        Initialize with species-specific cellular parameters.
        
        Args:
            species: Plant species name
        """
        self.species = species
        self.secondary_walls = {}
        self.pits = {}
        self.plasmodesmata = {}
        self.companion_cells = {}
        self.parenchyma = {}
        
        self._load_species_defaults(species)
    
    def _load_species_defaults(self, species: str):
        """Load species-specific cellular parameters."""
        
        if species == 'arabidopsis':
            # Arabidopsis: herbaceous, thin secondary walls
            self.secondary_walls['xylem'] = SecondaryWall(
                thickness_nm=150.0,
                lignin_content_percent=22.0,
                cellulose_microfibril_angle_deg=15.0
            )
            self.pits['xylem'] = Pit(
                diameter_um=3.0,
                pit_type='simple',
                membrane_porosity=0.4
            )
            self.plasmodesmata['phloem'] = Plasmodesma(
                diameter_nm=45.0,
                density_per_um2=8.0,
                size_exclusion_limit_kDa=12.0
            )
            self.companion_cells['phloem'] = CompanionCell(
                diameter_um=8.0,
                metabolic_activity=1.2
            )
            self.parenchyma['cortex'] = ParenchymaCell(
                diameter_um=18.0,
                starch_content_percent=3.0
            )
        
        elif species == 'maize':
            # Maize: monocot, larger vessels, thick walls
            self.secondary_walls['xylem'] = SecondaryWall(
                thickness_nm=300.0,
                lignin_content_percent=28.0,
                cellulose_microfibril_angle_deg=12.0
            )
            self.pits['xylem'] = Pit(
                diameter_um=8.0,
                pit_type='bordered',
                membrane_porosity=0.35
            )
            self.plasmodesmata['phloem'] = Plasmodesma(
                diameter_nm=50.0,
                density_per_um2=6.0,
                size_exclusion_limit_kDa=15.0
            )
            self.companion_cells['phloem'] = CompanionCell(
                diameter_um=12.0,
                metabolic_activity=1.5
            )
            self.parenchyma['pith'] = ParenchymaCell(
                diameter_um=30.0,
                starch_content_percent=8.0
            )
        
        elif species in ['wheat', 'rice']:
            # Wheat/Rice: moderate properties
            self.secondary_walls['xylem'] = SecondaryWall(
                thickness_nm=220.0,
                lignin_content_percent=25.0,
                cellulose_microfibril_angle_deg=13.0
            )
            self.pits['xylem'] = Pit(
                diameter_um=5.0,
                pit_type='bordered',
                membrane_porosity=0.38
            )
            self.plasmodesmata['phloem'] = Plasmodesma(
                diameter_nm=48.0,
                density_per_um2=7.0,
                size_exclusion_limit_kDa=13.0
            )
            self.companion_cells['phloem'] = CompanionCell(
                diameter_um=10.0,
                metabolic_activity=1.3
            )
            self.parenchyma['ground'] = ParenchymaCell(
                diameter_um=22.0,
                starch_content_percent=5.0
            )
    
    def get_effective_vessel_conductivity(self, vessel_diameter_um: float,
                                         vessel_length_um: float) -> float:
        """
        Calculate effective conductivity including pit resistance.
        
        Args:
            vessel_diameter_um: Vessel diameter
            vessel_length_um: Vessel length
        
        Returns:
            Effective conductivity factor (0-1)
        """
        # Base conductivity from Poiseuille (∝ r⁴)
        base_conductivity = (vessel_diameter_um / 20.0) ** 4
        
        # Pit resistance (assume pits every ~100 μm)
        n_pits = vessel_length_um / 100
        pit_conductance = self.pits['xylem'].get_flow_conductance()
        
        # Total resistance = vessel resistance + n_pits * pit_resistance
        # Simplified: reduce conductivity by pit factor
        pit_factor = 1.0 / (1.0 + n_pits * (1.0 / pit_conductance - 1.0) * 0.1)
        
        return base_conductivity * pit_factor
    
    def get_phloem_loading_rate(self, sieve_diameter_um: float) -> float:
        """
        Estimate phloem loading rate based on companion cells.
        
        Args:
            sieve_diameter_um: Sieve element diameter
        
        Returns:
            Relative loading rate
        """
        companion = self.companion_cells.get('phloem')
        if companion is None:
            return 1.0
        
        loading_capacity = companion.get_loading_capacity()
        
        # Scale by sieve tube size
        size_factor = sieve_diameter_um / 15.0
        
        return loading_capacity * size_factor
    
    def get_tissue_annotations(self) -> Dict[str, Dict]:
        """
        Get tissue-level annotations for visualization.
        
        Returns:
            Dictionary with tissue types and properties
        """
        annotations = {
            'xylem': {
                'cell_types': ['vessel_elements', 'tracheids', 'fibers'],
                'secondary_wall': self.secondary_walls.get('xylem'),
                'pit_type': self.pits.get('xylem').pit_type if 'xylem' in self.pits else 'simple',
                'function': 'Water and mineral transport',
                'color': '#1976d2'
            },
            'phloem': {
                'cell_types': ['sieve_elements', 'companion_cells'],
                'plasmodesmata_density': self.plasmodesmata.get('phloem').density_per_um2 if 'phloem' in self.plasmodesmata else 5.0,
                'function': 'Sugar and nutrient transport',
                'color': '#d32f2f'
            },
            'parenchyma': {
                'cell_types': ['cortex', 'pith', 'ray_cells'],
                'wall_type': 'primary',
                'function': 'Storage, support, radial transport',
                'color': '#f9e79f'
            },
            'epidermis': {
                'cell_types': ['epidermis', 'cuticle'],
                'function': 'Protection, water regulation',
                'color': '#aed6f1'
            }
        }
        
        return annotations
    
    def export_cellular_details(self) -> Dict:
        """Export all cellular parameters for documentation."""
        details = {
            'species': self.species,
            'secondary_walls': {},
            'pits': {},
            'plasmodesmata': {},
            'companion_cells': {},
            'parenchyma': {}
        }
        
        for key, obj in self.secondary_walls.items():
            details['secondary_walls'][key] = {
                'thickness_nm': obj.thickness_nm,
                'lignin_percent': obj.lignin_content_percent,
                'microfibril_angle_deg': obj.cellulose_microfibril_angle_deg,
                'mechanical_strength': obj.get_mechanical_strength()
            }
        
        for key, obj in self.pits.items():
            details['pits'][key] = {
                'diameter_um': obj.diameter_um,
                'type': obj.pit_type,
                'membrane_present': obj.membrane_present,
                'porosity': obj.membrane_porosity,
                'conductance': obj.get_flow_conductance()
            }
        
        for key, obj in self.plasmodesmata.items():
            details['plasmodesmata'][key] = {
                'diameter_nm': obj.diameter_nm,
                'density_per_um2': obj.density_per_um2,
                'conductance_pS': obj.conductance_pS,
                'size_exclusion_kDa': obj.size_exclusion_limit_kDa
            }
        
        for key, obj in self.companion_cells.items():
            details['companion_cells'][key] = {
                'diameter_um': obj.diameter_um,
                'length_um': obj.length_um,
                'metabolic_activity': obj.metabolic_activity,
                'loading_capacity': obj.get_loading_capacity()
            }
        
        for key, obj in self.parenchyma.items():
            details['parenchyma'][key] = {
                'diameter_um': obj.diameter_um,
                'wall_thickness_nm': obj.wall_thickness_nm,
                'starch_percent': obj.starch_content_percent,
                'storage_capacity': obj.get_storage_capacity()
            }
        
        return details


def get_cellular_explanations() -> Dict[str, str]:
    """Get educational explanations of cellular structures."""
    return {
        'secondary_wall': """
**Secondary Cell Walls in Xylem**

After initial growth, xylem vessels deposit additional cell wall layers:
- **S1 Layer**: Outer, thin, microfibrils at large angle
- **S2 Layer**: Thickest, determines mechanical properties, microfibrils nearly parallel to cell axis
- **S3 Layer**: Inner, thin, microfibrils at large angle

**Lignin**: Waterproofing polymer (20-35%) that strengthens walls and makes vessels rigid and impermeable.

**Function**: Provides mechanical strength to withstand negative pressure without collapsing.
        """,
        
        'pits': """
**Pits: Vessel-to-Vessel Connections**

Pits are openings in secondary walls that allow water to move between adjacent vessels:

**Simple Pits**: Found in parenchyma and some xylem. Just openings with primary wall.

**Bordered Pits**: Found in xylem vessels. Overhanging border of secondary wall creates chamber. 
Pit membrane (primary wall) acts as safety valve: if one vessel cavitates (fills with air), 
membrane blocks air entry to neighbors.

**Trade-off**: More pits = better connectivity but more flow resistance. Fewer pits = less backup if vessels fail.
        """,
        
        'plasmodesmata': """
**Plasmodesmata: Plant Cell "Gap Junctions"**

Cytoplasmic channels (20-60 nm) connecting adjacent plant cells:

- **Structure**: Plasma membrane-lined channels with central desmotubule (ER connection)
- **Size Exclusion**: Small molecules pass freely (< 1 kDa), proteins need targeting signals
- **Regulation**: Plants can dilate or constrict plasmodesmata in response to signals
- **Phloem**: High density between companion cells and sieve elements enables sugar loading

**Function**: Allow cell-to-cell communication and transport without crossing membranes.
        """,
        
        'companion_cells': """
**Companion Cells: The Phloem's Life Support**

Phloem sieve elements lose most organelles at maturity and rely on companion cells:

- **Metabolic Engine**: Full set of organelles, high ribosome density, active protein synthesis
- **Sugar Loading**: Actively pump sucrose into sieve elements (requires ATP)
- **Connected**: Abundant plasmodesmata to sieve elements (10+ per μm²)
- **Lifespan**: Live as long as sieve element; when companion cell dies, sieve element fails

**Types**:
- **Ordinary**: Support local sieve elements
- **Transfer Cells**: Specialized wall ingrowths for enhanced loading (grasses)

**Analogy**: Like mitochondria for a cell—provides energy and maintenance.
        """,
        
        'parenchyma': """
**Parenchyma: The Versatile "Filler" Cells**

Most common plant cell type, fills spaces between vascular bundles:

- **Storage**: Starch, proteins, oils (3-15% dry weight as starch in stems)
- **Support**: Turgid cells provide structural support in herbaceous plants
- **Radial Transport**: Move water and solutes between vascular bundles
- **Regeneration**: Can dedifferentiate and form new tissues (wound healing, adventitious roots)

**Types**:
- **Cortex**: Between epidermis and vascular tissue
- **Pith**: Center of dicot/monocot stems
- **Ray Parenchyma**: Radial bands in woody stems

**Flexibility**: Can survive as living cells for decades (unlike xylem vessels which die).
        """
    }
