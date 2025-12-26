"""Tests for geometry module."""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from geometry import StemGeometry, VascularBundle


class TestVascularBundle:
    """Test VascularBundle class."""
    
    def test_bundle_creation(self):
        """Test creating a vascular bundle."""
        bundle = VascularBundle(
            center=(1.0, 2.0),
            xylem_radius=0.05,
            phloem_radius=0.03,
            bundle_type="collateral"
        )
        
        assert bundle.center == (1.0, 2.0)
        assert bundle.xylem_radius == 0.05
        assert bundle.phloem_radius == 0.03
        assert bundle.bundle_type == "collateral"
    
    def test_bundle_to_dict(self):
        """Test serialization to dictionary."""
        bundle = VascularBundle((0.5, 0.5), 0.02, 0.01, "test")
        data = bundle.to_dict()
        
        assert 'center' in data
        assert 'xylem_radius' in data
        assert 'phloem_radius' in data
        assert 'type' in data
        assert data['center'] == (0.5, 0.5)


class TestStemGeometry:
    """Test StemGeometry class."""
    
    def test_geometry_initialization(self):
        """Test creating stem geometry."""
        geom = StemGeometry(stem_radius_mm=1.5)
        assert geom.stem_radius_mm == 1.5
        assert len(geom.bundles) == 0
    
    def test_dicot_ring_generation(self):
        """Test dicot ring arrangement generation."""
        geom = StemGeometry(stem_radius_mm=1.0)
        geom.generate_dicot_ring(
            xylem_diameter_um=20.0,
            phloem_diameter_um=15.0,
            n_bundles=8
        )
        
        assert len(geom.bundles) == 8
        assert geom.arrangement == "dicot"
        
        # Check bundles are in a ring
        for bundle in geom.bundles:
            distance = np.sqrt(bundle.center[0]**2 + bundle.center[1]**2)
            expected_distance = geom.stem_radius_mm * 0.7
            assert abs(distance - expected_distance) < 0.01
    
    def test_monocot_scattered_generation(self):
        """Test monocot scattered arrangement."""
        geom = StemGeometry(stem_radius_mm=2.0)
        geom.generate_monocot_scattered(
            xylem_diameter_um=50.0,
            phloem_diameter_um=25.0,
            n_bundles=12,
            seed=42
        )
        
        assert len(geom.bundles) == 12
        assert geom.arrangement == "monocot"
        
        # Check bundles are within stem radius
        for bundle in geom.bundles:
            distance = np.sqrt(bundle.center[0]**2 + bundle.center[1]**2)
            assert distance < geom.stem_radius_mm * 0.85
    
    def test_cross_section_data(self):
        """Test getting cross-section data."""
        geom = StemGeometry(stem_radius_mm=1.0)
        geom.generate_dicot_ring(20.0, 15.0, n_bundles=6)
        
        data = geom.get_cross_section_data()
        
        assert 'stem' in data
        assert 'bundles' in data
        assert data['stem']['radius'] == 1.0
        assert len(data['bundles']) == 6
        
        bundle_data = data['bundles'][0]
        assert 'center_x' in bundle_data
        assert 'center_y' in bundle_data
        assert 'xylem_radius' in bundle_data
        assert 'phloem_radius' in bundle_data
    
    def test_printability_check_valid(self):
        """Test printability check for valid geometry."""
        geom = StemGeometry(stem_radius_mm=2.0)
        geom.generate_dicot_ring(
            xylem_diameter_um=200.0,  # 0.2 mm diameter = printable
            phloem_diameter_um=150.0,
            n_bundles=6
        )
        
        is_printable, warnings = geom.check_printability(min_feature_size_mm=0.1)
        
        assert is_printable
        assert len(warnings) == 0
    
    def test_printability_check_invalid(self):
        """Test printability check for too-small features."""
        geom = StemGeometry(stem_radius_mm=1.0)
        geom.generate_dicot_ring(
            xylem_diameter_um=50.0,  # 0.05 mm diameter = too small
            phloem_diameter_um=30.0,
            n_bundles=8
        )
        
        is_printable, warnings = geom.check_printability(min_feature_size_mm=0.1)
        
        assert not is_printable
        assert len(warnings) > 0
    
    def test_shapely_conversion(self):
        """Test conversion to Shapely polygons."""
        geom = StemGeometry(stem_radius_mm=1.0)
        geom.generate_dicot_ring(20.0, 15.0, n_bundles=4)
        
        stem, xylem_polygons, phloem_polygons = geom.to_shapely_polygons()
        
        assert stem.geom_type == 'Polygon'
        assert len(xylem_polygons) == 4
        assert len(phloem_polygons) == 4
        
        # Check stem area is approximately correct
        expected_area = np.pi * (1.0 ** 2)
        assert abs(stem.area - expected_area) < 0.1
    
    def test_3d_extrusion(self):
        """Test 3D mesh extrusion."""
        geom = StemGeometry(stem_radius_mm=1.0)
        geom.generate_dicot_ring(20.0, 15.0, n_bundles=4)
        
        mesh = geom.extrude_to_3d(length_mm=10.0)
        
        assert mesh.is_valid
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0
        
        # Check mesh bounds
        bounds = mesh.bounds
        assert bounds[2, 1] >= 9.5  # Z-max should be close to 10 mm


def test_geometry_packing():
    """Test that bundles don't overlap in ring arrangement."""
    geom = StemGeometry(stem_radius_mm=1.0)
    geom.generate_dicot_ring(
        xylem_diameter_um=100.0,
        phloem_diameter_um=80.0,
        n_bundles=8
    )
    
    # Check no bundles overlap
    for i, bundle1 in enumerate(geom.bundles):
        for j, bundle2 in enumerate(geom.bundles[i+1:], start=i+1):
            dx = bundle1.center[0] - bundle2.center[0]
            dy = bundle1.center[1] - bundle2.center[1]
            dist = np.sqrt(dx**2 + dy**2)
            min_dist = bundle1.xylem_radius + bundle2.xylem_radius
            
            # Should have some spacing
            assert dist > min_dist * 0.5


def test_geometry_reproducibility():
    """Test that geometry generation is reproducible with same seed."""
    geom1 = StemGeometry(stem_radius_mm=2.0)
    geom1.generate_monocot_scattered(40.0, 20.0, n_bundles=10, seed=42)
    
    geom2 = StemGeometry(stem_radius_mm=2.0)
    geom2.generate_monocot_scattered(40.0, 20.0, n_bundles=10, seed=42)
    
    # Check positions match
    for b1, b2 in zip(geom1.bundles, geom2.bundles):
        assert abs(b1.center[0] - b2.center[0]) < 1e-10
        assert abs(b1.center[1] - b2.center[1]) < 1e-10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
