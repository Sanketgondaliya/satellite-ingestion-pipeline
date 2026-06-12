import os
import subprocess

# Point GDAL/PROJ to the correct proj.db bundled with the osgeo package
GDAL_DATA_PATH = r"C:\Users\BAPS\AppData\Local\Programs\Python\Python311\Lib\site-packages\osgeo\data\gdal"
PROJ_DATA_PATH = r"C:\Users\BAPS\AppData\Local\Programs\Python\Python311\Lib\site-packages\osgeo\data\proj"

os.environ["GDAL_DATA"] = GDAL_DATA_PATH
os.environ["PROJ_DATA"] = PROJ_DATA_PATH
os.environ["PROJ_LIB"] = PROJ_DATA_PATH

GDAL_TRANSLATE = r"C:\Users\BAPS\AppData\Local\Programs\Python\Python311\Lib\site-packages\osgeo\gdal_translate.exe"

def generate_cog(input_path: str, output_path: str) -> str:
    """
    Generate Cloud Optimized GeoTIFF using gdal_translate.
    Uses the user's proven command: RGB bands, 8-bit, JPEG compressed, tiled.
    """
    exe = GDAL_TRANSLATE if os.path.exists(GDAL_TRANSLATE) else "gdal_translate"
    
    cmd = [
        exe,
        input_path,
        output_path,
        "-b", "1", "-b", "2", "-b", "3",
        "-ot", "Byte",
        "-scale",
        "-of", "GTiff",
        "-co", "TILED=YES",
        "-co", "COMPRESS=JPEG",
        "-co", "JPEG_QUALITY=70",
        "-co", "BLOCKXSIZE=512",
        "-co", "BLOCKYSIZE=512"
    ]
    
    env = os.environ.copy()
    env["GDAL_DATA"] = GDAL_DATA_PATH
    env["PROJ_DATA"] = PROJ_DATA_PATH
    env["PROJ_LIB"] = PROJ_DATA_PATH
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    # If 3-band fails (single band file), fall back to single band
    if result.returncode != 0:
        cmd_single = [
            exe,
            input_path,
            output_path,
            "-b", "1",
            "-ot", "Byte",
            "-scale",
            "-of", "GTiff",
            "-co", "TILED=YES",
            "-co", "COMPRESS=JPEG",
            "-co", "JPEG_QUALITY=70",
            "-co", "BLOCKXSIZE=512",
            "-co", "BLOCKYSIZE=512"
        ]
        result = subprocess.run(cmd_single, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            raise Exception(f"COG generation failed: {result.stderr}")
    
    return output_path