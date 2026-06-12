from osgeo import gdal, osr
import json
import subprocess
import os

# Point to the correct PROJ data
PROJ_DATA_PATH = r"C:\Users\BAPS\AppData\Local\Programs\Python\Python311\Lib\site-packages\osgeo\data\proj"
os.environ["PROJ_DATA"] = PROJ_DATA_PATH
os.environ["PROJ_LIB"] = PROJ_DATA_PATH

def extract_metadata(tif_path: str) -> dict:
    """Extract metadata using gdalinfo (JSON output).
    Always returns spatial_coverage and bounds in EPSG:4326.
    """
    env = os.environ.copy()
    env["PROJ_DATA"] = PROJ_DATA_PATH
    env["PROJ_LIB"] = PROJ_DATA_PATH
    
    cmd = ["gdalinfo", "-json", tif_path]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise Exception(f"gdalinfo failed: {result.stderr}")
    
    info = json.loads(result.stdout)
    
    geo_transform = info.get("geoTransform")
    
    # Extract bounds and WKT — always in EPSG:4326
    wgs84_extent = info.get("wgs84Extent")
    spatial_coverage_wkt = None
    bounds = None
    
    if wgs84_extent and wgs84_extent.get("type") == "Polygon":
        # gdalinfo already provides wgs84Extent in EPSG:4326
        coords = wgs84_extent["coordinates"][0]
        wkt_coords = ", ".join([f"{lon} {lat}" for lon, lat in coords])
        spatial_coverage_wkt = f"POLYGON(({wkt_coords}))"
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
    elif geo_transform:
        # Fallback: compute corners from geoTransform and reproject to 4326
        min_x = geo_transform[0]
        max_y = geo_transform[3]
        max_x = min_x + geo_transform[1] * info["size"][0]
        min_y = max_y + geo_transform[5] * info["size"][1]
        
        # Reproject corners from source CRS to EPSG:4326
        source_wkt = info.get("coordinateSystem", {}).get("wkt", "")
        if source_wkt:
            source_srs = osr.SpatialReference()
            source_srs.ImportFromWkt(source_wkt)
            
            target_srs = osr.SpatialReference()
            target_srs.ImportFromEPSG(4326)
            target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            source_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            
            transform = osr.CoordinateTransformation(source_srs, target_srs)
            
            # Transform all 4 corners
            corners = [
                (min_x, min_y),
                (max_x, min_y),
                (max_x, max_y),
                (min_x, max_y),
                (min_x, min_y)  # close the ring
            ]
            
            transformed = []
            for x, y in corners:
                lon, lat, _ = transform.TransformPoint(x, y)
                transformed.append((lon, lat))
            
            wkt_coords = ", ".join([f"{lon} {lat}" for lon, lat in transformed])
            spatial_coverage_wkt = f"POLYGON(({wkt_coords}))"
            
            lons = [c[0] for c in transformed]
            lats = [c[1] for c in transformed]
            bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
        else:
            # No CRS info — store raw (best effort)
            bounds = [[min_y, min_x], [max_y, max_x]]
            spatial_coverage_wkt = f"POLYGON(({min_x} {min_y}, {max_x} {min_y}, {max_x} {max_y}, {min_x} {max_y}, {min_x} {min_y}))"
    
    # Resolution
    resolution = abs(geo_transform[1]) if geo_transform else None
    
    # Cloud cover – if not present, default 0
    cloud_cover = info.get("metadata", {}).get("", {}).get("CLOUD_COVER", 0.0)
    
    return {
        "width": info["size"][0],
        "height": info["size"][1],
        "bands": info["bands"],
        "projection": info.get("coordinateSystem", {}).get("wkt", ""),
        "resolution_meters": resolution,
        "cloud_cover_pct": float(cloud_cover),
        "bounds": bounds,
        "spatial_coverage_wkt": spatial_coverage_wkt
    }