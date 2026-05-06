from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rsare.apps.farm_app import App


# =============================================================================
# SAR defaults
# =============================================================================

@dataclass(frozen=True)
class SeaActivityDefaults:
    """
    Default or paper-recommended parameter values for sea activity workflows.

    Only confirmed default values should be placed here.
    """

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    # Google Earth Engine Sentinel-1 GRD collection name.
    sentinel1_collection: str = "COPERNICUS/S1_GRD"

    # Sentinel-1 platform selector.
    # "S1A" means Sentinel-1A, "S1B" means Sentinel-1B,
    # and "S1AB" means using both platforms in the mock workflow.
    sentinel1_satellite: str = "S1AB"

    # Sentinel-1 acquisition mode.
    # The paper-style SAR workflow uses Interferometric Wide swath mode.
    sentinel1_instrument_mode: str = "IW"

    # Required Sentinel-1 polarization bands.
    # The paper-style workflow requires both VV and VH.
    sentinel1_polarizations_required: tuple[str, ...] = ("VV", "VH")

    # Earth Engine resolution metadata filter.
    # The paper-style workflow uses high-resolution GRD scenes.
    sentinel1_resolution_metadata: str = "H"

    # Nominal working resolution in meters.
    # The paper-style workflow uses approximately 20 m resolution.
    sentinel1_nominal_resolution_m: float = 20.0

    # Google Earth Engine Sentinel-2 collection name.
    sentinel2_collection: str = "COPERNICUS/S2"

    # Sentinel-2 platform selector.
    # "S2A" means Sentinel-2A, "S2B" means Sentinel-2B,
    # and "S2AB" means using both platforms in the mock workflow.
    sentinel2_satellite: str = "S2AB"

    # Default Sentinel-2 RGB and near-infrared bands.
    # B4 is red, B3 is green, B2 is blue, and B8 is near-infrared.
    sentinel2_rgb_nir_bands: tuple[str, ...] = ("B4", "B3", "B2", "B8")

    # Nominal spatial resolution in meters for the default RGB and NIR bands.
    sentinel2_rgb_nir_resolution_m: int = 10

    # Default source table for AIS messages or pipeline-processed AIS records.
    ais_source_table: str = "gfw_ais_pipeline_table"

    # Default source or provider for chlorophyll products.
    chlorophyll_source: str = "NASA Ocean Biology Processing Group"

    # Default source or provider for sea-surface temperature products.
    sea_surface_temperature_source: str = (
        "Copernicus Global Ocean Analysis and Forecast System"
    )

    # Default source or provider for ocean current products.
    ocean_current_source: str = "Copernicus Global Ocean Analysis and Forecast System"

    # Default source or provider for distance-to-shore products.
    distance_to_shore_source: str = "NASA OBPG/PacIOOS"

    # Default source or provider for distance-to-port products.
    distance_to_port_source: str = "Global Fishing Watch"

    # Default source or provider for bathymetry products.
    bathymetry_source: str = "GEBCO"

    # Default source or provider for Exclusive Economic Zone boundary data.
    eez_source: str = "Marine Regions"

    # Default offshore infrastructure reference data sources.
    infrastructure_sources: tuple[str, ...] = (
        "BOEM",
        "UK Hydrographic Office",
        "California Department of Fish and Wildlife",
        "Geoscience Australia",
    )

    # Default source for synthetic shoreline data.
    shoreline_source: str = "synthetic_shoreline_sources"

    # Default sea-ice product name.
    sea_ice_product: str = "Multisensor Analyzed Sea Ice Extent - Northern Hemisphere"

    # Default sea-ice product version.
    sea_ice_version: str = "Version 1"

    # Default geographic coverage for the sea-ice product.
    sea_ice_coverage_region: str = "Northern Hemisphere"

    # Default source or provider for global road network data.
    roads_source: str = "gROADSv1"

    # Default source or dataset name for global oil-region spatial data.
    oil_regions_source: str = "global_oil_regions_reference"

    # -------------------------------------------------------------------------
    # Operation
    # -------------------------------------------------------------------------

    # Reference shoreline buffer distance in kilometers.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    shoreline_buffer_km: float = 1.0

    # Reference coastline distance threshold in kilometers for road, bridge,
    # and vehicle false-positive masking. This value is stored for oracle
    # construction and internal test reference, but it should not be exposed
    # as a default value in non-Data tool signatures.
    road_bridge_vehicle_coastline_distance_threshold_km: float = 3.0

    # Reference highway vehicle speed in kilometers per hour for road-related
    # false-positive masking. This value is stored for oracle construction and
    # internal test reference, but it should not be exposed as a default value
    # in non-Data tool signatures.
    highway_vehicle_speed_kmh: float = 135.0

    # Reference primary-road vehicle speed in kilometers per hour for
    # road-related false-positive masking. This value is stored for oracle
    # construction and internal test reference, but it should not be exposed
    # as a default value in non-Data tool signatures.
    primary_road_vehicle_speed_kmh: float = 100.0

    # Reference inward border clipping distance in meters for Sentinel-1 SAR scenes.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    sar_scene_border_clipping_buffer_m: float = 500.0

    # Reference maximum cloud coverage percentage for Sentinel-2 filtering.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    sentinel2_max_cloud_coverage_percent: float = 20.0

    # Reference Sentinel-2 cloud mask band for QA-based cloud filtering.
    # This value is stored for oracle construction and internal test reference.
    sentinel2_cloud_mask_band: str = "QA60"

    # Reference SAR-AIS matching score threshold.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    sar_ais_matching_score_threshold: float = 7.4e-6

    # Reference radar ambiguity angle rules.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    radar_ambiguity_angle_rules: dict[str, float] = field(
        default_factory=lambda: {
            "low_incidence_angle": 0.363,
            "middle_incidence_angle": 0.308,
            "high_incidence_angle": 0.359,
        }
    )

    # Reference angular tolerance in degrees for radar ambiguity filtering.
    radar_ambiguity_psi_tolerance_deg: float = 0.004

    # Reference rule used to remove one detection from a radar ambiguity pair.
    radar_ambiguity_remove_rule: str = "remove_dimmer_detection"

    # Reference rule used to remove fixed-structure candidates from vessel detections.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    fixed_structure_removal_rule: str = "remove_known_or_persistent_fixed_structures"

    # Reference temporal step for fixed-structure temporal filtering.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    fixed_structure_temporal_time_step: str = "monthly"

    # Reference rule used to interpolate missing fixed-structure detections.
    fixed_structure_temporal_interpolation_rule: str = (
        "interpolate_when_detected_in_previous_and_following_time_steps"
    )

    # Reference rule for removing isolated fixed-structure detections.
    fixed_structure_single_time_step_removal: bool = True

    # Reference rolling temporal window length in days for vessel time series construction.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    vessel_time_series_rolling_window_days: int = 24

    # Reference spatial resolution in meters for vessel time series construction.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    vessel_time_series_resolution_m: float = 550.0

    # Reference highest proportion of missing data accepted for vessel time series
    # selection, expressed as a percentage.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    vessel_time_series_highest_missing_data_accepted_percent: float = 9.1

    # Reference interpolation setting for vessel time series data.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    vessel_time_series_linear_interpolation: bool = True

    # -------------------------------------------------------------------------
    # Preparation
    # -------------------------------------------------------------------------

    # Reference temporal window length in months for SAR median composites.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    sar_median_composite_window_months: int = 6

    # Reference temporal step for SAR median composite construction.
    sar_median_composite_step: str = "monthly"

    # Reference minimum number of valid SAR images for composite construction.
    sar_median_composite_min_num_images: int = 5

    # Reference maximum number of SAR images sampled within each composite window.
    sar_median_composite_max_num_images: int = 40

    # Reference reducer for SAR median composite construction.
    sar_median_composite_reducer: str = "median"

    # Reference SAR polarization band for infrastructure composite construction.
    sar_median_composite_detection_band: str = "VH"

    # Reference vessel inference tile size in pixels.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    vessel_detection_tile_size_px: int = 80

    # Reference SAR input bands for vessel inference tile extraction.
    vessel_detection_tile_input_bands: tuple[str, ...] = ("VH", "VV")

    # Reference rule for centering vessel inference tiles.
    vessel_detection_tile_center_rule: str = "center_on_candidate_detection"

    # Reference infrastructure SAR tile size in pixels.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    infrastructure_sar_tile_size_px: int = 100

    # Reference SAR input bands for infrastructure SAR tile extraction.
    infrastructure_sar_tile_input_bands: tuple[str, ...] = ("VH", "VV")

    # Reference rule for centering infrastructure SAR tiles.
    infrastructure_sar_tile_center_rule: str = "center_on_candidate_detection"

    # Reference infrastructure optical tile size in pixels.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    infrastructure_optical_tile_size_px: int = 100

    # Reference Sentinel-2 optical input bands for infrastructure optical tiles.
    # B4 is red, B3 is green, B2 is blue, and B8 is near-infrared.
    infrastructure_optical_tile_input_bands: tuple[str, ...] = (
        "B4",
        "B3",
        "B2",
        "B8",
    )

    # Reference rule for centering infrastructure optical tiles.
    infrastructure_optical_tile_center_rule: str = "center_on_candidate_detection"

    # Reference spatial resolution in kilometers for SAR vessel data raster construction.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    sar_vessel_raster_spatial_resolution_km: float = 1.0

    # Reference aggregation rule for SAR vessel data raster construction.
    sar_vessel_raster_aggregation_method: str = (
        "aggregate_vessel_presence_density_and_average_length"
    )

    # Reference spatial resolution in kilometers for AIS vessel data raster construction.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    ais_vessel_raster_spatial_resolution_km: float = 1.0

    # Reference aggregation rule for AIS vessel data raster construction.
    ais_vessel_raster_aggregation_method: str = (
        "aggregate_ais_vessel_density_and_average_length"
    )

    # Reference spatial resolution in kilometers for environmental and physical
    # raster construction. This value is stored for oracle construction and
    # internal test reference, but it should not be exposed as a default value
    # in non-Data tool signatures.
    environmental_physical_raster_spatial_resolution_km: float = 1.0

    # Reference aggregation or resampling rule for environmental and physical
    # raster construction.
    environmental_physical_raster_aggregation_method: str = (
        "resample_and_stack_environmental_physical_features"
    )

    # Reference raster tile size in pixels for fishing/non-fishing model inputs.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    fishing_model_raster_tile_size_px: int = 100

    # Reference spatial resolution in kilometers for fishing/non-fishing raster tiles.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    fishing_model_raster_spatial_resolution_km: float = 1.0

    # Reference rule for centering fishing/non-fishing raster feature tiles.
    fishing_model_tile_center_rule: str = "center_on_vessel_presence_probability"


    # -------------------------------------------------------------------------
    # Training
    # -------------------------------------------------------------------------

    # Reference vessel training tile size in pixels.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    vessel_training_tile_size_px: int = 80

    # Reference test-set fraction for vessel model training.
    # The paper-style workflow uses a 20% holdout test set.
    vessel_training_train_test_split: float = 0.2

    # Reference number of cross-validation folds for vessel model selection.
    vessel_training_cross_validation_folds: int = 5

    # Reference test-set fraction for infrastructure model training.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a function parameter.
    infrastructure_training_train_test_split: float = 0.2

    # Reference number of cross-validation folds for infrastructure model selection.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a function parameter.
    infrastructure_training_cross_validation_folds: int = 5

    # Reference test-set fraction for fishing/non-fishing model training.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a function parameter.
    fishing_nonfishing_training_train_test_split: float = 0.2

    # Reference number of cross-validation folds for fishing/non-fishing model selection.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a function parameter.
    fishing_nonfishing_training_cross_validation_folds: int = 5

    # Reference class sampling ratio for fishing/non-fishing dataset construction.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in the function signature.
    fishing_nonfishing_class_sampling_ratio: float = 1.0


    # -------------------------------------------------------------------------
    # Model
    # -------------------------------------------------------------------------

    # Reference CFAR detection band.
    # This value is stored for oracle construction and internal test reference,
    # but it should not be exposed as a default value in non-Data tool signatures.
    cfar_detection_band: str = "VH"

    # Reference vessel CFAR inner background window size in pixels.
    vessel_cfar_inner_window_px: int = 200

    # Reference vessel CFAR outer background window size in pixels.
    vessel_cfar_outer_window_px: int = 600

    # Reference vessel CFAR post-processing dilation radius.
    vessel_cfar_dilation_radius: float = 60.0

    # Reference infrastructure CFAR inner background window size in pixels.
    infrastructure_cfar_inner_window_px: int = 140

    # Reference infrastructure CFAR outer background window size in pixels.
    infrastructure_cfar_outer_window_px: int = 200

    # Reference infrastructure CFAR post-processing dilation radius.
    infrastructure_cfar_dilation_radius: float = 45.0

    # Reference Sentinel-1A time-dependent CFAR threshold multipliers.
    cfar_threshold_multiplier_nt_s1a: dict[str, int] = field(
        default_factory=lambda: {
            "2016-01_to_2016-10": 14,
            "2016-09_to_2017-01": 14,
            "2017-01_to_2018-03": 14,
            "2018-03_to_2020-01": 16,
            "2020-01_to_2021-12": 22,
        }
    )

    # Reference Sentinel-1B time-dependent CFAR threshold multipliers.
    cfar_threshold_multiplier_nt_s1b: dict[str, int | None] = field(
        default_factory=lambda: {
            "2016-01_to_2016-10": None,
            "2016-09_to_2017-01": 18,
            "2017-01_to_2018-03": 17,
            "2018-03_to_2020-01": 19,
            "2020-01_to_2021-12": 24,
        }
    )

    # -------------------------------------------------------------------------
    # CFAR mock scoring defaults
    # -------------------------------------------------------------------------

    # Reference vessel CFAR scoring scales.
    # Larger scales make the score less sensitive to deviations from the optimum.
    vessel_cfar_inner_window_score_scale_px: float = 80.0
    vessel_cfar_outer_window_score_scale_px: float = 180.0

    # Reference infrastructure CFAR scoring scales.
    infrastructure_cfar_inner_window_score_scale_px: float = 50.0
    infrastructure_cfar_outer_window_score_scale_px: float = 120.0

