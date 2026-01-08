"""
Global Fishing Watch (GFW) dataset
----
GFW dataset: https://globalfishingwatch.org/data-download/

We download infrastructure and vessel detections from 
January 2017 to October 2024. The ground truths (.csv files)
from GFW are organized as follows:

* Infrastructure detections (folder `infrastructure`): 
    - sar_fixed_infrastructure_202410.csv

* Vessel detections: (montly detections - folder `vessels`)
    - sar_vessel_detections_pipev20231026_201701.csv
    - sar_vessel_detections_pipev20231026_201702.csv
    ... 
    - sar_vessel_detections_pipev20231026_202409.csv
    - sar_vessel_detections_pipev20231026_202410.csv
"""

"""
Constants for SAR_ARE data paths
"""
from pathlib import Path

# Base data directory
DATA_BASE_DIR = Path("rsare/data/gma")

# Vessel detections directory (contains multiple CSV files by date)
VESSEL_DETECTIONS_DIR = DATA_BASE_DIR / "vessels"

# Infrastructure detections directory
INFRASTRUCTURE_DETECTIONS_DIR = DATA_BASE_DIR / "infrastructure"

# Default files (for backward compatibility)
DEFAULT_VESSEL_DETECTIONS_FILE = VESSEL_DETECTIONS_DIR / "sar_vessel_detections_pipev20231026_201808.csv"
DEFAULT_INFRASTRUCTURE_DETECTIONS_FILE = INFRASTRUCTURE_DETECTIONS_DIR / "sar_fixed_infrastructure_202410.csv"