"""
Connect to the Minio object store.
"""
from minio import Minio
from nunaserver import settings

storage = Minio(
    settings.MINIO_URL,
    access_key=settings.MINIO_ACCESS,
    secret_key=settings.MINIO_SECRET,
    secure=settings.MINIO_SECURE
)
