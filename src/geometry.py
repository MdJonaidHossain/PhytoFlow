"""Geometry generation: parametric, AI image-based, and 3D export for PhytoFlow."""

import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import trimesh
from typing import List, Dict, Tuple, Optional
import cv2
from skimage import filters, measure, morphology
from scipy.spatial import Voronoi


class VascularBundle:
    """Represents a single vascular bundle (xylem + phloem)."""
    
    def __init__(self, center: Tuple[float, float], xylem_radius: float, 
                 phloem_radius: float, bundle_type: str = "collateral"):
        self.center = center
        self.xylem_radius = xylem_radius
        self.phloem_radius = phloem_radius
        self.bundle_type = bundle_type
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'center': self.center,
            'xylem_radius': self.xylem_radius,
            'phloem_radius': self.phloem_radius,
            'type': self.bundle_type
        }


class StemGeometry:
    """Digital anatomist: generates and manages stem cross-section geometry."""
    
    def __init__(self, stem_radius_mm: float = 1.0):
        self.stem_radius_mm = stem_radius_mm
        self.bundles: List[VascularBundle] = []
        self.arrangement = "dicot"  # or "monocot"
    
    def generate_dicot_ring(self, xylem_diameter_um: float, phloem_diameter_um: float,
                           n_bundles: int = 8) -> None:
        """
        Generate vascular bundles in a ring arrangement (Dicot like Arabidopsis).
        
        Args:
            xylem_diameter_um: Xylem vessel diameter in micrometers
            phloem_diameter_um: Phloem sieve element diameter in micrometers
            n_bundles: Number of bundles in the ring
        """
        self.arrangement = "dicot"
        self.bundles = []
        
        # Convert to mm
        xylem_radius = (xylem_diameter_um / 2.0) / 1000.0
        phloem_radius = (phloem_diameter_um / 2.0) / 1000.0
        
        # Place bundles in a ring at ~70% of stem radius
        ring_radius = self.stem_radius_mm * 0.7
        
        for i in range(n_bundles):
            angle = 2 * np.pi * i / n_bundles
            x = ring_radius * np.cos(angle)
            y = ring_radius * np.sin(angle)
            
            bundle = VascularBundle(
                center=(x, y),
                xylem_radius=xylem_radius,
                phloem_radius=phloem_radius,
                bundle_type="collateral"
            )
            self.bundles.append(bundle)
    
    def generate_monocot_scattered(self, xylem_diameter_um: float, 
                                   phloem_diameter_um: float,
                                   n_bundles: int = 15, seed: int = 42) -> None:
        """
        Generate scattered vascular bundles (Monocot like Maize/Rice).
        
        Args:
            xylem_diameter_um: Xylem vessel diameter in micrometers
            phloem_diameter_um: Phloem sieve element diameter in micrometers
            n_bundles: Number of bundles
            seed: Random seed for reproducibility
        """
        self.arrangement = "monocot"
        self.bundles = []
        
        np.random.seed(seed)
        
        # Convert to mm
        xylem_radius = (xylem_diameter_um / 2.0) / 1000.0
        phloem_radius = (phloem_diameter_um / 2.0) / 1000.0
        
        # Generate random positions within stem, avoiding edge
        usable_radius = self.stem_radius_mm * 0.85
        
        for _ in range(n_bundles):
            # Polar coordinates for more uniform distribution
            r = np.sqrt(np.random.random()) * usable_radius
            theta = np.random.random() * 2 * np.pi
            
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            
            bundle = VascularBundle(
                center=(x, y),
                xylem_radius=xylem_radius,
                phloem_radius=phloem_radius,
                bundle_type="scattered"
            )
            self.bundles.append(bundle)
    
    def from_image(self, image_path: str, threshold_method: str = 'otsu',
                   min_area_pixels: int = 50) -> None:
        """
        Create digital twin from microscopy image using AI image processing.
        
        Args:
            image_path: Path to microscopy image
            threshold_method: 'otsu', 'adaptive', or 'manual'
            min_area_pixels: Minimum area to consider as a bundle
        """
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        if threshold_method == 'otsu':
            threshold_value = filters.threshold_otsu(gray)
            binary = gray > threshold_value
        elif threshold_method == 'adaptive':
            binary = filters.threshold_local(gray, block_size=35)
            binary = gray > binary
        else:
            threshold_value = np.mean(gray)
            binary = gray > threshold_value
        
        # Clean up with morphological operations
        binary = morphology.remove_small_objects(binary, min_size=min_area_pixels)
        binary = morphology.remove_small_holes(binary, area_threshold=min_area_pixels)
        
        # Label connected components
        labels = measure.label(binary)
        regions = measure.regionprops(labels)
        
        # Convert detected regions to bundles
        self.bundles = []
        img_height, img_width = gray.shape
        
        # Assume image shows full stem diameter
        pixels_per_mm = img_width / (2 * self.stem_radius_mm)
        
        for region in regions:
            if region.area >= min_area_pixels:
                # Get centroid in mm coordinates (origin at center)
                cy, cx = region.centroid
                x_mm = (cx - img_width / 2) / pixels_per_mm
                y_mm = (img_height / 2 - cy) / pixels_per_mm  # Flip y-axis
                
                # Estimate radius from area
                radius_mm = np.sqrt(region.area / np.pi) / pixels_per_mm
                
                # Assume detected bundles contain both xylem and phloem
                # Split radius between them (simplified)
                xylem_radius = radius_mm * 0.6
                phloem_radius = radius_mm * 0.4
                
                bundle = VascularBundle(
                    center=(x_mm, y_mm),
                    xylem_radius=xylem_radius,
                    phloem_radius=phloem_radius,
                    bundle_type="detected"
                )
                self.bundles.append(bundle)
        
        self.arrangement = "image_based"
    
    def get_cross_section_data(self) -> Dict:
        """
        Get cross-section data for visualization.
        
        Returns dictionary with stem and bundle information.
        """
        data = {
            'stem': {
                'radius': self.stem_radius_mm,
                'arrangement': self.arrangement
            },
            'bundles': []
        }
        
        for bundle in self.bundles:
            data['bundles'].append({
                'center_x': bundle.center[0],
                'center_y': bundle.center[1],
                'xylem_radius': bundle.xylem_radius,
                'phloem_radius': bundle.phloem_radius,
                'type': bundle.bundle_type
            })
        
        return data
    
    def to_shapely_polygons(self) -> Tuple[Polygon, List[Polygon], List[Polygon]]:
        """
        Convert geometry to Shapely polygons for export and computation.
        
        Returns:
            (stem_polygon, xylem_polygons, phloem_polygons)
        """
        # Stem outline
        stem = Point(0, 0).buffer(self.stem_radius_mm)
        
        # Vascular bundles
        xylem_polygons = []
        phloem_polygons = []
        
        for bundle in self.bundles:
            center = Point(bundle.center)
            xylem = center.buffer(bundle.xylem_radius)
            phloem = center.buffer(bundle.phloem_radius)
            
            xylem_polygons.append(xylem)
            phloem_polygons.append(phloem)
        
        return stem, xylem_polygons, phloem_polygons
    
    def extrude_to_3d(self, length_mm: float = 10.0, resolution: int = 32) -> trimesh.Trimesh:
        """
        Extrude 2D cross-section to 3D mesh for STL/OBJ export.
        
        Args:
            length_mm: Length of extruded stem
            resolution: Number of points around circles
        
        Returns:
            Trimesh object ready for export
        """
        stem, xylem_polygons, phloem_polygons = self.to_shapely_polygons()
        
        # Create 2D path from stem outline
        coords = np.array(stem.exterior.coords)
        
        # Extrude by creating vertices at two z-levels
        vertices = []
        faces = []
        
        n_points = len(coords) - 1  # Exclude duplicate closing point
        
        # Add vertices for bottom and top
        for z in [0, length_mm]:
            for i in range(n_points):
                x, y = coords[i]
                vertices.append([x, y, z])
        
        # Create faces for side walls
        for i in range(n_points):
            next_i = (i + 1) % n_points
            
            # Two triangles per rectangular face
            v0 = i
            v1 = next_i
            v2 = i + n_points
            v3 = next_i + n_points
            
            faces.append([v0, v1, v2])
            faces.append([v1, v3, v2])
        
        # Create caps (bottom and top)
        # Bottom cap
        bottom_center_idx = len(vertices)
        vertices.append([0, 0, 0])
        for i in range(n_points):
            next_i = (i + 1) % n_points
            faces.append([bottom_center_idx, next_i, i])
        
        # Top cap
        top_center_idx = len(vertices)
        vertices.append([0, 0, length_mm])
        for i in range(n_points):
            next_i = (i + 1) % n_points
            faces.append([top_center_idx, i + n_points, next_i + n_points])
        
        mesh = trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces))
        
        # Ensure mesh is valid
        mesh.remove_degenerate_faces()
        mesh.remove_duplicate_faces()
        mesh.remove_unreferenced_vertices()
        
        return mesh
    
    def check_printability(self, min_feature_size_mm: float = 0.1) -> Tuple[bool, List[str]]:
        """
        Check if geometry is suitable for 3D printing.
        
        Args:
            min_feature_size_mm: Minimum printable feature size
        
        Returns:
            (is_printable, list_of_warnings)
        """
        warnings = []
        is_printable = True
        
        # Check bundle sizes
        for i, bundle in enumerate(self.bundles):
            if bundle.xylem_radius * 2 < min_feature_size_mm:
                warnings.append(f"⚠️ Bundle {i}: xylem diameter "
                              f"({bundle.xylem_radius*2:.3f} mm) below printable minimum "
                              f"({min_feature_size_mm} mm)")
                is_printable = False
            
            if bundle.phloem_radius * 2 < min_feature_size_mm:
                warnings.append(f"⚠️ Bundle {i}: phloem diameter "
                              f"({bundle.phloem_radius*2:.3f} mm) below printable minimum "
                              f"({min_feature_size_mm} mm)")
                is_printable = False
        
        # Check bundle spacing
        for i, bundle1 in enumerate(self.bundles):
            for j, bundle2 in enumerate(self.bundles[i+1:], start=i+1):
                dist = np.sqrt((bundle1.center[0] - bundle2.center[0])**2 +
                             (bundle1.center[1] - bundle2.center[1])**2)
                min_dist = bundle1.xylem_radius + bundle2.xylem_radius + min_feature_size_mm
                
                if dist < min_dist:
                    warnings.append(f"⚠️ Bundles {i} and {j} too close "
                                  f"({dist:.3f} mm, need {min_dist:.3f} mm)")
                    is_printable = False
        
        return is_printable, warnings
    
    def export_stl(self, filepath: str, length_mm: float = 10.0) -> None:
        """Export geometry as STL file for 3D printing."""
        mesh = self.extrude_to_3d(length_mm=length_mm)
        mesh.export(filepath, file_type='stl')
    
    def export_obj(self, filepath: str, length_mm: float = 10.0) -> None:
        """Export geometry as OBJ file."""
        mesh = self.extrude_to_3d(length_mm=length_mm)
        mesh.export(filepath, file_type='obj')
