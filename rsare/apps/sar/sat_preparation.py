from __future__ import annotations
from typing import Any

from rsare.agents.agent.toolset_builder import agent_tool
from rsare.apps.sar.sea_activity_tools import (
    SeaActivityDefaults,
    SeaActivityStates,
    SeaActivityToolState,
    SeaActivityTools,
)


class SAT_Preparation(SeaActivityTools):
    """
    Preparation tools for SAR-based sea activity workflow testing.
    """

    def __init__(
        self,
        state: SeaActivityToolState | None = None,
        sat_defaults: SeaActivityDefaults | None = None,
    ):
        super().__init__(
            name="SAT_Preparation",
            state=state,
            sat_defaults=sat_defaults,
        )

    # -------------------------------------------------------------------------
    # Preparation tools
    # -------------------------------------------------------------------------

    @agent_tool
    def construct_sar_median_composites(
            self,
            clipped_sar_scenes: object,
            composite_window_months: int,
            composite_step: str,
            min_num_images: int,
            max_num_images: int,
            composite_reducer: str,
            detection_band: str,
    ) -> dict[str, Any]:
        """
        Construct Sentinel-1 SAR median composites for fixed-infrastructure
        detection.

        This tool builds a time series of Sentinel-1 SAR median composites for
        offshore infrastructure detection. For each temporal step, it selects
        SAR scenes within a temporal window, uses the requested SAR backscatter
        band, and computes a composite. The resulting composites emphasize
        stationary objects that persist across multiple SAR acquisitions while
        suppressing non-stationary objects such as moving vessels.

        Parameters
        ----------
        clipped_sar_scenes : object
            Border-clipped Sentinel-1 SAR scenes available for composite
            construction.
        composite_window_months : int
            Length of the temporal window used to construct each composite.
        composite_step : str
            Temporal step between composites.
        min_num_images : int
            Minimum number of valid SAR images required for composite
            construction.
        max_num_images : int
            Maximum number of SAR images sampled within each composite window.
        composite_reducer : str
            Reducer used to combine images within the window.
        detection_band : str
            SAR polarization band used for composite construction.

        Returns
        -------
        sar_median_composites : object
            Time series of Sentinel-1 SAR median composite images.

        Notes
        -----
        This tool only constructs SAR median composites. It does not run CFAR
        detection, classify infrastructure, perform temporal interpolation of
        fixed structures, or aggregate infrastructure activity over space or
        time.
        """
        tool_name = "construct_sar_median_composites"

        required_states = [
            SeaActivityStates.SAR_SCENE_BORDERS_CLIPPED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Clipped SAR scenes must be prepared before constructing "
                    "SAR median composites."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if "clipped_sar_scenes" not in self.state.generated_contents:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Clipped SAR scene content is missing before constructing "
                    "SAR median composites."
                ),
                "missing_generated_content": ["clipped_sar_scenes"],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "sar_median_composites": {
                "sar_median_composites_id": "sar_median_composites",
                "source_clipped_sar_scenes": clipped_sar_scenes,
                "composite_window_months": composite_window_months,
                "composite_step": composite_step,
                "min_num_images": min_num_images,
                "max_num_images": max_num_images,
                "composite_reducer": composite_reducer,
                "detection_band": detection_band,
            }
        }

        completed_state = SeaActivityStates.SAR_MEDIAN_COMPOSITES_CONSTRUCTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Sentinel-1 SAR median composites have been constructed from "
                "clipped SAR scenes."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def extract_vessel_detection_tiles(
        self,
        candidate_vessel_detections: object,
        clipped_sar_images: object,
        tile_size_px: int,
        input_bands: list[str] | None = None,
        tile_center_rule: str | None = None,
    ) -> dict[str, Any]:
        """
        Extract SAR image tiles centered on candidate vessel detections.

        This tool extracts dual-band Sentinel-1 SAR image tiles for candidate
        vessel detections produced by the CFAR detector. Each tile is centered
        on a candidate detection location and contains the requested SAR bands
        needed by the vessel presence and length estimation model.

        Parameters
        ----------
        candidate_vessel_detections : object
            Candidate vessel detections produced by the two-parameter SAR CFAR
            detector.
        clipped_sar_images : object
            Border-clipped Sentinel-1 SAR images from which detection-centered
            tiles are extracted.
        tile_size_px : int
            Width and height of the square SAR tile in pixels.
        input_bands : list[str], optional
            SAR bands to include in each tile. If not provided, the default
            vessel detection tile input bands from SeaActivityDefaults are used.
        tile_center_rule : str, optional
            Rule used to place each tile. If not provided, the default vessel
            detection tile center rule from SeaActivityDefaults is used.

        Returns
        -------
        vessel_inference_tiles : object
            Extracted SAR image tiles for candidate vessel detections.

        Notes
        -----
        This tool only extracts SAR tiles for candidate vessel detections. It
        does not run CFAR detection, classify vessel presence, estimate vessel
        length, perform AIS matching, or classify vessels as fishing or
        non-fishing.
        """
        tool_name = "extract_vessel_detection_tiles"

        required_states = [
            SeaActivityStates.VESSEL_CFAR_DETECTION_COMPLETED,
            SeaActivityStates.SAR_SCENE_BORDERS_CLIPPED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Candidate vessel detections and clipped SAR images must be "
                    "prepared before extracting vessel detection tiles."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        missing_generated_content = []

        for content_key in [
            "candidate_vessel_detections",
            "clipped_sar_scenes",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Candidate vessel detection content or clipped SAR image "
                    "content is missing before extracting vessel detection tiles."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if input_bands is None:
            input_bands = list(self.sat_defaults.vessel_detection_tile_input_bands)

        if tile_center_rule is None:
            tile_center_rule = self.sat_defaults.vessel_detection_tile_center_rule

        generated = {
            "vessel_inference_tiles": {
                "vessel_inference_tiles_id": "vessel_inference_tiles",
                "source_candidate_vessel_detections": candidate_vessel_detections,
                "source_clipped_sar_images": clipped_sar_images,
                "tile_size_px": tile_size_px,
                "input_bands": input_bands,
                "tile_center_rule": tile_center_rule,
            },
        }

        completed_state = SeaActivityStates.VESSEL_DETECTION_TILES_EXTRACTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Vessel detection tiles have been extracted from clipped SAR images."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def extract_infrastructure_sar_tiles(
        self,
        candidate_infrastructure_detections: object,
        sar_composites: object,
        tile_size_px: int,
        input_bands: list[str] | None = None,
        tile_center_rule: str | None = None,
    ) -> dict[str, Any]:
        """
        Extract SAR image tiles centered on candidate infrastructure detections.

        This tool extracts dual-band Sentinel-1 SAR tiles for candidate
        offshore infrastructure detections produced by the CFAR detector. Each
        tile is centered on a candidate detection location and contains the
        requested SAR bands needed by the infrastructure classification model.

        Parameters
        ----------
        candidate_infrastructure_detections : object
            Candidate infrastructure detections produced by the two-parameter
            SAR CFAR detector.
        sar_composites : object
            Sentinel-1 SAR composite images or SAR image data from which
            detection-centered tiles are extracted.
        tile_size_px : int
            Width and height of the square SAR tile in pixels.
        input_bands : list[str], optional
            SAR bands to include in each tile. If not provided, the default
            infrastructure SAR tile input bands from SeaActivityDefaults are
            used.
        tile_center_rule : str, optional
            Rule used to place each tile. If not provided, the default
            infrastructure SAR tile center rule from SeaActivityDefaults is
            used.

        Returns
        -------
        infrastructure_sar_tiles : object
            Extracted SAR image tiles for candidate infrastructure detections.

        Notes
        -----
        This tool only extracts SAR tiles for candidate infrastructure
        detections. It does not run CFAR detection, construct SAR median
        composites, extract optical tiles, classify infrastructure, or aggregate
        infrastructure activity over time.
        """
        tool_name = "extract_infrastructure_sar_tiles"

        required_states = [
            SeaActivityStates.INFRASTRUCTURE_CFAR_DETECTION_COMPLETED,
            SeaActivityStates.SAR_MEDIAN_COMPOSITES_CONSTRUCTED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Candidate infrastructure detections and SAR composites must "
                    "be prepared before extracting infrastructure SAR tiles."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        missing_generated_content = []

        for content_key in [
            "candidate_infrastructure_detections",
            "sar_median_composites",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Candidate infrastructure detection content or SAR composite "
                    "content is missing before extracting infrastructure SAR tiles."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if input_bands is None:
            input_bands = list(self.sat_defaults.infrastructure_sar_tile_input_bands)

        if tile_center_rule is None:
            tile_center_rule = self.sat_defaults.infrastructure_sar_tile_center_rule

        generated = {
            "infrastructure_sar_tiles": {
                "infrastructure_sar_tiles_id": "infrastructure_sar_tiles",
                "source_candidate_infrastructure_detections": (
                    candidate_infrastructure_detections
                ),
                "source_sar_composites": sar_composites,
                "tile_size_px": tile_size_px,
                "input_bands": input_bands,
                "tile_center_rule": tile_center_rule,
            },
        }

        completed_state = SeaActivityStates.INFRASTRUCTURE_SAR_TILES_EXTRACTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Infrastructure SAR tiles have been extracted from SAR composites."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def extract_infrastructure_optical_tiles(
        self,
        candidate_infrastructure_detections: object,
        optical_images: object,
        tile_size_px: int,
        input_bands: list[str] | None = None,
        tile_center_rule: str | None = None,
    ) -> dict[str, Any]:
        """
        Extract Sentinel-2 optical tiles centered on candidate infrastructure detections.

        This tool extracts Sentinel-2 optical image tiles for candidate offshore
        infrastructure detections produced by the CFAR detector. Each tile is
        centered on a candidate detection location and contains the requested
        optical bands needed by the infrastructure classification model.

        Parameters
        ----------
        candidate_infrastructure_detections : object
            Candidate infrastructure detections produced by the two-parameter
            SAR CFAR detector.
        optical_images : object
            Sentinel-2 optical images from which detection-centered tiles are
            extracted.
        tile_size_px : int
            Width and height of the square optical tile in pixels.
        input_bands : list[str], optional
            Optical bands to include in each tile. If not provided, the default
            infrastructure optical tile input bands from SeaActivityDefaults are
            used.
        tile_center_rule : str, optional
            Rule used to place each tile. If not provided, the default
            infrastructure optical tile center rule from SeaActivityDefaults is
            used.

        Returns
        -------
        infrastructure_optical_tiles : object
            Extracted Sentinel-2 optical image tiles for candidate
            infrastructure detections.
        Notes
        -----
        This tool only extracts optical tiles for candidate infrastructure
        detections. It does not run CFAR detection, construct SAR tiles, filter
        clouds, classify infrastructure, or aggregate infrastructure activity
        over time.
        """
        tool_name = "extract_infrastructure_optical_tiles"

        required_states = [
            SeaActivityStates.INFRASTRUCTURE_CFAR_DETECTION_COMPLETED,
            SeaActivityStates.SENTINEL2_CLOUD_FILTERED_WITH_QA60,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Candidate infrastructure detections and cloud-filtered "
                    "Sentinel-2 images must be prepared before extracting "
                    "infrastructure optical tiles."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        missing_generated_content = []

        for content_key in [
            "candidate_infrastructure_detections",
            "cloud_filtered_sentinel2_images",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Candidate infrastructure detection content or "
                    "cloud-filtered Sentinel-2 image content is missing before "
                    "extracting infrastructure optical tiles."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if input_bands is None:
            input_bands = list(
                self.sat_defaults.infrastructure_optical_tile_input_bands
            )

        if tile_center_rule is None:
            tile_center_rule = (
                self.sat_defaults.infrastructure_optical_tile_center_rule
            )

        generated = {
            "infrastructure_optical_tiles": {
                "infrastructure_optical_tiles_id": (
                    "infrastructure_optical_tiles"
                ),
                "source_candidate_infrastructure_detections": (
                    candidate_infrastructure_detections
                ),
                "source_optical_images": optical_images,
                "tile_size_px": tile_size_px,
                "input_bands": input_bands,
                "tile_center_rule": tile_center_rule,
            },
        }

        completed_state = SeaActivityStates.INFRASTRUCTURE_OPTICAL_TILES_EXTRACTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Infrastructure optical tiles have been extracted from "
                "Sentinel-2 optical images."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def construct_sar_vessel_data_rasters(
        self,
        vessel_presence_probability: object,
        estimated_length_m: object,
        spatial_resolution_km: float,
        aggregation_method: str | None = None,
    ) -> dict[str, Any]:
        """
        Construct SAR-derived vessel feature rasters.

        This tool converts vessel model outputs from SAR detections into
        spatial raster features. It aggregates vessel presence probabilities
        and estimated vessel lengths to produce gridded vessel density and
        average vessel length rasters.

        Parameters
        ----------
        vessel_presence_probability : object
            Vessel presence probabilities produced by the vessel presence and
            length estimation model.
        estimated_length_m : object
            Estimated vessel lengths in meters for SAR detections.
        spatial_resolution_km : float
            Spatial resolution of the output raster grid.
        aggregation_method : str or None, optional
            Aggregation rule used to construct the vessel density and average
            vessel length rasters. If not provided, the default SAR vessel
            raster aggregation method from SeaActivityDefaults is used.

        Returns
        -------
        sar_vessel_density_raster : object
            Raster representing SAR-derived vessel density or vessel presence
            density.
        sar_average_vessel_length_raster : object
            Raster representing average SAR-estimated vessel length per grid
            cell.

        Notes
        -----
        This tool only constructs SAR-derived vessel rasters. It does not run
        SAR CFAR detection, estimate vessel presence or length, construct AIS
        vessel rasters, build environmental rasters, or classify vessels as
        fishing or non-fishing.
        """
        tool_name = "construct_sar_vessel_data_rasters"

        required_states = [
            SeaActivityStates.VESSEL_PRESENCE_AND_LENGTH_ESTIMATED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel presence probability and estimated vessel length "
                    "must be prepared before constructing SAR vessel data rasters."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        missing_generated_content = []

        for content_key in [
            "vessel_presence_probability",
            "estimated_length_m",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel presence probability or estimated vessel length "
                    "content is missing before constructing SAR vessel data "
                    "rasters."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if aggregation_method is None:
            aggregation_method = (
                self.sat_defaults.sar_vessel_raster_aggregation_method
            )

        generated = {
            "sar_vessel_density_raster": {
                "sar_vessel_density_raster_id": "sar_vessel_density_raster",
                "source_vessel_presence_probability": vessel_presence_probability,
                "spatial_resolution_km": spatial_resolution_km,
                "aggregation_method": aggregation_method,
            },
            "sar_average_vessel_length_raster": {
                "sar_average_vessel_length_raster_id": (
                    "sar_average_vessel_length_raster"
                ),
                "source_estimated_length_m": estimated_length_m,
                "spatial_resolution_km": spatial_resolution_km,
                "aggregation_method": aggregation_method,
            },
        }

        completed_state = SeaActivityStates.SAR_VESSEL_DATA_RASTERS_CONSTRUCTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "SAR-derived vessel data rasters have been constructed from "
                "vessel model outputs."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def construct_ais_vessel_data_rasters(
        self,
        interpolated_ais_data: object,
        spatial_resolution_km: float,
        aggregation_method: str | None = None,
    ) -> dict[str, Any]:
        """
        Construct AIS-derived vessel feature rasters.

        This tool converts interpolated AIS vessel records into spatial raster
        features. It aggregates AIS vessel records to produce gridded AIS vessel
        density and average vessel length rasters.

        Parameters
        ----------
        interpolated_ais_data : object
            AIS vessel records extracted and interpolated to SAR scene
            acquisition time.
        spatial_resolution_km : float
            Spatial resolution of the output raster grid.
        aggregation_method : str or None, optional
            Aggregation rule used to construct AIS vessel density and average
            vessel length rasters. If not provided, the default AIS vessel
            raster aggregation method from SeaActivityDefaults is used.

        Returns
        -------
        ais_vessel_density_raster : object
            Raster representing AIS-derived vessel density.
        ais_average_vessel_length_raster : object
            Raster representing average AIS vessel length per grid cell.

        Notes
        -----
        This tool only constructs AIS-derived vessel rasters. It does not load
        AIS data, interpolate AIS records, construct SAR vessel rasters, build
        environmental rasters, or classify vessels as fishing or non-fishing.
        """
        tool_name = "construct_ais_vessel_data_rasters"

        required_states = [
            SeaActivityStates.AIS_DATA_EXTRACTED_AND_INTERPOLATED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Interpolated AIS data must be prepared before constructing "
                    "AIS vessel data rasters."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if "interpolated_ais_data" not in self.state.generated_contents:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Interpolated AIS data content is missing before constructing "
                    "AIS vessel data rasters."
                ),
                "missing_generated_content": ["interpolated_ais_data"],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if aggregation_method is None:
            aggregation_method = (
                self.sat_defaults.ais_vessel_raster_aggregation_method
            )

        generated = {
            "ais_vessel_density_raster": {
                "ais_vessel_density_raster_id": "ais_vessel_density_raster",
                "source_interpolated_ais_data": interpolated_ais_data,
                "spatial_resolution_km": spatial_resolution_km,
                "aggregation_method": aggregation_method,
            },
            "ais_average_vessel_length_raster": {
                "ais_average_vessel_length_raster_id": (
                    "ais_average_vessel_length_raster"
                ),
                "source_interpolated_ais_data": interpolated_ais_data,
                "spatial_resolution_km": spatial_resolution_km,
                "aggregation_method": aggregation_method,
            },
        }

        completed_state = SeaActivityStates.AIS_VESSEL_DATA_RASTERS_CONSTRUCTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "AIS-derived vessel data rasters have been constructed from "
                "interpolated AIS data."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def construct_environmental_physical_data_rasters(
        self,
        chlorophyll_data: object,
        sea_surface_temperature_data: object,
        ocean_current_speed_data: object,
        distance_to_port_data: object,
        bathymetry_data: object,
        spatial_resolution_km: float,
        aggregation_method: str | None = None,
    ) -> dict[str, Any]:
        """
        Construct environmental and physical data rasters.

        This tool converts loaded environmental and physical source datasets
        into a common raster feature stack. The resulting rasters can be used as
        environmental and physical covariates for downstream fishing/non-fishing
        classification or spatial activity analysis.

        Parameters
        ----------
        chlorophyll_data : object
            Loaded chlorophyll environmental raster data.
        sea_surface_temperature_data : object
            Loaded sea-surface temperature raster data.
        ocean_current_speed_data : object
            Loaded ocean current speed raster data.
        distance_to_port_data : object
            Loaded distance-to-port data.
        bathymetry_data : object
            Loaded bathymetry or seafloor elevation data.
        spatial_resolution_km : float
            Spatial resolution of the output environmental and physical raster
            grid.
        aggregation_method : str or None, optional
            Aggregation or resampling rule used to construct the environmental
            and physical raster stack. If not provided, the default
            environmental and physical raster aggregation method from
            SeaActivityDefaults is used.

        Returns
        -------
        environmental_physical_data_rasters : object
            Environmental and physical raster feature stack constructed from
            chlorophyll, sea-surface temperature, ocean current speed,
            distance-to-port, and bathymetry inputs.

        Notes
        -----
        This tool only constructs environmental and physical feature rasters. It
        does not load source environmental datasets, construct SAR or AIS vessel
        rasters, train fishing/non-fishing models, or perform model inference.
        """
        tool_name = "construct_environmental_physical_data_rasters"

        required_states = [
            SeaActivityStates.CHLOROPHYLL_DATA_LOADED,
            SeaActivityStates.SEA_SURFACE_TEMPERATURE_DATA_LOADED,
            SeaActivityStates.OCEAN_CURRENT_SPEED_DATA_LOADED,
            SeaActivityStates.DISTANCE_TO_PORT_DATA_LOADED,
            SeaActivityStates.BATHYMETRY_DATA_LOADED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Environmental and physical source data must be loaded before "
                    "constructing environmental and physical data rasters."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        missing_generated_content = []

        for content_key in [
            "chlorophyll_data",
            "sea_surface_temperature_data",
            "ocean_current_speed_data",
            "distance_to_port_data",
            "bathymetry_data",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Required environmental or physical source content is "
                    "missing before constructing environmental and physical "
                    "data rasters."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if aggregation_method is None:
            aggregation_method = (
                self.sat_defaults
                .environmental_physical_raster_aggregation_method
            )

        generated = {
            "environmental_physical_data_rasters": {
                "environmental_physical_data_rasters_id": (
                    "environmental_physical_data_rasters"
                ),
                "source_chlorophyll_data": chlorophyll_data,
                "source_sea_surface_temperature_data": (
                    sea_surface_temperature_data
                ),
                "source_ocean_current_speed_data": ocean_current_speed_data,
                "source_distance_to_port_data": distance_to_port_data,
                "source_bathymetry_data": bathymetry_data,
                "spatial_resolution_km": spatial_resolution_km,
                "aggregation_method": aggregation_method,
            }
        }

        completed_state = (
            SeaActivityStates
            .ENVIRONMENTAL_PHYSICAL_DATA_RASTERS_CONSTRUCTED
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Environmental and physical data rasters have been constructed "
                "from loaded environmental inputs."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def generate_raster_feature_tile_stack(
        self,
        spatial_resolution_km: float,
        tile_size_px: int,
        sar_vessel_rasters: object,
        ais_vessel_rasters: object,
        environmental_rasters: object,
        vessel_presence_probability: object,
        tile_center_rule: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate model-ready raster feature tiles from raster inputs.

        This tool constructs the input feature tiles used by the fishing and
        non-fishing classification model. It combines SAR-derived vessel
        rasters, AIS-derived vessel rasters, environmental and physical rasters,
        and vessel presence probabilities into model-ready raster feature
        tiles.

        Parameters
        ----------
        spatial_resolution_km : float
            Spatial resolution of the input rasters.
        tile_size_px : int
            Width and height of each square raster feature tile in pixels.
        sar_vessel_rasters : object
            SAR-derived vessel feature rasters.
        ais_vessel_rasters : object
            AIS-derived vessel activity rasters.
        environmental_rasters : object
            Environmental and physical raster layers.
        vessel_presence_probability : object
            Vessel presence probabilities used to locate or define model-ready
            vessel samples.
        tile_center_rule : str or None, optional
            Rule used to place each tile. If not provided, the default fishing
            model tile center rule from SeaActivityDefaults is used.

        Returns
        -------
        fishing_model_feature_tiles : object
            Model-ready raster feature tiles for fishing and non-fishing
            classification.

        Notes
        -----
        This tool only generates raster feature tiles for the fishing/non-fishing
        model. It does not construct the source rasters, estimate vessel
        presence, run SAR detection, train the classifier, or perform model
        inference.
        """
        tool_name = "generate_raster_feature_tile_stack"

        required_states = [
            SeaActivityStates.SAR_VESSEL_DATA_RASTERS_CONSTRUCTED,
            SeaActivityStates.AIS_VESSEL_DATA_RASTERS_CONSTRUCTED,
            SeaActivityStates.ENVIRONMENTAL_PHYSICAL_DATA_RASTERS_CONSTRUCTED,
            SeaActivityStates.VESSEL_PRESENCE_AND_LENGTH_ESTIMATED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "SAR vessel rasters, AIS vessel rasters, environmental "
                    "rasters, and vessel presence probabilities must be prepared "
                    "before generating raster feature tiles."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        missing_generated_content = []

        for content_key in [
            "sar_vessel_density_raster",
            "sar_average_vessel_length_raster",
            "ais_vessel_density_raster",
            "ais_average_vessel_length_raster",
            "environmental_physical_data_rasters",
            "vessel_presence_probability",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Required raster feature tile source content is missing "
                    "before generating raster feature tiles."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if tile_center_rule is None:
            tile_center_rule = self.sat_defaults.fishing_model_tile_center_rule

        generated = {
            "fishing_model_feature_tiles": {
                "fishing_model_feature_tiles_id": "fishing_model_feature_tiles",
                "source_sar_vessel_rasters": sar_vessel_rasters,
                "source_ais_vessel_rasters": ais_vessel_rasters,
                "source_environmental_rasters": environmental_rasters,
                "source_vessel_presence_probability": vessel_presence_probability,
                "spatial_resolution_km": spatial_resolution_km,
                "tile_size_px": tile_size_px,
                "tile_center_rule": tile_center_rule,
            }
        }

        completed_state = SeaActivityStates.RASTER_FEATURE_TILE_STACK_GENERATED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Fishing model raster feature tiles have been generated from "
                "SAR, AIS, environmental rasters, and vessel presence probabilities."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

