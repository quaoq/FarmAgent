from __future__ import annotations

from typing import Any

from rsare.agents.agent.toolset_builder import agent_tool
from rsare.apps.sar.sea_activity_tools import (
    SeaActivityDefaults,
    SeaActivityStates,
    SeaActivityToolState,
    SeaActivityTools,
)


class SAT_Data(SeaActivityTools):
    """
    Data tools for SAR-based sea activity workflow testing.

    This class contains tools for loading SAR scenes, optical scenes, AIS data,
    environmental rasters, static reference layers, and spatial boundary data.
    """

    def __init__(
        self,
        state: SeaActivityToolState | None = None,
        sat_defaults: SeaActivityDefaults | None = None,
    ):
        super().__init__(
            name="SAT_Data",
            state=state,
            sat_defaults=sat_defaults,
        )

    # -------------------------------------------------------------------------
    # Data tools
    # -------------------------------------------------------------------------

    @agent_tool
    def load_sar_scenes(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            collection: str = "COPERNICUS/S1_GRD",
            satellite: str = "S1AB",
            instrument_mode: str = "IW",
            polarizations_required: list[str] | None = None,
            resolution_metadata: str = "H",
            nominal_resolution_m: float = 20.0,
    ) -> dict[str, Any]:
        """
        Load and filter Sentinel-1 SAR scenes from Google Earth Engine.

        This tool selects Sentinel-1 GRD scenes that match the specified
        temporal, spatial, satellite, instrument mode, polarization, and
        resolution constraints. It is intended to provide the input scene
        list or image collection for downstream SAR detection, footprint
        generation, and composite construction workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the query period in ``YYYY-MM-DD`` format.
        date_end : str
            End date of the query period in ``YYYY-MM-DD`` format.
        region : list[float]
            Spatial region used to constrain the query as a bounding box:
            ``[lon_min, lat_min, lon_max, lat_max]``.
        collection : str, optional
            Google Earth Engine Sentinel-1 collection name. The expected value
            is typically ``"COPERNICUS/S1_GRD"``.
        satellite : str, optional
            Sentinel-1 platform selector, such as ``"S1A"``, ``"S1B"``, or
            a project-specific value indicating both satellites.
        instrument_mode : str, optional
            Sentinel-1 acquisition mode. The expected value for the paper
            workflow is ``"IW"``.
        polarizations_required : list[str] or None, optional
            Required polarization bands. The paper workflow requires both
            ``"VV"`` and ``"VH"``. If None, ``["VV", "VH"]`` is used.
        resolution_metadata : str, optional
            Earth Engine resolution metadata filter. The paper workflow uses
            high-resolution GRD scenes, typically represented as ``"H"``.
        nominal_resolution_m : float, optional
            Nominal working resolution in meters. The paper workflow uses
            approximately 20 m resolution.

        Returns
        -------
        dict
            A structured mock response indicating that the requested
            Sentinel-1 SAR scenes have been loaded.
        """
        tool_name = "load_sar_scenes"

        if polarizations_required is None:
            polarizations_required = list(
                self.sat_defaults.sentinel1_polarizations_required
            )

        scene_collection_id = (
            f"sar_scenes_{date_begin}_{date_end}_{satellite}_"
            f"{instrument_mode}_{resolution_metadata}"
        )

        generated = {
            "scene_collection": {
                "scene_collection_id": scene_collection_id,
                "collection": collection,
                "date_begin": date_begin,
                "date_end": date_end,
                "satellite": satellite,
                "instrument_mode": instrument_mode,
                "polarizations_required": polarizations_required,
                "resolution_metadata": resolution_metadata,
                "nominal_resolution_m": nominal_resolution_m,
                "region": region,
            }
        }

        completed_state = SeaActivityStates.SAR_SCENES_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Sentinel-1 SAR scenes from {collection} for {date_begin} to "
                f"{date_end} over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_optical_scenes(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            collection: str = "COPERNICUS/S2",
            satellite: str = "S2AB",
            bands: list[str] | None = None,
            resolution_m: int = 10,
    ) -> dict[str, Any]:
        """
        Load Sentinel-2 optical scenes for RGB and NIR imagery.

        This tool selects Sentinel-2 optical scenes from Google Earth Engine
        according to the requested temporal range, spatial region, satellite
        platforms, and spectral bands. By default, it loads the 10 m RGB and
        near-infrared bands used by downstream offshore infrastructure
        classification workflows.

        Parameters
        ----------
        collection : str
            Google Earth Engine Sentinel-2 collection name, such as
            ``"COPERNICUS/S2"``. The exact product should be verified against
            the paper or implementation.
        date_begin : str
            Start date of the query period in ``YYYY-MM-DD`` format.
        date_end : str
            End date of the query period in ``YYYY-MM-DD`` format.
        region : list[float]
            Spatial region used to constrain the query, such as a bounding box
            or Earth Engine geometry.
        satellite : str, optional
            Sentinel-2 platform selector, such as ``"S2A"``, ``"S2B"``, or ``S2AB``.
            a project-specific value indicating both satellites.
        bands : sequence of str, optional
            Sentinel-2 bands to load. The default RGB-NIR setup is
            ``["B4", "B3", "B2", "B8"]``, corresponding to red, green, blue,
            and near-infrared bands at 10 m resolution.
            Reference mapping of Sentinel-2 optical bands that may be used when
            extending the loading configuration. Common groups include:
            ``Blue: B2 (10 m)``, ``Green: B3 (10 m)``, ``Red: B4 (10 m)``,
            ``NIR: B8 (10 m)``, ``Red edge: B5/B6/B7/B8A (20 m)``,
            ``SWIR: B11/B12 (20 m)``, and atmospheric bands
            ``B1/B9/B10 (60 m)``.
        resolution_m : int, optional
            Nominal spatial resolution in meters for the selected bands. The
            default RGB and NIR bands are 10 m bands.

        Returns
        -------
        optical_scenes : object
            Selected Sentinel-2 optical scenes or an image collection containing
            the requested optical bands.

        Notes
        -----
        The paper workflow for offshore infrastructure classification uses
        RGB and NIR optical thumbnails. Red edge, SWIR, and atmospheric bands
        may be listed as available Sentinel-2 bands, but they should not be
        treated as default model inputs unless explicitly supported by the
        paper or implementation.

        This tool only loads Sentinel-2 optical imagery. It does not perform
        cloud masking, compositing, tile extraction, infrastructure
        classification, or SAR-optical data fusion.
        """
        tool_name = "load_optical_scenes"

        if satellite is None:
            satellite = self.sat_defaults.sentinel2_satellite

        if bands is None:
            bands = list(self.sat_defaults.sentinel2_rgb_nir_bands)

        optical_collection_id = (
            f"optical_scenes_{date_begin}_{date_end}_"
            f"{'_'.join(satellite)}_{resolution_m}m"
        )

        generated = {
            "optical_scenes": {
                "optical_collection_id": optical_collection_id,
                "collection": collection,
                "date_begin": date_begin,
                "date_end": date_end,
                "satellite_platforms": satellite,
                "bands": bands,
                "resolution_m": resolution_m,
                "region": region,
            }
        }

        completed_state = SeaActivityStates.OPTICAL_SCENES_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Sentinel-2 optical scenes from {collection} for {date_begin} "
                f"to {date_end} over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_ais_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            ais_source_table: str = "gfw_ais_pipeline_table",
    ) -> dict[str, Any]:
        """
        Load AIS vessel position records for a specified time and region.

        This tool loads AIS message records, typically from a preprocessed GFW
        AIS pipeline table, and filters them by temporal and spatial bounds.
        The resulting AIS records can be used by downstream AIS filtering,
        interpolation, and SAR-AIS matching workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the AIS query period in ``YYYY-MM-DD`` format.
        date_end : str
            End date of the AIS query period in ``YYYY-MM-DD`` format.
        region : list[float]
            Spatial bounding box used to filter AIS positions, typically in the
            form ``[lon_min, lat_min, lon_max, lat_max]``.
        ais_source_table : str, optional
            Source table containing AIS messages or pipeline-processed AIS
            records, such as a GFW AIS pipeline table.

        Returns
        -------
        ais_records : object
            AIS records filtered by date and region. Expected fields typically
            include vessel identifier, timestamp, longitude, latitude, speed,
            course, and segment identifier.

        Notes
        -----
        This tool only loads AIS records. It does not perform AIS interpolation
        to SAR acquisition time, SAR-AIS matching, vessel classification, or
        activity aggregation.
        """
        tool_name = "load_ais_data"

        generated = {
            "ais_records": {
                "ais_records_id": f"ais_records_{date_begin}_{date_end}",
                "date_begin": date_begin,
                "date_end": date_end,
                "region": region,
                "ais_source_table": ais_source_table,
                "mock_fields": [
                    "vessel_id",
                    "timestamp",
                    "longitude",
                    "latitude",
                    "speed",
                    "course",
                    "segment_id",
                ],
            }
        }

        completed_state = SeaActivityStates.AIS_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"AIS vessel position records from {ais_source_table} for "
                f"{date_begin} to {date_end} over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_chlorophyll_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            chlorophyll_source: str = "NASA Ocean Biology Processing Group",
    ) -> dict[str, Any]:
        """
        Load chlorophyll environmental raster data for a specified time and region.

        This tool loads chlorophyll-related oceanographic data from a specified
        source, such as NASA Ocean Biology Processing Group products, and
        filters the data by temporal and spatial bounds. The resulting
        chlorophyll rasters can be used as environmental inputs for downstream
        feature construction, fishing/non-fishing classification, or spatial
        analysis workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the chlorophyll query period in ``YYYY-MM-DD`` format.
        date_end : str
            End date of the chlorophyll query period in ``YYYY-MM-DD`` format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        chlorophyll_source : str, optional
            Data source or provider for chlorophyll products, such as NASA Ocean
            Biology Processing Group.

        Returns
        -------
        chlorophyll_data : object
            Chlorophyll raster data filtered by date and region.

        Notes
        -----
        This tool only loads chlorophyll data. It does not perform feature-stack
        construction, raster resampling, normalization, fishing/non-fishing
        classification, or temporal aggregation.
        """
        tool_name = "load_chlorophyll_data"

        generated = {
            "chlorophyll_data": {
                "chlorophyll_data_id": f"chlorophyll_data_{date_begin}_{date_end}",
                "date_begin": date_begin,
                "date_end": date_end,
                "region": region,
                "chlorophyll_source": chlorophyll_source,
            }
        }

        completed_state = SeaActivityStates.CHLOROPHYLL_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Chlorophyll data from {chlorophyll_source} for {date_begin} "
                f"to {date_end} over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_sea_surface_temperature_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            sst_source: str = "Copernicus Global Ocean Analysis and Forecast System",
    ) -> dict[str, Any]:
        """
        Load sea-surface temperature raster data for a specified time and region.

        This tool loads sea-surface temperature data from a specified ocean
        analysis or forecast source, such as the Copernicus Global Ocean
        Analysis and Forecast System, and filters the data by temporal and
        spatial bounds. The resulting SST rasters can be used as environmental
        inputs for downstream feature construction, fishing/non-fishing
        classification, or spatial analysis workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the sea-surface temperature query period in
            ``YYYY-MM-DD`` format.
        date_end : str
            End date of the sea-surface temperature query period in
            ``YYYY-MM-DD`` format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        sst_source : str, optional
            Data source or provider for sea-surface temperature products, such
            as the Copernicus Global Ocean Analysis and Forecast System.

        Returns
        -------
        sst_data : object
            Sea-surface temperature raster data filtered by date and region.

        Notes
        -----
        This tool only loads sea-surface temperature data. It does not perform
        feature-stack construction, raster resampling, normalization,
        fishing/non-fishing classification, or temporal aggregation.
        """
        tool_name = "load_sea_surface_temperature_data"

        generated = {
            "sea_surface_temperature_data": {
                "sea_surface_temperature_data_id": (
                    f"sea_surface_temperature_data_{date_begin}_{date_end}"
                ),
                "date_begin": date_begin,
                "date_end": date_end,
                "region": region,
                "sst_source": sst_source,
            }
        }

        completed_state = SeaActivityStates.SEA_SURFACE_TEMPERATURE_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Sea-surface temperature data from {sst_source} for "
                f"{date_begin} to {date_end} over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_ocean_current_speed_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            ocean_current_source: str = "Copernicus Global Ocean Analysis and Forecast System",
    ) -> dict[str, Any]:
        """
        Load ocean current speed raster data for a specified time and region.

        This tool loads ocean current speed data from a specified ocean analysis
        or forecast source, such as the Copernicus Global Ocean Analysis and
        Forecast System, and filters the data by temporal and spatial bounds.
        The resulting current-speed rasters can be used as environmental inputs
        for downstream feature construction, fishing/non-fishing classification,
        or spatial analysis workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the ocean current query period in ``YYYY-MM-DD``
            format.
        date_end : str
            End date of the ocean current query period in ``YYYY-MM-DD``
            format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        ocean_current_source : str, optional
            Data source or provider for ocean current products, such as the
            Copernicus Global Ocean Analysis and Forecast System.

        Returns
        -------
        ocean_current_speed_data : object
            Ocean current speed raster data filtered by date and region.

        Notes
        -----
        This tool only loads ocean current speed data. It does not compute
        derived current-speed features from vector components unless explicitly
        implemented, and it does not perform feature-stack construction, raster
        resampling, normalization, fishing/non-fishing classification, or
        temporal aggregation.
        """
        tool_name = "load_ocean_current_speed_data"

        generated = {
            "ocean_current_speed_data": {
                "ocean_current_speed_data_id": (
                    f"ocean_current_speed_data_{date_begin}_{date_end}"
                ),
                "date_begin": date_begin,
                "date_end": date_end,
                "region": region,
                "ocean_current_source": ocean_current_source,
            }
        }

        completed_state = SeaActivityStates.OCEAN_CURRENT_SPEED_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Ocean current speed data from {ocean_current_source} for "
                f"{date_begin} to {date_end} over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_distance_to_shore_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            distance_to_shore_source: str = "NASA OBPG/PacIOOS",
    ) -> dict[str, Any]:
        """
        Load distance-to-shore data for a specified spatial region.

        This tool loads distance-to-shore data from a specified source, such as
        NASA OBPG/PacIOOS products, and filters it by spatial bounds. The
        resulting distance-to-shore raster or lookup data can be used for
        environmental feature construction, coastal filtering, vessel activity
        analysis, or fishing/non-fishing classification workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the ocean current query period in ``YYYY-MM-DD``
            format.
        date_end : str
            End date of the ocean current query period in ``YYYY-MM-DD``
            format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        distance_to_shore_source : str, optional
            Data source or provider for distance-to-shore products, such as
            NASA OBPG/PacIOOS.

        Returns
        -------
        distance_to_shore_data : object
            Distance-to-shore raster or lookup data filtered by spatial region.

        Notes
        -----
        This tool only loads distance-to-shore data. It does not perform
        shoreline masking, SAR scene clipping, vessel detection, feature-stack
        construction, raster resampling, or temporal aggregation.
        """
        tool_name = "load_distance_to_shore_data"

        generated = {
            "distance_to_shore_data": {
                "distance_to_shore_data_id": "distance_to_shore_data",
                "region": region,
                "distance_to_shore_source": distance_to_shore_source,
                "date_begin": date_begin,
                "date_end": date_end,
            }
        }

        completed_state = SeaActivityStates.DISTANCE_TO_SHORE_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Distance-to-shore data from {distance_to_shore_source} "
                f"over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_distance_to_port_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            distance_to_port_source: str = "Global Fishing Watch",
    ) -> dict[str, Any]:
        """
        Load distance-to-port data for a specified spatial region.

        This tool loads distance-to-port data from a specified source, such as
        Global Fishing Watch products, and filters it by spatial bounds. The
        resulting distance-to-port raster or lookup data can be used for
        environmental feature construction, vessel activity analysis, port
        proximity filtering, or fishing/non-fishing classification workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the ocean current query period in ``YYYY-MM-DD``
            format.
        date_end : str
            End date of the ocean current query period in ``YYYY-MM-DD``
            format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        distance_to_port_source : str, optional
            Data source or provider for distance-to-port products, such as
            Global Fishing Watch.

        Returns
        -------
        distance_to_port_data : object
            Distance-to-port raster or lookup data filtered by spatial region.

        Notes
        -----
        This tool only loads distance-to-port data. It does not perform port
        proximity filtering, vessel detection, feature-stack construction,
        raster resampling, fishing/non-fishing classification, or temporal
        aggregation.
        """
        tool_name = "load_distance_to_port_data"

        generated = {
            "distance_to_port_data": {
                "distance_to_port_data_id": "distance_to_port_data",
                "region": region,
                "distance_to_port_source": distance_to_port_source,
                "date_begin": date_begin,
                "date_end": date_end,
            }
        }

        completed_state = SeaActivityStates.DISTANCE_TO_PORT_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Distance-to-port data from {distance_to_port_source} "
                f"over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_bathymetry_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            bathymetry_source: str = "GEBCO",
    ) -> dict[str, Any]:
        """
        Load bathymetry data for a specified spatial region.

        This tool loads bathymetry or seafloor elevation data from a specified
        source, such as GEBCO products, and filters it by spatial bounds. The
        resulting bathymetry raster can be used for environmental feature
        construction, fishing/non-fishing classification, spatial analysis, or
        marine context characterization.

        Parameters
        ----------
        date_begin : str
            Start date of the ocean current query period in ``YYYY-MM-DD``
            format.
        date_end : str
            End date of the ocean current query period in ``YYYY-MM-DD``
            format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        bathymetry_source : str, optional
            Data source or provider for bathymetry products, such as GEBCO.

        Returns
        -------
        bathymetry_data : object
            Bathymetry or seafloor elevation raster data filtered by spatial
            region.

        Notes
        -----
        This tool only loads bathymetry data. It does not perform depth
        sign conversion, raster resampling, feature-stack construction,
        fishing/non-fishing classification, or temporal aggregation.
        """
        tool_name = "load_bathymetry_data"

        generated = {
            "bathymetry_data": {
                "bathymetry_data_id": "bathymetry_data",
                "region": region,
                "bathymetry_source": bathymetry_source,
                "date_begin": date_begin,
                "date_end": date_end,
            }
        }

        completed_state = SeaActivityStates.BATHYMETRY_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Bathymetry data from {bathymetry_source} "
                f"over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_eez_boundaries(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            eez_source: str = "Marine Regions",
    ) -> dict[str, Any]:
        """
        Load Exclusive Economic Zone (EEZ) boundary polygons for a spatial region.

        This tool loads EEZ boundary data from a specified source, such as
        Marine Regions, and filters the boundary polygons by spatial bounds.
        The resulting EEZ geometries can be used for downstream spatial joins,
        jurisdictional attribution, regional aggregation, or activity analysis.

        Parameters
        ----------
        date_begin : str
            Start date of the ocean current query period in ``YYYY-MM-DD``
            format.
        date_end : str
            End date of the ocean current query period in ``YYYY-MM-DD``
            format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        eez_source : str, optional
            Data source or provider for EEZ boundary data, such as Marine
            Regions.

        Returns
        -------
        eez_boundaries : object
            EEZ boundary polygons filtered by spatial region.

        Notes
        -----
        This tool only loads EEZ boundary geometries. It does not perform
        spatial joins, country attribution, vessel detection, activity
        aggregation, or temporal analysis.
        """
        tool_name = "load_eez_boundaries"

        generated = {
            "eez_boundaries": {
                "eez_boundaries_id": "eez_boundaries",
                "region": region,
                "eez_source": eez_source,
                "date_begin": date_begin,
                "date_end": date_end,
            }
        }

        completed_state = SeaActivityStates.EEZ_BOUNDARIES_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"EEZ boundary polygons from {eez_source} "
                f"over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_infrastructure_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            infrastructure_sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Load and standardize offshore infrastructure reference data.

        This tool loads offshore infrastructure reference or ground-truth data
        from one or more authoritative sources and filters the records by
        spatial bounds and, when applicable, temporal constraints. The loaded
        records can be standardized into a common schema for downstream
        infrastructure labeling, model training, validation, or spatial
        alignment workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the ocean current query period in ``YYYY-MM-DD``
            format.
        date_end : str
            End date of the ocean current query period in ``YYYY-MM-DD``
            format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        infrastructure_sources : sequence of str, optional
            Source datasets or agencies providing offshore infrastructure
            reference data, such as the Bureau of Ocean Energy Management, UK
            Hydrographic Office, California Department of Fish and Wildlife, or
            Geoscience Australia.

        Returns
        -------
        infrastructure_reference_data : object
            Standardized offshore infrastructure reference records, points, or
            polygons filtered by region and optional temporal constraints.

        Notes
        -----
        This tool only loads and standardizes offshore infrastructure reference
        or ground-truth data. It does not run SAR detection, create SAR or
        optical thumbnails, train the infrastructure classifier, perform model
        inference, or classify detected objects.
        """
        tool_name = "load_infrastructure_data"

        if infrastructure_sources is None:
            infrastructure_sources = list(self.sat_defaults.infrastructure_sources)

        generated = {
            "infrastructure_reference_data": {
                "infrastructure_reference_data_id": "infrastructure_reference_data",
                "date_begin": date_begin,
                "date_end": date_end,
                "region": region,
                "infrastructure_sources": infrastructure_sources,
            }
        }

        completed_state = SeaActivityStates.INFRASTRUCTURE_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Offshore infrastructure reference data from "
                f"{infrastructure_sources} over region {region} have been loaded "
                "and standardized."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_synthetic_shoreline_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            shoreline_source: str = "synthetic_shoreline_sources",
    ) -> dict[str, Any]:
        """
        Load synthetic shoreline data for a specified spatial region.

        This tool loads synthetic shoreline data from one or more shoreline or
        coastline sources and filters it by spatial bounds. The resulting
        shoreline geometry or raster can be used by downstream coastal masking,
        shoreline-buffer filtering, water-mask construction, or SAR detection
        area filtering workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the ocean current query period in ``YYYY-MM-DD``
            format.
        date_end : str
            End date of the ocean current query period in ``YYYY-MM-DD``
            format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        shoreline_source : str or sequence of str, optional
            Source or sources used to provide the synthetic shoreline data.
            Use this parameter when the exact shoreline inputs are known.

        Returns
        -------
        synthetic_shoreline_data : object
            Synthetic shoreline geometry, vector data, or raster data filtered
            by spatial region.

        Notes
        -----
        This tool only loads synthetic shoreline data. It does not create
        shoreline buffers, apply water or land masks, clip SAR scenes, run CFAR
        detection, or remove nearshore detections.
        """
        tool_name = "load_synthetic_shoreline_data"

        generated = {
            "synthetic_shoreline_data": {
                "synthetic_shoreline_data_id": "synthetic_shoreline_data",
                "region": region,
                "shoreline_source": shoreline_source,
                "date_begin": date_begin,
                "date_end": date_end,
            }
        }

        completed_state = SeaActivityStates.SYNTHETIC_SHORELINE_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Synthetic shoreline data from {shoreline_source} "
                f"over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_sea_ice_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            sea_ice_product: str = "Multisensor Analyzed Sea Ice Extent - Northern Hemisphere",
            sea_ice_version: str = "Version 1",
            coverage_region: str = "Northern Hemisphere",
    ) -> dict[str, Any]:
        """
        Load time-variable sea-ice extent data for a specified time and region.

        This tool loads sea-ice extent data from a specified product, such as
        the Multisensor Analyzed Sea Ice Extent - Northern Hemisphere
        (MASIE-NH), Version 1, and filters it by temporal and spatial bounds.
        The resulting sea-ice extent raster or polygon data can be used for
        SAR detection-area filtering, sea-ice masking, environmental feature
        construction, or polar-region spatial analysis.

        Parameters
        ----------
        date_begin : str
            Start date of the sea-ice query period in ``YYYY-MM-DD`` format.
        date_end : str
            End date of the sea-ice query period in ``YYYY-MM-DD`` format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        sea_ice_product : str, optional
            Sea-ice product name, such as
            ``"Multisensor Analyzed Sea Ice Extent - Northern Hemisphere"``.
        sea_ice_version : str, optional
            Version identifier of the sea-ice product, such as ``"Version 1"``.
        coverage_region : str, optional
            Geographic coverage of the sea-ice product. For MASIE-NH, this is
            typically ``"Northern Hemisphere"``.

        Returns
        -------
        sea_ice_data : object
            Time-variable sea-ice extent raster or polygon data filtered by date
            and region.

        Notes
        -----
        This tool only loads sea-ice extent data. It does not perform sea-ice
        mask construction, SAR scene clipping, SAR target detection, feature
        stack construction, or temporal aggregation.
        """
        tool_name = "load_sea_ice_data"

        generated = {
            "sea_ice_data": {
                "sea_ice_data_id": f"sea_ice_data_{date_begin}_{date_end}",
                "date_begin": date_begin,
                "date_end": date_end,
                "region": region,
                "sea_ice_product": sea_ice_product,
                "sea_ice_version": sea_ice_version,
                "coverage_region": coverage_region,
            }
        }

        completed_state = SeaActivityStates.SEA_ICE_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Sea-ice extent data from {sea_ice_product} {sea_ice_version} "
                f"for {date_begin} to {date_end} over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_global_roads_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            roads_source: str = "gROADSv1",
    ) -> dict[str, Any]:
        """
        Load global road network data for a specified spatial region.

        This tool loads road network data from a specified global road dataset,
        such as gROADSv1, and filters it by spatial bounds. The resulting road
        geometries can be used by downstream road-proximity filtering, bridge
        or land-vehicle false-positive removal, shoreline quality control, or
        spatial analysis workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the sea-ice query period in ``YYYY-MM-DD`` format.
        date_end : str
            End date of the sea-ice query period in ``YYYY-MM-DD`` format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        roads_source : str, optional
            Data source or provider for the global road network dataset.

        Returns
        -------
        roads_data : object
            Road network geometries filtered by spatial region.

        Notes
        -----
        This tool only loads road network data. It does not create road buffers,
        remove SAR detections near roads or bridges, apply shoreline masks, run
        SAR target detection, or perform temporal aggregation.
        """
        tool_name = "load_global_roads_data"

        generated = {
            "roads_data": {
                "roads_data_id": "roads_data",
                "region": region,
                "roads_source": roads_source,
                "date_begin": date_begin,
                "date_end": date_end,
            }
        }

        completed_state = SeaActivityStates.GLOBAL_ROADS_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Global road network data from {roads_source} "
                f"over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }

    @agent_tool
    def load_global_oil_regions_data(
            self,
            date_begin: str,
            date_end: str,
            region: list[float],
            oil_regions_source: str = "global_oil_regions_reference",
    ) -> dict[str, Any]:
        """
        Load global oil-region spatial data for a specified region.

        This tool loads global oil-region reference data, such as spatial
        polygons or region-level datasets derived from published sources, and
        filters it by spatial bounds. The resulting oil-region data can be used
        for downstream offshore oil infrastructure analysis, spatial
        attribution, validation, or regional aggregation workflows.

        Parameters
        ----------
        date_begin : str
            Start date of the sea-ice query period in ``YYYY-MM-DD`` format.
        date_end : str
            End date of the sea-ice query period in ``YYYY-MM-DD`` format.
        region : list[float]
            Spatial bounding box used to filter the data, typically in the form
            ``[lon_min, lat_min, lon_max, lat_max]``.
        oil_regions_source : str, optional
            Source or dataset name for global oil-region spatial data.

        Returns
        -------
        oil_regions_data : object
            Oil-region polygons or spatial reference data filtered by spatial
            region.

        Notes
        -----
        This tool only loads oil-region reference data. It does not classify
        infrastructure, identify oil platforms, perform spatial joins, validate
        detections, or aggregate infrastructure activity by region.
        """
        tool_name = "load_global_oil_regions_data"

        generated = {
            "oil_regions_data": {
                "oil_regions_data_id": "oil_regions_data",
                "region": region,
                "oil_regions_source": oil_regions_source,
                "date_begin": date_begin,
                "date_end": date_end,
            }
        }

        completed_state = SeaActivityStates.GLOBAL_OIL_REGIONS_DATA_LOADED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                f"Global oil-region spatial data from {oil_regions_source} "
                f"over region {region} have been loaded."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": None,
            },
        }
