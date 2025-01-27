import io
import os
import warnings

import polars as pl

from op_analytics.coreutils.logger import human_size, structlog

log = structlog.get_logger()
warnings.filterwarnings("ignore", message="Polars found a filename")

PROJECT_NAME = "oplabs-tools-data"
BUCKET_NAME = "oplabs-tools-data-sink"


_CLIENT = None
_BUCKET = None

_PATH_PREFIX = "op_analytics"


def init_client():
    """Idempotent client initialization.

    This function guarantess only one global instance of the storage.Client() exists.
    """
    global _CLIENT
    global _BUCKET

    if _CLIENT is None:
        from google.cloud import storage

        _CLIENT = storage.Client()
        _BUCKET = _CLIENT.bucket(BUCKET_NAME)
        log.info(f"Initialized GCS client for bucket=gs://{BUCKET_NAME}")


def gcs_upload(blob_path: str, content: bytes | str, prefix=None):
    """Uploads content to GCS."""
    init_client()

    if _BUCKET is None:
        raise RuntimeError("GCS was not properly initialized.")

    from google.cloud.storage import Blob

    key = os.path.join(prefix or _PATH_PREFIX, blob_path)
    blob: Blob = _BUCKET.blob(key)
    blob.upload_from_string(content)
    log.info(f"Wrote {human_size(len(content))} to gs://{_BUCKET.name}/{key}")


def gcs_upload_csv(blob_path: str, df: pl.DataFrame):
    buf = io.BytesIO()
    df.write_csv(buf)
    gcs_upload(blob_path, buf.getvalue())
