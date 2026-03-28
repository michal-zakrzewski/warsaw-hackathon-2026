"""Google Satellite Embedding (AlphaEarth Foundations) connector via Earth Engine."""

from satellite_embedding.connector import (
    BANDS,
    COLLECTION_ID,
    embedding_image,
    init,
    mean_embedding_in_bbox,
    sample_point,
)

__all__ = [
    "BANDS",
    "COLLECTION_ID",
    "embedding_image",
    "init",
    "mean_embedding_in_bbox",
    "sample_point",
]