# =============================================================================
# State names
# =============================================================================

class SeaActivityStates:
    """
    Centralized workflow state names for SeaActivityTools.

    State names are used to represent completed tool steps and to express
    dependencies between tools.
    """

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    SAR_SCENES_LOADED = "sar_scenes_loaded"
    OPTICAL_SCENES_LOADED = "optical_scenes_loaded"
    AIS_DATA_LOADED = "ais_data_loaded"
    CHLOROPHYLL_DATA_LOADED = "chlorophyll_data_loaded"
    SEA_SURFACE_TEMPERATURE_DATA_LOADED = "sea_surface_temperature_data_loaded"
    OCEAN_CURRENT_SPEED_DATA_LOADED = "ocean_current_speed_data_loaded"
    DISTANCE_TO_SHORE_DATA_LOADED = "distance_to_shore_data_loaded"
    DISTANCE_TO_PORT_DATA_LOADED = "distance_to_port_data_loaded"
    BATHYMETRY_DATA_LOADED = "bathymetry_data_loaded"
    EEZ_BOUNDARIES_LOADED = "eez_boundaries_loaded"
    INFRASTRUCTURE_DATA_LOADED = "infrastructure_data_loaded"
    SYNTHETIC_SHORELINE_DATA_LOADED = "synthetic_shoreline_data_loaded"
    SEA_ICE_DATA_LOADED = "sea_ice_data_loaded"
    GLOBAL_ROADS_DATA_LOADED = "global_roads_data_loaded"
    GLOBAL_OIL_REGIONS_DATA_LOADED = "global_oil_regions_data_loaded"

    # -------------------------------------------------------------------------
    # Operation
    # -------------------------------------------------------------------------

    SHORELINE_BUFFER_MASK_CONSTRUCTED = "shoreline_buffer_mask_constructed"

    OCEAN_MASK_CONSTRUCTED = "ocean_mask_constructed"

    SEA_ICE_FILTERING_MASK_CONSTRUCTED = "sea_ice_filtering_mask_constructed"

    ROAD_BRIDGE_VEHICLE_MASK_CONSTRUCTED = "road_bridge_vehicle_mask_constructed"

    SAR_SCENES_FILTERED_WITH_MASK = "sar_scenes_filtered_with_mask"

    SAR_SCENE_BORDERS_CLIPPED = "sar_scene_borders_clipped"

    SENTINEL2_CLOUD_FILTERED_WITH_QA60 = "sentinel2_cloud_filtered_with_qa60"

    AIS_DATA_EXTRACTED_AND_INTERPOLATED = "ais_data_extracted_and_interpolated"

    OFFSHORE_INFRASTRUCTURE_ANALYSIS_POLYGONS_DEFINED = "offshore_infrastructure_analysis_polygons_defined"

    AIS_CFAR_RESULTS_MATCHED = "ais_cfar_results_matched"

    AIS_RECALL_CALCULATED = "ais_recall_calculated"

    LOCATION_PROBABILITY_P_CALCULATED = "location_probability_p_calculated"

    SAR_AIS_MATCHES_CONSTRUCTED = "sar_ais_matches_constructed"

    VESSEL_RADAR_AMBIGUITIES_EXCLUDED = "vessel_radar_ambiguities_excluded"
    INFRASTRUCTURE_RADAR_AMBIGUITIES_EXCLUDED = "infrastructure_radar_ambiguities_excluded"

    FIXED_STRUCTURES_REMOVED_FROM_VESSEL_DETECTIONS = "fixed_structures_removed_from_vessel_detections"

    FIXED_STRUCTURE_TEMPORAL_SELECTION_AND_INTERPOLATION_COMPLETED = "fixed_structure_temporal_selection_and_interpolation_completed"

    VESSEL_TIME_SERIES_DATA_CONSTRUCTED = "vessel_time_series_data_constructed"

    TIME_SERIES_DATA_SELECTED_AND_INTERPOLATED = "time_series_data_selected_and_interpolated"


    # -------------------------------------------------------------------------
    # Preparation
    # -------------------------------------------------------------------------

    SAR_MEDIAN_COMPOSITES_CONSTRUCTED = "sar_median_composites_constructed"

    VESSEL_DETECTION_TILES_EXTRACTED = "vessel_detection_tiles_extracted"

    INFRASTRUCTURE_SAR_TILES_EXTRACTED = "infrastructure_sar_tiles_extracted"

    INFRASTRUCTURE_OPTICAL_TILES_EXTRACTED = "infrastructure_optical_tiles_extracted"

    SAR_VESSEL_DATA_RASTERS_CONSTRUCTED = "sar_vessel_data_rasters_constructed"

    AIS_VESSEL_DATA_RASTERS_CONSTRUCTED = "ais_vessel_data_rasters_constructed"

    ENVIRONMENTAL_PHYSICAL_DATA_RASTERS_CONSTRUCTED = "environmental_physical_data_rasters_constructed"

    RASTER_FEATURE_TILE_STACK_GENERATED = "raster_feature_tile_stack_generated"


    # -------------------------------------------------------------------------
    # Training
    # -------------------------------------------------------------------------

    VESSEL_TRAINING_DATASET_CONSTRUCTED = "vessel_training_dataset_constructed"

    INFRASTRUCTURE_TRAINING_DATASET_CONSTRUCTED = "infrastructure_training_dataset_constructed"

    FISHING_NONFISHING_TRAINING_DATASET_CONSTRUCTED = "fishing_nonfishing_training_dataset_constructed"

    VESSEL_MODEL_TRAINED_AND_VALIDATED = "vessel_model_trained_and_validated"

    INFRASTRUCTURE_MODEL_TRAINED_AND_VALIDATED = "infrastructure_model_trained_and_validated"

    FISHING_NONFISHING_MODEL_TRAINED_AND_VALIDATED = "fishing_nonfishing_model_trained_and_validated"


    # -------------------------------------------------------------------------
    # Model
    # -------------------------------------------------------------------------

    VESSEL_CFAR_DETECTION_COMPLETED = "vessel_cfar_detection_completed"
    INFRASTRUCTURE_CFAR_DETECTION_COMPLETED = "infrastructure_cfar_detection_completed"

    VESSEL_PRESENCE_AND_LENGTH_ESTIMATED = "vessel_presence_and_length_estimated"

    INFRASTRUCTURE_CLASSIFICATION_COMPLETED = "infrastructure_classification_completed"

    FISHING_NONFISHING_CLASSIFICATION_COMPLETED = "fishing_nonfishing_classification_completed"



