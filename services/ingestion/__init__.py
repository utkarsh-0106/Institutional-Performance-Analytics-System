"""Indian higher-education data source ingestion."""
from services.ingestion.aishe import AISHEIngestion
from services.ingestion.naac import NAACIngestion
from services.ingestion.nirf import NIRFIngestion
from services.ingestion.ugc import UGCIngestion

__all__ = ["NIRFIngestion", "AISHEIngestion", "NAACIngestion", "UGCIngestion"]
