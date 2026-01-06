

from typing import Optional, List, Dict, Set, Tuple, cast, Any
from rsare.agents.agent.toolset_builder import agent_tool

class Database:

    def __init__(self):
        """
        Initialize with the path to the GeoPackage.
        """
        self.name = "database"

    
    @agent_tool
    def load_SAR_scenes(
            self,
            date1,
            date2,
            region: List[float] = None,
            satellite="S1AB",  # choice is S1A, S1B, or "S1AB"
            collection="COPERNICUS/S1_GRD",
    ):
        """Get Sentinel-1 SAR scenes over ocean areas within a specified date range.

        This function queries Google Earth Engine for Sentinel-1 GRD (Ground Range
        Detected) imagery that overlaps with specified ocean and region boundaries.
        The results are filtered to include only IW (Interferometric Wide) mode images
        with both VV and VH polarizations at high resolution.

        Args:
            date1 (str): Start date of the query range in "YYYY-MM-DD" format.
            date2 (str or None): End date of the query range in "YYYY-MM-DD" format.
                If None, defaults to date1 + 1 day.
            region: List of four floats defining the bounding box
                [lon_min, lat_min, lon_max, lat_max].
            satellite (str): Satellite identifier prefix to filter scenes
                by (e.g., "S1A" "S1B" "S1AB"). Defaults to "S1AB".
            collection (str, optional): Earth Engine image collection ID. Defaults
                to "COPERNICUS/S1_GRD".

        Returns:
            reply [str]: Message with the number of matching scenes, if any found.
        """
        return f"Loaded 10 scenes"