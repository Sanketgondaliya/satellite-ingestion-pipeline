from geoserver.catalog import Catalog
from config import GEOSERVER_URL, GEOSERVER_USER, GEOSERVER_PASSWORD

def publish_cog_to_geoserver(cog_url: str, layer_name: str, workspace: str = "satleo"):
    """Publish a COG file (already on S3) to GeoServer using its S3 GeoTIFF store."""
    cat = Catalog(GEOSERVER_URL + "/rest", GEOSERVER_USER, GEOSERVER_PASSWORD)
    
    # Ensure workspace exists
    ws = cat.get_workspace(workspace)
    if not ws:
        ws = cat.create_workspace(workspace, f"http://{workspace}")
    
    # Create coverage store (S3 GeoTIFF requires plugin)
    store_name = f"{layer_name}_store"
    store = cat.create_coveragestore(
        store_name,
        cog_url,
        workspace=ws,
        type="GeoTIFF"
    )
    
    # Publish layer
    layer = cat.publish_layer(store)
    return f"{GEOSERVER_URL}/{workspace}/wms?layers={layer_name}"