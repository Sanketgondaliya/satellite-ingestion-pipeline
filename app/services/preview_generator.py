from osgeo import gdal
from PIL import Image
import numpy as np
import io
import boto3
from config import S3_PREVIEW_BUCKET

def generate_thumbnail(cog_path: str, size: tuple = (256, 256)) -> bytes:
    """Generate thumbnail JPEG from COG using GDAL + PIL.
    Supports RGB (3+ bands) and single-band (grayscale) files.
    """
    ds = gdal.Open(cog_path)
    if ds is None:
        raise ValueError(f"Could not open file: {cog_path}")

    if ds.RasterCount >= 3:
        # RGB thumbnail from first 3 bands
        r = ds.GetRasterBand(1).ReadAsArray()
        g = ds.GetRasterBand(2).ReadAsArray()
        b = ds.GetRasterBand(3).ReadAsArray()
        rgb = np.stack([r, g, b], axis=-1)
        # Scale to 0-255
        mn, mx = rgb.min(), rgb.max()
        if mx > mn:
            rgb = ((rgb - mn) / (mx - mn) * 255).astype(np.uint8)
        else:
            rgb = np.zeros_like(rgb, dtype=np.uint8)
        img = Image.fromarray(rgb, mode="RGB")
    else:
        # Single-band grayscale thumbnail
        band_data = ds.GetRasterBand(1).ReadAsArray()
        mn, mx = band_data.min(), band_data.max()
        if mx > mn:
            gray = ((band_data - mn) / (mx - mn) * 255).astype(np.uint8)
        else:
            gray = np.zeros_like(band_data, dtype=np.uint8)
        img = Image.fromarray(gray, mode="L").convert("RGB")

    img.thumbnail(size, Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()

import os
import boto3

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "satleo-satellite-data")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY

from botocore.config import Config

def upload_thumbnail_to_s3(image_bytes: bytes, dataset_id: str) -> str:
    s3 = boto3.client(
        's3',
        region_name="ap-south-2",
        endpoint_url="https://s3.ap-south-2.amazonaws.com",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        config=Config(signature_version='s3v4')
    )
    key = f"previews/{dataset_id}.jpg"
    s3.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=image_bytes, ContentType="image/jpeg")
    presigned_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET_NAME, 'Key': key},
        ExpiresIn=43200  # 12 hours
    )
    return presigned_url