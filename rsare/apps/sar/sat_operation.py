from __future__ import annotations
from typing import Any

from rsare.agents.agent.toolset_builder import agent_tool
from rsare.apps.sar.sea_activity_tools import (
    SeaActivityDefaults,
    SeaActivityStates,
    SeaActivityToolState,
    SeaActivityTools,

)


class SAT_Operation(SeaActivityTools):
    """
    Operation tools for SAR-based sea activity workflow testing.
    """

    def __init__(
        self,
        state: SeaActivityToolState | None = None,
        sat_defaults: SeaActivityDefaults | None = None,
    ):
        super().__init__(
            name="SAT_Operation",
            state=state,
            sat_defaults=sat_defaults,
        )

    # -------------------------------------------------------------------------
    # Operation tools
    # -------------------------------------------------------------------------

    @agent_tool
    def construct_shoreline_buffer_mask(
        self,
        synthetic_shoreline_data: object,
        shoreline_buffer_km: float,
    ) -> dict[str, Any]:
        """
        Construct a shoreline buffer mask for SAR detection filtering.

        This tool builds a coastal buffer mask from synthetic shoreline data.
        It excludes areas within a specified distance of the shoreline from the
        valid detection region, producing a shoreline buffer mask that can be
        used to filter SAR scenes or detections near the coast.

        Parameters
        ----------
        synthetic_shoreline_data : object
            Synthetic shoreline geometry, coastline vector data, or shoreline
            distance raster used to construct the coastal buffer mask.
        shoreline_buffer_km : float
            Buffer distance around the shoreline in kilometers.

        Returns
        -------
        shoreline_buffer_mask : object
            Shoreline buffer mask representing the nearshore region to exclude.

        Notes
        -----
        This tool only constructs the shoreline buffer mask. It does not load
        the shoreline dataset, construct the valid ocean mask, clip SAR scene
        borders, run SAR target detection, classify detections, or perform AIS
        matching.
        """
        tool_name = "construct_shoreline_buffer_mask"

        required_states = [
            SeaActivityStates.SYNTHETIC_SHORELINE_DATA_LOADED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Synthetic shoreline data must be loaded before constructing "
                    "a shoreline buffer mask."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "shoreline_buffer_mask": {
                "shoreline_buffer_mask_id": "shoreline_buffer_mask",
                "source_synthetic_shoreline_data": synthetic_shoreline_data,
                "shoreline_buffer_km": shoreline_buffer_km,
            }
        }

        completed_state = SeaActivityStates.SHORELINE_BUFFER_MASK_CONSTRUCTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Shoreline buffer mask has been constructed using the requested "
                "shoreline buffer distance."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def construct_ocean_mask(
        self,
        synthetic_shoreline_data: object,
        shoreline_buffer_km: float,
    ) -> dict[str, Any]:
        """
        Construct a valid ocean mask for SAR detection filtering.

        This tool builds a valid ocean mask from synthetic shoreline or
        shoreline-derived data. It excludes coastal areas within a specified
        shoreline buffer distance and returns the ocean region that should be
        treated as valid for downstream SAR scene filtering, clipping, or
        target detection.

        Parameters
        ----------
        synthetic_shoreline_data : object
            Synthetic shoreline geometry, coastline vector data, or
            shoreline-derived raster data used to define land, coast, and ocean
            regions.
        shoreline_buffer_km : float
            Distance from the shoreline to exclude from the valid ocean region.

        Returns
        -------
        valid_ocean_mask : object
            Ocean mask excluding the shoreline buffer region.

        Notes
        -----
        This tool only constructs the valid ocean mask. It does not load the
        shoreline dataset, construct the shoreline buffer mask as a separate
        output, clip SAR scene borders, run CFAR detection, classify detections,
        or perform AIS matching.
        """
        tool_name = "construct_ocean_mask"

        required_states = [
            SeaActivityStates.SYNTHETIC_SHORELINE_DATA_LOADED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Synthetic shoreline data must be loaded before constructing "
                    "a valid ocean mask."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "valid_ocean_mask": {
                "valid_ocean_mask_id": "valid_ocean_mask",
                "source_synthetic_shoreline_data": synthetic_shoreline_data,
                "shoreline_buffer_km": shoreline_buffer_km,
            }
        }

        completed_state = SeaActivityStates.OCEAN_MASK_CONSTRUCTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Valid ocean mask has been constructed using the requested "
                "shoreline buffer distance."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def construct_sea_ice_filtering_mask(
        self,
        sea_ice_data: object,
        mask_date: str | None = None,
        region: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        Construct a sea-ice filtering mask for SAR detection filtering.

        This tool converts time-variable sea-ice extent data into a mask that
        can be used to exclude sea-ice-covered areas from SAR detection regions
        or detection results. The mask should be aligned with the relevant SAR
        scene date or detection date and spatial region.

        Parameters
        ----------
        sea_ice_data : object
            Sea-ice extent raster or polygon data loaded for the relevant time
            period and spatial region.
        mask_date : str, optional
            Date used to select or align the sea-ice extent with SAR scenes or
            detections, typically in ``YYYY-MM-DD`` format.
        region : list[float] or None, optional
            Spatial bounding box used to construct the mask, typically in the
            form ``[lon_min, lat_min, lon_max, lat_max]``.

        Returns
        -------
        valid_non_ice_mask : object
            Mask representing areas not covered by sea ice and valid for
            downstream SAR detection or filtering.

        Notes
        -----
        This tool only constructs the sea-ice filtering mask. It does not load
        sea-ice data, run SAR target detection, classify detections, perform
        AIS matching, or aggregate detections over space or time.
        """
        tool_name = "construct_sea_ice_filtering_mask"

        required_states = [
            SeaActivityStates.SEA_ICE_DATA_LOADED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Sea-ice data must be loaded before constructing a sea-ice "
                    "filtering mask."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "valid_non_ice_mask": {
                "valid_non_ice_mask_id": "valid_non_ice_mask",
                "source_sea_ice_data": sea_ice_data,
                "mask_date": mask_date,
                "region": region,
            }
        }

        completed_state = SeaActivityStates.SEA_ICE_FILTERING_MASK_CONSTRUCTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Sea-ice filtering mask has been constructed for the requested "
                "date and region."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def construct_road_bridge_vehicle_mask(
        self,
        roads_data: object,
        coastline_data: object,
        coastline_distance_threshold_km: float,
        highway_vehicle_speed_kmh: float,
        primary_road_vehicle_speed_kmh: float,
        region: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        Construct a road, bridge, and vehicle false-positive exclusion mask.

        This tool builds an exclusion mask for SAR detections that may be caused
        by roads, bridges, or fast-moving vehicles near the coastline. It uses
        road network data together with coastline proximity constraints and
        road-type-specific vehicle speed assumptions to identify regions where
        SAR detections are likely to be road- or bridge-related false positives.

        Parameters
        ----------
        roads_data : object
            Road network geometries filtered to the region of interest.
        coastline_data : object
            Coastline or shoreline geometry used to identify roads and bridges
            near the coast.
        coastline_distance_threshold_km : float
            Maximum distance from the coastline for roads and bridges to be
            considered in the filtering mask.
        highway_vehicle_speed_kmh : float
            Assumed vehicle speed on highways in kilometers per hour.
        primary_road_vehicle_speed_kmh : float
            Assumed vehicle speed on primary roads in kilometers per hour.
        region : list[float] or None, optional
            Spatial bounding box used to construct the mask, typically in the
            form ``[lon_min, lat_min, lon_max, lat_max]``.

        Returns
        -------
        road_bridge_vehicle_exclusion_mask : object
            Mask representing road, bridge, and vehicle-related areas to exclude
            from SAR detections or valid detection regions.

        Notes
        -----
        This tool only constructs the road, bridge, and vehicle false-positive
        mask. It does not load the road dataset, run SAR target detection,
        classify detections, perform shoreline masking, or aggregate detections
        over space or time.
        """
        tool_name = "construct_road_bridge_vehicle_mask"

        required_states = [
            SeaActivityStates.GLOBAL_ROADS_DATA_LOADED,
            SeaActivityStates.SYNTHETIC_SHORELINE_DATA_LOADED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Roads data and synthetic shoreline data must be loaded before "
                    "constructing a road, bridge, and vehicle false-positive mask."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "road_bridge_vehicle_exclusion_mask": {
                "road_bridge_vehicle_exclusion_mask_id": (
                    "road_bridge_vehicle_exclusion_mask"
                ),
                "source_roads_data": roads_data,
                "source_coastline_data": coastline_data,
                "coastline_distance_threshold_km": coastline_distance_threshold_km,
                "highway_vehicle_speed_kmh": highway_vehicle_speed_kmh,
                "primary_road_vehicle_speed_kmh": primary_road_vehicle_speed_kmh,
                "region": region,
            }
        }

        completed_state = SeaActivityStates.ROAD_BRIDGE_VEHICLE_MASK_CONSTRUCTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Road, bridge, and vehicle false-positive exclusion mask has "
                "been constructed."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def filter_sar_scenes_with_mask(
        self,
        sar_scenes: object,
        mask_list: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Filter Sentinel-1 SAR scenes using selected spatial masks.

        This tool applies selected spatial masks to Sentinel-1 SAR scenes in
        order to restrict downstream detection to valid regions and exclude
        areas likely to produce false detections. If no mask is selected, the
        tool performs a no-op pass-through and returns the SAR scenes without
        spatial mask filtering.

        Parameters
        ----------
        sar_scenes : object
            Selected Sentinel-1 SAR scenes or image objects to be filtered.
        mask_list : list[str] or None, optional
            Optional list of selected mask names. Supported mask names are
            ``"valid_ocean_mask"``, ``"shoreline_buffer_mask"``,
            ``"valid_non_ice_mask"``, and
            ``"road_bridge_vehicle_exclusion_mask"``. If None or empty, no
            spatial mask filtering is applied.

        Returns
        -------
        filtered_sar_scenes : object
            SAR scenes after applying the selected masks, or the original SAR
            scenes passed through when no masks are selected.

        Notes
        -----
        This tool only applies selected spatial masks to SAR scenes. It does
        not load SAR imagery, construct the masks, clip SAR scene borders, run
        CFAR detection, classify detections, or perform AIS matching.

        The mask combination should be selected based on the downstream task.
        """
        tool_name = "filter_sar_scenes_with_mask"

        allowed_masks = {
            "valid_ocean_mask": {
                "required_state": SeaActivityStates.OCEAN_MASK_CONSTRUCTED,
                "effect": "invalid ocean-region",
            },
            "shoreline_buffer_mask": {
                "required_state": SeaActivityStates.SHORELINE_BUFFER_MASK_CONSTRUCTED,
                "effect": "nearshore shoreline-buffer",
            },
            "valid_non_ice_mask": {
                "required_state": SeaActivityStates.SEA_ICE_FILTERING_MASK_CONSTRUCTED,
                "effect": "sea-ice-covered",
            },
            "road_bridge_vehicle_exclusion_mask": {
                "required_state": SeaActivityStates.ROAD_BRIDGE_VEHICLE_MASK_CONSTRUCTED,
                "effect": "road-, bridge-, and vehicle-related false-positive",
            },
        }

        if mask_list is None:
            mask_list = []

        unsupported_masks = [
            mask_name
            for mask_name in mask_list
            if mask_name not in allowed_masks
        ]

        if unsupported_masks:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Unsupported masks were provided. Only valid_ocean_mask, "
                    "shoreline_buffer_mask, valid_non_ice_mask, and "
                    "road_bridge_vehicle_exclusion_mask are supported."
                ),
                "unsupported_masks": unsupported_masks,
                "supported_masks": list(allowed_masks.keys()),
                "generated": {},
                "state": {
                    "completed": None,
                    "required": None,
                },
            }

        required_states = [
            SeaActivityStates.SAR_SCENES_LOADED,
        ]

        for mask_name in mask_list:
            required_states.append(allowed_masks[mask_name]["required_state"])

        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Required SAR scenes or selected spatial masks are missing "
                    "before filtering SAR scenes."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        missing_generated_masks = [
            mask_name
            for mask_name in mask_list
            if mask_name not in self.state.generated_contents
        ]

        if missing_generated_masks:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Selected mask states are completed, but required generated "
                    "mask contents are missing."
                ),
                "missing_generated_masks": missing_generated_masks,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        selected_mask_objects = {
            mask_name: self.state.generated_contents[mask_name]
            for mask_name in mask_list
        }

        mask_usage_fraction = len(mask_list) / len(allowed_masks)
        mask_usage_percent = round(mask_usage_fraction * 100.0, 2)

        generated = {
            "filtered_sar_scenes": {
                "filtered_sar_scenes_id": "filtered_sar_scenes",
                "source_sar_scenes": sar_scenes,
                "mask_list": mask_list,
                "selected_mask_objects": selected_mask_objects,
                "mask_usage_percent": mask_usage_percent,
                "no_op": len(mask_list) == 0,
            }
        }

        completed_state = SeaActivityStates.SAR_SCENES_FILTERED_WITH_MASK

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        if len(mask_list) == 0:
            message = (
                "No spatial masks were selected; Sentinel-1 SAR scenes were "
                "passed through without mask filtering."
            )
        elif len(mask_list) == len(allowed_masks):
            message = (
                "Sentinel-1 SAR scenes have been filtered using all supported "
                "spatial masks."
            )
        else:
            removed_effects = [
                allowed_masks[mask_name]["effect"]
                for mask_name in mask_list
            ]
            message = (
                f"Sentinel-1 SAR scenes have been filtered using "
                f"{mask_usage_percent}% of supported spatial masks; the effects "
                f"of {', '.join(removed_effects)} areas have been removed."
            )

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": message,
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def clip_sar_scene_borders(
        self,
        filtered_sar_scenes: object,
        border_clipping_buffer_m: float,
    ) -> dict[str, Any]:
        """
        Clip border regions from filtered Sentinel-1 SAR scenes.

        This tool applies an inward border clipping buffer to filtered
        Sentinel-1 SAR scenes in order to remove edge regions that may contain
        noise artefacts and produce false detections in downstream SAR target
        detection.

        Parameters
        ----------
        filtered_sar_scenes : object
            Filtered Sentinel-1 SAR scenes or image objects to be clipped.
        border_clipping_buffer_m : float
            Border clipping distance in meters.

        Returns
        -------
        clipped_sar_scenes : object
            Sentinel-1 SAR scenes after border clipping.

        Notes
        -----
        This tool only performs SAR scene border clipping. It does not apply
        masks, run CFAR detection, classify detections, or perform AIS matching.
        """
        tool_name = "clip_sar_scene_borders"

        required_states = [
            SeaActivityStates.SAR_SCENES_FILTERED_WITH_MASK,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Filtered SAR scenes must be prepared before clipping scene "
                    "borders."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if "filtered_sar_scenes" not in self.state.generated_contents:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Filtered SAR scene content is missing before clipping scene "
                    "borders."
                ),
                "missing_generated_content": ["filtered_sar_scenes"],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "clipped_sar_scenes": {
                "clipped_sar_scenes_id": "clipped_sar_scenes",
                "source_filtered_sar_scenes": filtered_sar_scenes,
                "border_clipping_buffer_m": border_clipping_buffer_m,
            }
        }

        completed_state = SeaActivityStates.SAR_SCENE_BORDERS_CLIPPED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Sentinel-1 SAR scene borders have been clipped using the "
                "requested inward buffer."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def filter_sentinel2_clouds_with_qa60(
        self,
        sentinel2_images: object,
        max_cloud_coverage_percent: float,
        cloud_mask_band: str,
    ) -> dict[str, Any]:
        """
        Filter Sentinel-2 RGB-NIR imagery using cloud information.

        This tool filters selected Sentinel-2 optical imagery using cloud
        information, such as a QA cloud mask band and a maximum cloud coverage
        threshold. It is intended to reduce cloud-contaminated optical
        observations before downstream compositing, tile construction, or
        offshore infrastructure classification.

        Parameters
        ----------
        sentinel2_images : object
            Selected Sentinel-2 RGB-NIR image collection or image set to be
            filtered.
        max_cloud_coverage_percent : float
            Maximum allowed cloud coverage percentage for retaining an image.
        cloud_mask_band : str
            Sentinel-2 cloud mask band used for QA-based cloud filtering.

        Returns
        -------
        cloud_filtered_sentinel2_images : object
            Sentinel-2 RGB-NIR images after cloud filtering or cloud masking.

        Notes
        -----
        This tool only performs Sentinel-2 cloud filtering. It does not load
        Sentinel-2 imagery, create optical composites, extract image tiles,
        classify infrastructure, or fuse SAR and optical features.

        The exact bit-mask logic should be verified against the implementation
        if pixel-level cloud masking is required.
        """
        tool_name = "filter_sentinel2_clouds_with_qa60"

        required_states = [
            SeaActivityStates.OPTICAL_SCENES_LOADED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Sentinel-2 optical scenes must be loaded before cloud filtering."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if "optical_scenes" not in self.state.generated_contents:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Sentinel-2 optical scene content is missing before cloud filtering."
                ),
                "missing_generated_content": ["optical_scenes"],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "cloud_filtered_sentinel2_images": {
                "cloud_filtered_sentinel2_images_id": (
                    "cloud_filtered_sentinel2_images"
                ),
                "source_sentinel2_images": sentinel2_images,
                "max_cloud_coverage_percent": max_cloud_coverage_percent,
                "cloud_mask_band": cloud_mask_band,
            }
        }

        completed_state = SeaActivityStates.SENTINEL2_CLOUD_FILTERED_WITH_QA60

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Sentinel-2 RGB-NIR imagery has been filtered using the requested "
                "cloud mask band and cloud coverage threshold."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def extract_and_interpolate_ais_data(
        self,
        sar_scenes: object,
        ais_records: object,
    ) -> dict[str, Any]:
        """
        Extract AIS records near SAR scenes and interpolate vessel positions to SAR
        acquisition time.

        This tool selects AIS vessel records that are temporally and spatially
        relevant to Sentinel-1 SAR scenes and estimates each vessel's position
        at the SAR acquisition time. Scene footprints and acquisition times are
        treated as information provided by or derived from the SAR scenes input.

        Parameters
        ----------
        sar_scenes : object
            Sentinel-1 SAR scenes containing or implying scene footprints,
            acquisition times, scene identifiers, and spatial coverage.
        ais_records : object
            AIS message records or pipeline-processed AIS data containing vessel
            identifiers, timestamps, positions, speed, course, and segment
            information.

        Returns
        -------
        interpolated_ais_data : object
            AIS-derived vessel positions interpolated to SAR scene time,
            typically including vessel identifiers, scene identifiers,
            interpolated longitude and latitude, timestamps, and
            within-footprint indicators.

        Notes
        -----
        This tool only extracts and interpolates AIS vessel positions relative
        to SAR scenes. It does not load SAR scenes, load AIS data, run SAR-CFAR
        detection, score SAR-AIS matches, classify vessels, or aggregate vessel
        activity.
        """
        tool_name = "extract_and_interpolate_ais_data"

        required_states = [
            SeaActivityStates.SAR_SCENES_LOADED,
            SeaActivityStates.AIS_DATA_LOADED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "SAR scenes and AIS records must be loaded before AIS "
                    "extraction and interpolation."
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
            "scene_collection",
            "ais_records",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "SAR scene content or AIS record content is missing before "
                    "AIS extraction and interpolation."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "interpolated_ais_data": {
                "interpolated_ais_data_id": "interpolated_ais_data",
                "source_sar_scenes": sar_scenes,
                "source_ais_records": ais_records,
            }
        }

        completed_state = SeaActivityStates.AIS_DATA_EXTRACTED_AND_INTERPOLATED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "AIS records have been extracted and interpolated using the "
                "provided SAR scenes."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def define_offshore_infrastructure_analysis_polygons(
        self,
        polygon_type: str,
        global_oil_regions_data: object | None = None,
        interpolated_ais_data: object | None = None,
    ) -> dict[str, Any]:
        """
        Define offshore infrastructure analysis polygons.

        This tool constructs or filters spatial polygons used to represent
        offshore infrastructure analysis regions, such as offshore oil-producing
        areas and wind-farm regions. The polygons can be derived from external
        oil-region reference datasets, interpolated AIS-derived activity data,
        or confirmed infrastructure detection and classification outputs,
        depending on the available implementation and data sources.

        Parameters
        ----------
        polygon_type : str
            Type of polygons to construct or return. Supported values are
            ``"oil_producing_area"`` and ``"wind_farm_region"``.
        global_oil_regions_data : object, optional
            Spatial reference data used to define offshore oil-producing area
            polygons.
        interpolated_ais_data : object, optional
            Extracted and interpolated AIS records that may be used to support
            construction of activity-based infrastructure region polygons.

        Returns
        -------
        spatial_polygons : object
            Offshore infrastructure analysis polygons, such as oil-producing
            area polygons and wind-farm region polygons.

        Notes
        -----
        This tool only defines or filters spatial analysis polygons. It does not
        load the source datasets, interpolate AIS positions, run SAR detection,
        classify infrastructure, or perform spatial aggregation.
        """
        tool_name = "define_offshore_infrastructure_analysis_polygons"

        supported_polygon_types = {
            "oil_producing_area",
            "wind_farm_region",
        }

        if polygon_type not in supported_polygon_types:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Unsupported polygon type was provided. Only "
                    "oil_producing_area and wind_farm_region are supported."
                ),
                "unsupported_polygon_type": polygon_type,
                "supported_polygon_types": sorted(supported_polygon_types),
                "generated": {},
                "state": {
                    "completed": None,
                    "required": None,
                },
            }

        if global_oil_regions_data is None and interpolated_ais_data is None:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "At least one source input must be provided before defining "
                    "offshore infrastructure analysis polygons."
                ),
                "required_states": [],
                "missing_states": [],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": [],
                },
            }

        required_states = []

        if global_oil_regions_data is not None:
            required_states.append(
                SeaActivityStates.GLOBAL_OIL_REGIONS_DATA_LOADED
            )

        if interpolated_ais_data is not None:
            required_states.append(
                SeaActivityStates.AIS_DATA_EXTRACTED_AND_INTERPOLATED
            )

        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Required source data must be prepared before defining "
                    "offshore infrastructure analysis polygons."
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

        if (
            global_oil_regions_data is not None
            and "oil_regions_data" not in self.state.generated_contents
        ):
            missing_generated_content.append("oil_regions_data")

        if (
            interpolated_ais_data is not None
            and "interpolated_ais_data" not in self.state.generated_contents
        ):
            missing_generated_content.append("interpolated_ais_data")

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Required source content is missing before defining offshore "
                    "infrastructure analysis polygons."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "spatial_polygons": {
                "spatial_polygons_id": "spatial_polygons",
                "polygon_type": polygon_type,
                "source_global_oil_regions_data": global_oil_regions_data,
                "source_interpolated_ais_data": interpolated_ais_data,
            }
        }

        completed_state = (
            SeaActivityStates.OFFSHORE_INFRASTRUCTURE_ANALYSIS_POLYGONS_DEFINED
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Offshore infrastructure analysis polygons have been defined "
                "using the requested polygon type and provided source data."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def match_ais_with_cfar_results(
        self,
        candidate_vessel_detections: object,
        interpolated_ais_data: object,
    ) -> dict[str, Any]:
        """
        Match interpolated AIS vessel positions to CFAR vessel detections.

        This tool associates AIS vessel positions, interpolated to Sentinel-1
        SAR scene acquisition time, with candidate vessel detections produced
        by the SAR CFAR detector. It labels AIS vessels as detected or not
        detected by CFAR within the relevant SAR scene and records supporting
        matching information for recall and false-positive analysis.

        Parameters
        ----------
        candidate_vessel_detections : object
            Candidate vessel detections produced by the vessel two-parameter
            SAR CFAR detector. Expected fields may include detection
            identifier, longitude, latitude, scene identifier, and detection
            time.
        interpolated_ais_data : object
            AIS vessel positions interpolated or aligned to SAR scene time.
            Expected fields may include vessel identifier, scene identifier,
            interpolated longitude and latitude, vessel length, speed, course,
            and within-footprint indicators.

        Returns
        -------
        ais_cfar_match_records : object
            AIS vessel records annotated with whether they were detected by the
            CFAR vessel detector.

        Notes
        -----
        This tool is intended for CFAR recall and false-positive analysis. It
        does not perform AIS interpolation, run CFAR detection, compute the full
        SAR-AIS tracking score, classify vessel type, estimate vessel length
        from SAR tiles, or aggregate vessel activity over space or time.
        """
        tool_name = "match_ais_with_cfar_results"

        required_states = [
            SeaActivityStates.VESSEL_CFAR_DETECTION_COMPLETED,
            SeaActivityStates.AIS_DATA_EXTRACTED_AND_INTERPOLATED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel CFAR detections and interpolated AIS data must be "
                    "prepared before AIS-CFAR result matching."
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
            "interpolated_ais_data",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Candidate vessel detection content or interpolated AIS "
                    "content is missing before AIS-CFAR result matching."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "ais_cfar_match_records": {
                "ais_cfar_match_records_id": "ais_cfar_match_records",
                "source_candidate_vessel_detections": candidate_vessel_detections,
                "source_interpolated_ais_data": interpolated_ais_data,
                "matched_output_description": (
                    "AIS vessel records annotated with CFAR detection status, "
                    "scene identifier, vessel attributes, and matching diagnostics."
                ),
            }
        }

        completed_state = SeaActivityStates.AIS_CFAR_RESULTS_MATCHED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "AIS vessel records have been matched with CFAR vessel detections."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def calculate_ais_recall(
        self,
        ais_cfar_match_records: object,
    ) -> dict[str, Any]:
        """
        Calculate AIS-based recall for SAR CFAR vessel detections.

        This tool estimates the recall of the SAR CFAR vessel detector using
        AIS-CFAR match records. It represents recall conceptually as a function
        of vessel length and vessel spacing.

        Parameters
        ----------
        ais_cfar_match_records : object
            AIS-CFAR matching records containing AIS vessels annotated with
            whether they were detected by the CFAR vessel detector.

        Returns
        -------
        recall_function : object
            Estimated AIS recall function, represented conceptually as
            ``R(length, spacing)``.

        Notes
        -----
        This tool only calculates AIS-based CFAR recall from existing AIS-CFAR
        match records. It does not perform AIS interpolation, run CFAR
        detection, create AIS-CFAR matches, estimate vessel length from SAR
        tiles, or apply recall correction to downstream vessel activity
        estimates.
        """
        tool_name = "calculate_ais_recall"

        required_states = [
            SeaActivityStates.AIS_CFAR_RESULTS_MATCHED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "AIS-CFAR match records must be prepared before calculating "
                    "AIS recall."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if "ais_cfar_match_records" not in self.state.generated_contents:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "AIS-CFAR match record content is missing before calculating "
                    "AIS recall."
                ),
                "missing_generated_content": ["ais_cfar_match_records"],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "recall_function": {
                "recall_function_id": "recall_function",
                "source_ais_cfar_match_records": ais_cfar_match_records,
                "function_description": (
                    "Estimated AIS recall function represented conceptually as "
                    "R(length, spacing)."
                ),
            }
        }

        completed_state = SeaActivityStates.AIS_RECALL_CALCULATED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "AIS-based CFAR recall function has been calculated from "
                "AIS-CFAR match records."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def calculate_vessel_cfar_candidate_location_probability(
        self,
        interpolated_ais_data: object,
        candidate_vessel_detections: object,
    ) -> dict[str, Any]:
        """
        Calculate the location probability p for vessel CFAR candidate matches.

        This tool computes the probability term ``p`` used in SAR-AIS matching
        for each AIS vessel and CFAR candidate detection pair. Given
        AIS-derived vessel motion information and candidate CFAR detection
        locations, the tool evaluates the location probability associated with
        each candidate pairing.

        Parameters
        ----------
        interpolated_ais_data : object
            AIS vessel positions and attributes interpolated or aligned to SAR
            scene acquisition time. Expected fields may include vessel
            identifier, scene identifier, vessel class, speed, course,
            timestamp, and interpolated or likely vessel position.
        candidate_vessel_detections : object
            Candidate vessel detections produced by the SAR CFAR detector.
            Expected fields may include detection identifier, scene identifier,
            longitude, latitude, and detection time.

        Returns
        -------
        location_probability_p : object
            Probability value ``p`` for each AIS vessel and CFAR candidate
            detection pair, representing the location probability term used in
            SAR-AIS matching.

        Notes
        -----
        This tool only calculates the location probability term ``p`` for CFAR
        candidate locations. It does not compute the full SAR-AIS matching
        score, apply final matching thresholds, rank candidate matches, estimate
        vessel length, or classify vessels.
        """
        tool_name = "calculate_vessel_cfar_candidate_location_probability"

        required_states = [
            SeaActivityStates.AIS_DATA_EXTRACTED_AND_INTERPOLATED,
            SeaActivityStates.VESSEL_CFAR_DETECTION_COMPLETED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Interpolated AIS data and vessel CFAR detections must be "
                    "prepared before calculating location probability p."
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
            "interpolated_ais_data",
            "candidate_vessel_detections",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Interpolated AIS data or candidate vessel detection content "
                    "is missing before calculating location probability p."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "location_probability_p": {
                "location_probability_p_id": "location_probability_p",
                "source_interpolated_ais_data": interpolated_ais_data,
                "source_candidate_vessel_detections": candidate_vessel_detections,
                "probability_description": (
                    "Location probability p for each AIS vessel and CFAR "
                    "candidate detection pair."
                ),
            }
        }

        completed_state = SeaActivityStates.LOCATION_PROBABILITY_P_CALCULATED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Vessel CFAR candidate location probability p has been calculated."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def construct_sar_ais_matches(
        self,
        location_probability_p: object,
        interpolated_ais_data: object,
        candidate_vessel_detections: object,
        recall_function: object,
        score_threshold: float,
    ) -> dict[str, Any]:
        """
        Construct SAR-AIS matches from vessel detections and interpolated AIS records.

        This tool computes candidate matching scores between SAR CFAR vessel
        detections and AIS vessel records. It combines the CFAR candidate
        location probability term, AIS-derived vessel records, candidate CFAR
        detections, and an AIS-based recall function. Candidate pairs are
        accepted or rejected using a matching score threshold.

        Parameters
        ----------
        location_probability_p : object
            Probability term for each AIS vessel and CFAR candidate detection
            pair.
        interpolated_ais_data : object
            AIS vessel records interpolated or aligned to SAR scene acquisition
            time.
        candidate_vessel_detections : object
            Candidate vessel detections produced by the SAR CFAR detector.
        recall_function : object
            AIS-based CFAR recall function, conceptually represented as
            ``R(length, spacing)``.
        score_threshold : float
            Matching score threshold used to accept or reject candidate pairs.

        Returns
        -------
        sar_ais_matches : object
            SAR-AIS match records containing detection identifiers, AIS vessel
            identifiers, matching scores, and accept/reject labels.

        Notes
        -----
        This tool constructs SAR-AIS matches only. It does not interpolate AIS
        positions, run CFAR detection, calculate the CFAR candidate location
        probability term, estimate vessel length from SAR tiles, or compute the
        AIS recall function.
        """
        tool_name = "construct_sar_ais_matches"

        required_states = [
            SeaActivityStates.LOCATION_PROBABILITY_P_CALCULATED,
            SeaActivityStates.AIS_DATA_EXTRACTED_AND_INTERPOLATED,
            SeaActivityStates.VESSEL_CFAR_DETECTION_COMPLETED,
            SeaActivityStates.AIS_RECALL_CALCULATED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Location probability, interpolated AIS data, vessel CFAR "
                    "detections, and AIS recall must be prepared before "
                    "constructing SAR-AIS matches."
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
            "location_probability_p",
            "interpolated_ais_data",
            "candidate_vessel_detections",
            "recall_function",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Required SAR-AIS matching input content is missing before "
                    "constructing SAR-AIS matches."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "sar_ais_matches": {
                "sar_ais_matches_id": "sar_ais_matches",
                "source_location_probability_p": location_probability_p,
                "source_interpolated_ais_data": interpolated_ais_data,
                "source_candidate_vessel_detections": candidate_vessel_detections,
                "source_recall_function": recall_function,
                "score_threshold": score_threshold,
                "match_record_description": (
                    "SAR-AIS match records containing detection identifiers, "
                    "AIS vessel identifiers, matching scores, and accept/reject "
                    "labels."
                ),
            }
        }

        completed_state = SeaActivityStates.SAR_AIS_MATCHES_CONSTRUCTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "SAR-AIS matches have been constructed using the requested "
                "matching score threshold."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def exclude_radar_ambiguities(
        self,
        candidate_detections: object,
    ) -> dict[str, Any]:
        """
        Exclude radar ambiguity artefacts from SAR CFAR detections.

        This tool filters candidate SAR detections by removing detections that
        are consistent with radar ambiguity artefacts. The available CFAR
        detection types determine whether vessel detections, infrastructure
        detections, or both are processed.

        Parameters
        ----------
        candidate_detections : object
            Candidate vessel detections, candidate infrastructure detections, or
            a combined candidate detection object produced by the two-parameter
            CFAR detector.

        Returns
        -------
        valid_candidate_vessel_detections : object
            Candidate vessel detections after radar ambiguity filtering, if
            vessel CFAR detections are available.

        valid_candidate_infrastructure_detections : object
            Candidate infrastructure detections after radar ambiguity filtering,
            if infrastructure CFAR detections are available.

        Notes
        -----
        This tool only filters radar ambiguity artefacts from existing CFAR
        detections. It does not run CFAR detection, construct SAR masks,
        classify vessel or infrastructure detections, estimate vessel length,
        or perform AIS matching.
        """
        tool_name = "exclude_radar_ambiguities"

        vessel_state = SeaActivityStates.VESSEL_CFAR_DETECTION_COMPLETED
        infrastructure_state = (
            SeaActivityStates.INFRASTRUCTURE_CFAR_DETECTION_COMPLETED
        )

        has_vessel_cfar = self.has_state(vessel_state)
        has_infrastructure_cfar = self.has_state(infrastructure_state)

        if not has_vessel_cfar and not has_infrastructure_cfar:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "At least one CFAR detection result must be prepared before "
                    "excluding radar ambiguities."
                ),
                "required_states": [
                    vessel_state,
                    infrastructure_state,
                ],
                "missing_states": [
                    state_name
                    for state_name in [
                        vessel_state,
                        infrastructure_state,
                    ]
                    if not self.has_state(state_name)
                ],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": [
                        vessel_state,
                        infrastructure_state,
                    ],
                },
            }

        missing_generated_content = []

        if (
            has_vessel_cfar
            and "candidate_vessel_detections"
            not in self.state.generated_contents
        ):
            missing_generated_content.append("candidate_vessel_detections")

        if (
            has_infrastructure_cfar
            and "candidate_infrastructure_detections"
            not in self.state.generated_contents
        ):
            missing_generated_content.append(
                "candidate_infrastructure_detections"
            )

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Candidate detection content is missing before excluding "
                    "radar ambiguities."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": [
                        state_name
                        for state_name, has_state in [
                            (vessel_state, has_vessel_cfar),
                            (infrastructure_state, has_infrastructure_cfar),
                        ]
                        if has_state
                    ],
                },
            }

        generated = {}
        completed_states = []
        required_states = []

        if has_vessel_cfar:
            generated["valid_candidate_vessel_detections"] = {
                "valid_candidate_vessel_detections_id": (
                    "valid_candidate_vessel_detections"
                ),
                "source_candidate_detections": candidate_detections,
                "source_candidate_vessel_detections": (
                    self.state.generated_contents["candidate_vessel_detections"]
                ),
                "target_type": "vessel",
                "filtering_rule": "radar_ambiguity_exclusion",
            }
            completed_states.append(
                SeaActivityStates.VESSEL_RADAR_AMBIGUITIES_EXCLUDED
            )
            required_states.append(vessel_state)

        if has_infrastructure_cfar:
            generated["valid_candidate_infrastructure_detections"] = {
                "valid_candidate_infrastructure_detections_id": (
                    "valid_candidate_infrastructure_detections"
                ),
                "source_candidate_detections": candidate_detections,
                "source_candidate_infrastructure_detections": (
                    self.state.generated_contents[
                        "candidate_infrastructure_detections"
                    ]
                ),
                "target_type": "infrastructure",
                "filtering_rule": "radar_ambiguity_exclusion",
            }
            completed_states.append(
                SeaActivityStates.INFRASTRUCTURE_RADAR_AMBIGUITIES_EXCLUDED
            )
            required_states.append(infrastructure_state)

        for completed_state in completed_states:
            self.mark_state(completed_state)

        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Radar ambiguity artefacts have been excluded from the "
                "available candidate detections."
            ),
            "generated": generated,
            "state": {
                "completed": completed_states,
                "required": required_states,
            },
        }

    @agent_tool
    def remove_fixed_structures_from_vessel_detections(
        self,
        valid_candidate_vessel_detections: object,
    ) -> dict[str, Any]:
        """
        Remove fixed-structure detections from vessel candidate detections.

        This tool filters valid candidate vessel detections by removing
        detections that spatially coincide with known or persistent fixed
        offshore structures. It is intended to reduce false vessel detections
        caused by offshore infrastructure, fixed platforms, or repeated
        stationary objects.

        Parameters
        ----------
        valid_candidate_vessel_detections : object
            Candidate vessel detections after radar ambiguity filtering.

        Returns
        -------
        fixed_structure_removed_vessel_detections : object
            Vessel detections after removing fixed-structure candidates.

        Notes
        -----
        This tool only removes fixed-structure candidates from existing vessel
        detections. It does not run CFAR detection, exclude radar ambiguities,
        classify infrastructure, construct fixed-structure reference layers,
        estimate vessel length, or perform AIS matching.
        """
        tool_name = "remove_fixed_structures_from_vessel_detections"

        required_states = [
            SeaActivityStates.VESSEL_RADAR_AMBIGUITIES_EXCLUDED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Valid candidate vessel detections must be prepared before "
                    "removing fixed-structure detections."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if "valid_candidate_vessel_detections" not in self.state.generated_contents:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Valid candidate vessel detection content is missing before "
                    "removing fixed-structure detections."
                ),
                "missing_generated_content": [
                    "valid_candidate_vessel_detections",
                ],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "fixed_structure_removed_vessel_detections": {
                "fixed_structure_removed_vessel_detections_id": (
                    "fixed_structure_removed_vessel_detections"
                ),
                "source_valid_candidate_vessel_detections": (
                    valid_candidate_vessel_detections
                ),
                "filtering_rule": self.sat_defaults.fixed_structure_removal_rule,
            }
        }

        completed_state = (
            SeaActivityStates.FIXED_STRUCTURES_REMOVED_FROM_VESSEL_DETECTIONS
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Fixed-structure detections have been removed from valid "
                "candidate vessel detections."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def apply_fixed_structure_temporal_selection_and_interpolation(
        self,
        valid_candidate_infrastructure_detections: object,
    ) -> dict[str, Any]:
        """
        Apply temporal consistency filtering and interpolation to fixed-structure
        detections.

        This tool processes valid candidate infrastructure detections over a
        time series. It fills missing detections for fixed structures that are
        detected in both the previous and following time steps, and removes
        isolated detections that appear in only a single time step.

        Parameters
        ----------
        valid_candidate_infrastructure_detections : object
            Candidate infrastructure detections after radar ambiguity filtering.

        Returns
        -------
        temporally_consistent_infrastructure_detections : object
            Infrastructure detections after temporal interpolation and removal
            of isolated single-time-step detections.

        Notes
        -----
        This tool only performs temporal consistency filtering and interpolation
        for existing infrastructure detections. It does not run CFAR detection,
        construct SAR composites, classify infrastructure as oil, wind, other,
        or noise, or aggregate infrastructure activity over space or time.
        """
        tool_name = "apply_fixed_structure_temporal_selection_and_interpolation"

        required_states = [
            SeaActivityStates.INFRASTRUCTURE_RADAR_AMBIGUITIES_EXCLUDED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Valid candidate infrastructure detections must be prepared "
                    "before fixed-structure temporal selection and interpolation."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if (
            "valid_candidate_infrastructure_detections"
            not in self.state.generated_contents
        ):
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Valid candidate infrastructure detection content is missing "
                    "before fixed-structure temporal selection and interpolation."
                ),
                "missing_generated_content": [
                    "valid_candidate_infrastructure_detections",
                ],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "temporally_consistent_infrastructure_detections": {
                "temporally_consistent_infrastructure_detections_id": (
                    "temporally_consistent_infrastructure_detections"
                ),
                "source_valid_candidate_infrastructure_detections": (
                    valid_candidate_infrastructure_detections
                ),
                "time_step": self.sat_defaults.fixed_structure_temporal_time_step,
                "interpolation_rule": (
                    self.sat_defaults.fixed_structure_temporal_interpolation_rule
                ),
                "single_time_step_removal": (
                    self.sat_defaults.fixed_structure_single_time_step_removal
                ),
            }
        }

        completed_state = (
            SeaActivityStates
            .FIXED_STRUCTURE_TEMPORAL_SELECTION_AND_INTERPOLATION_COMPLETED
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Fixed-structure detections have been temporally selected and "
                "interpolated."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def construct_vessel_time_series_data(
        self,
        vessel_presence_probability: object,
        rolling_window_days: int,
        resolution_m: float,
    ) -> dict[str, Any]:
        """
        Construct vessel time series data from vessel presence probability.

        This tool constructs vessel time series data by aggregating vessel
        presence probability over a rolling temporal window and a specified
        spatial resolution.

        Parameters
        ----------
        vessel_presence_probability : object
            Predicted probability that each candidate object is a vessel.
        rolling_window_days : int
            Length of the rolling temporal window in days.
        resolution_m : float
            Spatial resolution in meters used to construct the time series data.

        Returns
        -------
        vessel_time_series_data : object
            Vessel time series data constructed from vessel presence probability,
            rolling temporal window length, and spatial resolution.

        Notes
        -----
        This tool only constructs vessel time series data. It does not run CFAR
        detection, remove radar ambiguities, estimate vessel presence, estimate
        vessel length, construct SAR-AIS matches, classify fishing/non-fishing
        activity, or aggregate vessel activity by administrative regions.
        """
        tool_name = "construct_vessel_time_series_data"

        required_states = [
            SeaActivityStates.VESSEL_PRESENCE_AND_LENGTH_ESTIMATED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel presence probability must be prepared before "
                    "constructing vessel time series data."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if "vessel_presence_probability" not in self.state.generated_contents:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel presence probability content is missing before "
                    "constructing vessel time series data."
                ),
                "missing_generated_content": ["vessel_presence_probability"],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "vessel_time_series_data": {
                "vessel_time_series_data_id": "vessel_time_series_data",
                "source_vessel_presence_probability": vessel_presence_probability,
                "rolling_window_days": rolling_window_days,
                "resolution_m": resolution_m,
            }
        }

        completed_state = SeaActivityStates.VESSEL_TIME_SERIES_DATA_CONSTRUCTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Vessel time series data have been constructed from vessel "
                "presence probability."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def select_and_interpolate_time_series_data(
        self,
        vessel_time_series_data: object,
        highest_missing_data_accepted_percent: float,
        linear_interpolation: bool,
    ) -> dict[str, Any]:
        """
        Select and interpolate vessel time series data.

        This tool selects valid vessel time series records according to the
        highest accepted proportion of missing data, then applies interpolation
        to fill missing values when requested.

        Parameters
        ----------
        vessel_time_series_data : object
            Vessel time series data constructed from vessel presence
            probability, rolling temporal window length, and spatial resolution.
        highest_missing_data_accepted_percent : float
            Highest proportion of missing data accepted, expressed as a
            percentage.
        linear_interpolation : bool
            Whether to use linear interpolation for missing time-series values.

        Returns
        -------
        selected_interpolated_vessel_time_series_data : object
            Vessel time series data after missing-data selection and
            interpolation.

        Notes
        -----
        This tool only performs time series selection and interpolation. It does
        not construct vessel time series data, estimate vessel presence,
        estimate vessel length, run CFAR detection, construct SAR-AIS matches,
        or classify fishing/non-fishing activity.
        """
        tool_name = "select_and_interpolate_time_series_data"

        required_states = [
            SeaActivityStates.VESSEL_TIME_SERIES_DATA_CONSTRUCTED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel time series data must be constructed before time "
                    "series selection and interpolation."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if "vessel_time_series_data" not in self.state.generated_contents:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel time series data content is missing before time "
                    "series selection and interpolation."
                ),
                "missing_generated_content": ["vessel_time_series_data"],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "selected_interpolated_vessel_time_series_data": {
                "selected_interpolated_vessel_time_series_data_id": (
                    "selected_interpolated_vessel_time_series_data"
                ),
                "source_vessel_time_series_data": vessel_time_series_data,
                "highest_missing_data_accepted_percent": (
                    highest_missing_data_accepted_percent
                ),
                "linear_interpolation": linear_interpolation,
            }
        }

        completed_state = (
            SeaActivityStates.TIME_SERIES_DATA_SELECTED_AND_INTERPOLATED
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Vessel time series data have been selected and interpolated "
                "using the requested missing-data threshold and interpolation "
                "setting."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }





