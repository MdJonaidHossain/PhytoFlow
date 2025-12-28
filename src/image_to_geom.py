"""Image-to-geometry pipeline for creating digital twins from microscopy."""

import numpy as np
from typing import Tuple, Dict, List
import warnings

# Lazy imports for heavy dependencies
def _import_cv2():
    """Lazy import opencv (only when image processing needed)."""
    import cv2
    return cv2

def _import_skimage():
    """Lazy import scikit-image (only when image processing needed)."""
    from skimage import filters, measure, morphology, segmentation
    from skimage.feature import peak_local_max
    return filters, measure, morphology, segmentation, peak_local_max

def _import_scipy_ndi():
    """Lazy import scipy.ndimage (only when image processing needed)."""
    from scipy import ndimage as ndi
    return ndi


class ImageToGeometry:
    """Convert microscopy images to vascular geometry."""
    
    def __init__(self):
        self.original_image = None
        self.processed_image = None
        self.binary_mask = None
        self.labeled_regions = None
        self.detected_bundles = []
    
    def load_image(self, image_path: str) -> np.ndarray:
        """
        Load microscopy image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Grayscale image array
        """
        cv2 = _import_cv2()
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        self.original_image = img
        
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        return gray
    
    def preprocess(self, image: np.ndarray, blur_sigma: float = 1.0,
                  clahe: bool = True) -> np.ndarray:
        """
        Preprocess image to enhance features.
        
        Args:
            image: Input grayscale image
            blur_sigma: Gaussian blur sigma
            clahe: Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        
        Returns:
            Preprocessed image
        """
        cv2 = _import_cv2()
        # Gaussian blur to reduce noise
        if blur_sigma > 0:
            image = cv2.GaussianBlur(image, (0, 0), blur_sigma)
        
        # CLAHE for contrast enhancement
        if clahe:
            clahe_obj = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            image = clahe_obj.apply(image)
        
        self.processed_image = image
        return image
    
    def segment_threshold(self, image: np.ndarray, method: str = 'otsu',
                         block_size: int = 35, offset: float = 0) -> np.ndarray:
        """
        Segment image using thresholding.
        
        Args:
            image: Preprocessed grayscale image
            method: 'otsu', 'adaptive', 'manual', or 'multiotsu'
            block_size: Block size for adaptive thresholding
            offset: Offset for adaptive threshold
        
        Returns:
            Binary mask
        """
        filters, _, _, _, _ = _import_skimage()
        
        if method == 'otsu':
            threshold = filters.threshold_otsu(image)
            binary = image > threshold
        
        elif method == 'multiotsu':
            thresholds = filters.threshold_multiotsu(image, classes=3)
            # Use highest threshold to get darkest regions (vessels)
            binary = image < thresholds[0]
        
        elif method == 'adaptive':
            threshold = filters.threshold_local(image, block_size=block_size, offset=offset)
            binary = image > threshold
        
        elif method == 'manual':
            threshold = np.mean(image)
            binary = image > threshold
        
        else:
            raise ValueError(f"Unknown segmentation method: {method}")
        
        self.binary_mask = binary
        return binary
    
    def segment_watershed(self, image: np.ndarray, min_distance: int = 10) -> np.ndarray:
        """
        Segment image using watershed algorithm (better for touching objects).
        
        Args:
            image: Preprocessed grayscale image
            min_distance: Minimum distance between peaks
        
        Returns:
            Labeled segmentation mask
        """
        filters, measure, _, segmentation, peak_local_max = _import_skimage()
        ndi = _import_scipy_ndi()
        
        # Apply thresholding
        threshold = filters.threshold_otsu(image)
        binary = image > threshold
        
        # Distance transform
        distance = ndi.distance_transform_edt(binary)
        
        # Find peaks (local maxima)
        local_max = peak_local_max(distance, min_distance=min_distance, 
                                   labels=binary, indices=False)
        
        # Create markers
        markers = measure.label(local_max)
        
        # Watershed
        labels = segmentation.watershed(-distance, markers, mask=binary)
        
        self.labeled_regions = labels
        return labels
    
    def clean_mask(self, binary: np.ndarray, min_size: int = 50,
                   max_size: int = 10000, fill_holes: bool = True) -> np.ndarray:
        """
        Clean binary mask with morphological operations.
        
        Args:
            binary: Binary mask
            min_size: Minimum object size in pixels
            max_size: Maximum object size in pixels
            fill_holes: Fill holes in objects
        
        Returns:
            Cleaned binary mask
        """
        _, measure, morphology, _, _ = _import_skimage()
        
        # Remove small objects
        cleaned = morphology.remove_small_objects(binary, min_size=min_size)
        
        # Remove large objects (likely artifacts)
        labeled = measure.label(cleaned)
        props = measure.regionprops(labeled)
        for prop in props:
            if prop.area > max_size:
                cleaned[labeled == prop.label] = False
        
        # Fill holes
        if fill_holes:
            cleaned = morphology.remove_small_holes(cleaned, area_threshold=min_size)
        
        # Morphological closing to smooth boundaries
        cleaned = morphology.binary_closing(cleaned, morphology.disk(2))
        
        self.binary_mask = cleaned
        return cleaned
    
    def extract_bundles(self, binary_or_labeled: np.ndarray, 
                       pixels_per_mm: float = 100.0,
                       is_labeled: bool = False) -> List[Dict]:
        """
        Extract vascular bundle properties from segmented image.
        
        Args:
            binary_or_labeled: Binary mask or labeled image
            pixels_per_mm: Calibration factor
            is_labeled: Whether input is labeled (watershed) or binary
        
        Returns:
            List of bundle dictionaries
        """
        _, measure, _, _, _ = _import_skimage()
        
        if is_labeled:
            labeled = binary_or_labeled
        else:
            labeled = measure.label(binary_or_labeled)
        
        regions = measure.regionprops(labeled)
        
        bundles = []
        img_height, img_width = labeled.shape
        
        for region in regions:
            # Get centroid in mm coordinates (origin at center)
            cy, cx = region.centroid
            x_mm = (cx - img_width / 2) / pixels_per_mm
            y_mm = (img_height / 2 - cy) / pixels_per_mm  # Flip y-axis
            
            # Estimate radius from area (assume circular)
            radius_mm = np.sqrt(region.area / np.pi) / pixels_per_mm
            
            # Eccentricity (0 = circle, 1 = line)
            eccentricity = region.eccentricity
            
            # Orientation
            orientation = region.orientation
            
            bundle = {
                'center_x': x_mm,
                'center_y': y_mm,
                'radius_mm': radius_mm,
                'area_mm2': region.area / (pixels_per_mm ** 2),
                'eccentricity': eccentricity,
                'orientation_rad': orientation,
                'bbox': region.bbox  # (min_row, min_col, max_row, max_col)
            }
            
            bundles.append(bundle)
        
        self.detected_bundles = bundles
        return bundles
    
    def classify_bundles(self, bundles: List[Dict], 
                        xylem_phloem_ratio: float = 0.6) -> List[Dict]:
        """
        Classify detected regions as xylem or phloem.
        
        Simple heuristic: larger regions are xylem, smaller nearby regions are phloem.
        
        Args:
            bundles: List of bundle dictionaries
            xylem_phloem_ratio: Phloem radius as fraction of xylem radius
        
        Returns:
            Updated bundle list with classifications
        """
        # Sort by size (largest first)
        bundles_sorted = sorted(bundles, key=lambda b: b['area_mm2'], reverse=True)
        
        classified = []
        for bundle in bundles_sorted:
            # Assume larger regions are xylem
            classified.append({
                **bundle,
                'xylem_radius': bundle['radius_mm'],
                'phloem_radius': bundle['radius_mm'] * xylem_phloem_ratio,
                'tissue_type': 'vascular_bundle'
            })
        
        return classified
    
    def bundle_statistics(self, bundles: List[Dict]) -> Dict:
        """
        Calculate statistics on detected bundles.
        
        Args:
            bundles: List of bundle dictionaries
        
        Returns:
            Statistics dictionary
        """
        if not bundles:
            return {
                'n_bundles': 0,
                'mean_radius_mm': 0,
                'std_radius_mm': 0,
                'total_area_mm2': 0
            }
        
        radii = [b['radius_mm'] for b in bundles]
        areas = [b['area_mm2'] for b in bundles]
        
        return {
            'n_bundles': len(bundles),
            'mean_radius_mm': np.mean(radii),
            'std_radius_mm': np.std(radii),
            'min_radius_mm': np.min(radii),
            'max_radius_mm': np.max(radii),
            'total_area_mm2': np.sum(areas),
            'mean_area_mm2': np.mean(areas)
        }
    
    def to_geometry_format(self, bundles: List[Dict]) -> Dict:
        """
        Convert detected bundles to format compatible with StemGeometry.
        
        Args:
            bundles: List of classified bundle dictionaries
        
        Returns:
            Geometry data dictionary
        """
        geometry_bundles = []
        
        for bundle in bundles:
            geometry_bundles.append({
                'center_x': bundle['center_x'],
                'center_y': bundle['center_y'],
                'xylem_radius': bundle.get('xylem_radius', bundle['radius_mm']),
                'phloem_radius': bundle.get('phloem_radius', bundle['radius_mm'] * 0.6),
                'type': 'detected'
            })
        
        # Estimate stem radius from bundle positions
        if bundles:
            max_dist = max(np.sqrt(b['center_x']**2 + b['center_y']**2) + b['radius_mm'] 
                          for b in bundles)
            stem_radius = max_dist * 1.2  # Add 20% margin
        else:
            stem_radius = 1.0
        
        return {
            'stem': {
                'radius': stem_radius,
                'arrangement': 'image_based'
            },
            'bundles': geometry_bundles
        }