# =============================================================================
# State management
# =============================================================================

@dataclass
class SeaActivityToolState:
    """
    Runtime state for workflow-testing tools.

    This state is intentionally lightweight. It only records:
    - completed_states: states completed by successful mock tool calls.
    - generated_contents: mock outputs produced by tools.
    """

    completed_states: set[str] = field(default_factory=set)
    generated_contents: dict[str, Any] = field(default_factory=dict)

    def has_state(self, state_name: str) -> bool:
        """Return whether a workflow state has been completed."""
        return state_name in self.completed_states

    def mark_state(self, state_name: str) -> None:
        """Mark a workflow state as completed."""
        self.completed_states.add(state_name)

    def store_generated_content(self, key: str, value: Any) -> None:
        """Store mock content generated by a tool."""
        self.generated_contents[key] = value

    def clear(self) -> None:
        """Clear all workflow-testing state."""
        self.completed_states.clear()
        self.generated_contents.clear()


# =============================================================================
# Base tool app
# =============================================================================

class SeaActivityTools(App):
    """
    Base app for SAR-based sea activity workflow testing.

    This base class should not expose concrete @agent_tool methods.
    Concrete tool categories should be implemented in subclasses:
    - SAT_Data
    - SAT_Preparation
    - SAT_Training
    - SAT_Model
    - SAT_Operation
    """

    def __init__(
        self,
        name: str | None = None,
        state: SeaActivityToolState | None = None,
        sat_defaults: SeaActivityDefaults | None = None,
    ):
        super().__init__(name=name or self.__class__.__name__)
        self.state = state if state is not None else SeaActivityToolState()
        self.sat_defaults = sat_defaults if sat_defaults is not None else SeaActivityDefaults()

    def has_state(self, state_name: str) -> bool:
        """Return whether a required workflow state has been completed."""
        return self.state.has_state(state_name)

    def mark_state(self, state_name: str) -> None:
        """Mark a workflow state as completed."""
        self.state.mark_state(state_name)

    def store_generated_content(self, key: str, value: Any) -> None:
        """Store mock content generated by a tool."""
        self.state.store_generated_content(key, value)

    def get_state(self) -> dict[str, Any]:
        """
        Return a serializable snapshot of the workflow-testing state.
        """
        return {
            "name": self.name,
            "completed_states": sorted(self.state.completed_states),
            "generated_contents": self.state.generated_contents,
        }

    def reset(self) -> None:
        """
        Reset deterministic RNG and clear workflow-testing state.

        Note:
            If multiple SAT_* apps share the same state object, calling reset()
            on any one of them clears the shared state for all of them.
        """
        super().reset()
        self.state.clear()

    def get_missing_states(self, required_states: list[str]) -> list[str]:
        """
        Return required workflow states that have not been completed.
        """
        return [
            state_name
            for state_name in required_states
            if not self.has_state(state_name)
        ]
