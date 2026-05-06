from __future__ import annotations
from typing import Any
import numpy as np

from rsare.agents.agent.toolset_builder import agent_tool
from rsare.apps.sar.sea_activity_tools import (
    SeaActivityDefaults,
    SeaActivityStates,
    SeaActivityToolState,
    SeaActivityTools,
)


class SAT_Model(SeaActivityTools):
    """
    Model tools for SAR-based sea activity workflow testing.
    """

    def __init__(
        self,
        state: SeaActivityToolState | None = None,
        sat_defaults: SeaActivityDefaults | None = None,
    ):
        super().__init__(
            name="SAT_Model",
            state=state,
            sat_defaults=sat_defaults,
        )


    def _get_cfar_window_scoring_config(
        self,
        target_type: str,
    ) -> dict[str, float | int]:
        """
        Return target-type-specific CFAR window scoring configuration.

        The returned configuration is used only for mock quality scoring. It is
        not exposed to the Agent as a tool parameter.
        """
        if target_type == "vessel":
            return {
                "optimal_inner_window_px": (
                    self.sat_defaults.vessel_cfar_inner_window_px
                ),
                "optimal_outer_window_px": (
                    self.sat_defaults.vessel_cfar_outer_window_px
                ),
                "inner_window_score_scale_px": (
                    self.sat_defaults.vessel_cfar_inner_window_score_scale_px
                ),
                "outer_window_score_scale_px": (
                    self.sat_defaults.vessel_cfar_outer_window_score_scale_px
                ),
            }

        if target_type == "infrastructure":
            return {
                "optimal_inner_window_px": (
                    self.sat_defaults.infrastructure_cfar_inner_window_px
                ),
                "optimal_outer_window_px": (
                    self.sat_defaults.infrastructure_cfar_outer_window_px
                ),
                "inner_window_score_scale_px": (
                    self.sat_defaults
                    .infrastructure_cfar_inner_window_score_scale_px
                ),
                "outer_window_score_scale_px": (
                    self.sat_defaults
                    .infrastructure_cfar_outer_window_score_scale_px
                ),
            }

        raise ValueError(f"Unsupported target_type for CFAR scoring: {target_type}")

    def _calculate_cfar_window_quality_score(
        self,
        target_type: str,
        inner_window_px: int,
        outer_window_px: int,
    ) -> float:
        """
        Calculate a mock CFAR window quality score.

        The score is target-type specific and is maximized when the requested
        inner and outer CFAR windows match the reference optimal configuration
        for the requested target type.

        The score is in [0, 1]. Invalid window geometry, where the outer window
        is not larger than the inner window, returns 0.
        """

        if inner_window_px <= 0 or outer_window_px <= 0:
            return 0.0

        if outer_window_px <= inner_window_px:
            return 0.0

        config = self._get_cfar_window_scoring_config(target_type)

        optimal_inner = float(config["optimal_inner_window_px"])
        optimal_outer = float(config["optimal_outer_window_px"])
        inner_scale = float(config["inner_window_score_scale_px"])
        outer_scale = float(config["outer_window_score_scale_px"])

        score = np.exp(
            -((inner_window_px - optimal_inner) / inner_scale) ** 2
            -((outer_window_px - optimal_outer) / outer_scale) ** 2
        )

        return round(float(score), 6)

    # -------------------------------------------------------------------------
    # Model tools
    # -------------------------------------------------------------------------

    @agent_tool
    def run_two_parameter_cfar_detection(
            self,
            sar_image_or_composite: object,
            target_type: str,
            detection_band: str,
            inner_window_px: int,
            outer_window_px: int,
            threshold_multiplier_nt_s1a: int,
            threshold_multiplier_nt_s1b: int,
            dilation_radius: float,
    ) -> dict[str, Any]:
        """
        Detect candidate targets in Sentinel-1 SAR imagery using a
        two-parameter CFAR detector.

        This tool applies a two-parameter constant false alarm rate detector to
        Sentinel-1 SAR imagery or SAR median composites. It estimates the local
        background from a square annular window around each pixel and marks
        pixels as candidate targets when their backscatter exceeds the local
        background according to the requested threshold configuration.

        Parameters
        ----------
        sar_image_or_composite : object
            Input Sentinel-1 SAR image or composite. For vessel detection this
            should be clipped single-scene SAR imagery. For infrastructure
            detection this should be SAR median composite imagery.
        target_type : str
            Target profile that determines the intended detection task.
            Supported values are ``"vessel"`` and ``"infrastructure"``.
        detection_band : str
            SAR polarization band used for CFAR detection.
        inner_window_px : int
            Size of the inner square background window in pixels.
        outer_window_px : int
            Size of the outer square background window in pixels.
        threshold_multiplier_nt_s1a : int
            CFAR threshold multiplier for Sentinel-1A acquisitions in the
            selected time period.
        threshold_multiplier_nt_s1b : int
            CFAR threshold multiplier for Sentinel-1B acquisitions in the
            selected time period.
        dilation_radius : float
            Post-processing dilation radius used to merge or clean candidate
            detections.

        Returns
        -------
        candidate_detections : object
            Candidate SAR detections identified by the two-parameter CFAR
            detector. The semantic meaning of the detections depends on
            ``target_type``: candidate vessels or candidate fixed
            infrastructure.

        Notes
        -----
        This tool performs CFAR-based candidate target detection only. It does
        not construct SAR median composites, classify vessel/noise detections,
        estimate vessel length, classify infrastructure type, match detections
        to AIS, or perform temporal aggregation.

        The returned detection payload includes ``cfar_window_quality_score``,
        a score in [0, 1] used for testing Agent parameter selection.
        Higher values indicate better inner/outer CFAR window choices.
        """
        tool_name = "run_two_parameter_cfar_detection"

        supported_target_types = {
            "vessel",
            "infrastructure",
        }

        if target_type not in supported_target_types:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Unsupported target type was provided. Only vessel and "
                    "infrastructure are supported."
                ),
                "unsupported_target_type": target_type,
                "supported_target_types": sorted(supported_target_types),
                "generated": {},
                "state": {
                    "completed": None,
                    "required": None,
                },
            }

        if target_type == "vessel":
            required_states = [
                SeaActivityStates.SAR_SCENE_BORDERS_CLIPPED,
            ]
            expected_generated_content = "clipped_sar_scenes"
            generated_key = "candidate_vessel_detections"
            completed_state = SeaActivityStates.VESSEL_CFAR_DETECTION_COMPLETED
            base_success_message = (
                "Vessel candidate detections have been produced using "
                "two-parameter CFAR detection."
            )
        else:
            required_states = [
                SeaActivityStates.SAR_MEDIAN_COMPOSITES_CONSTRUCTED,
            ]
            expected_generated_content = "sar_median_composites"
            generated_key = "candidate_infrastructure_detections"
            completed_state = (
                SeaActivityStates.INFRASTRUCTURE_CFAR_DETECTION_COMPLETED
            )
            base_success_message = (
                "Infrastructure candidate detections have been produced using "
                "two-parameter CFAR detection."
            )

        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Required SAR imagery or composite preparation state is "
                    "missing before running two-parameter CFAR detection."
                ),
                "required_states": required_states,
                "missing_states": missing_states,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        if expected_generated_content not in self.state.generated_contents:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Required SAR imagery or composite content is missing before "
                    "running two-parameter CFAR detection."
                ),
                "missing_generated_content": [expected_generated_content],
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        cfar_window_quality_score = self._calculate_cfar_window_quality_score(
            target_type=target_type,
            inner_window_px=inner_window_px,
            outer_window_px=outer_window_px,
        )

        detection_payload = {
            f"{generated_key}_id": generated_key,
            "source_sar_image_or_composite": sar_image_or_composite,
            "target_type": target_type,
            "detection_band": detection_band,
            "inner_window_px": inner_window_px,
            "outer_window_px": outer_window_px,
            "threshold_multiplier_nt_s1a": threshold_multiplier_nt_s1a,
            "threshold_multiplier_nt_s1b": threshold_multiplier_nt_s1b,
            "dilation_radius": dilation_radius,
            "cfar_window_quality_score": cfar_window_quality_score,
            "cfar_window_quality_score_description": (
                "CFAR window quality score in [0, 1]. Higher is better."
            ),
        }

        generated = {
            generated_key: detection_payload
        }

        success_message = (
            f"{base_success_message} "
            f"CFAR window quality score: {cfar_window_quality_score}."
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": success_message,
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def estimate_vessel_presence_and_length(
        self,
        sar_tiles: object,
        model: object,
    ) -> dict[str, Any]:
        """
        Estimate vessel presence probability and vessel length from SAR image tiles.

        This tool applies a trained multi-task convolutional neural network to
        dual-band Sentinel-1 SAR image tiles centered on candidate detections.
        The model predicts the probability that each candidate object is a
        vessel and estimates the object's length in meters.

        Parameters
        ----------
        sar_tiles : object
            Dual-band SAR image tiles centered on candidate detections.
        model : object
            Trained vessel presence-and-length model or model weights.

        Returns
        -------
        vessel_presence_probability : object
            Predicted probability that each candidate object is a vessel.
        estimated_length_m : object
            Estimated vessel length in meters for each candidate object.

        Notes
        -----
        This tool performs neural-network inference for vessel presence and
        length estimation only. It does not run SAR CFAR detection, extract SAR
        tiles, train the model, match detections to AIS, or classify vessels as
        fishing or non-fishing.
        """
        tool_name = "estimate_vessel_presence_and_length"

        required_states = [
            SeaActivityStates.VESSEL_DETECTION_TILES_EXTRACTED,
            SeaActivityStates.VESSEL_MODEL_TRAINED_AND_VALIDATED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel inference tiles and trained vessel model must be "
                    "prepared before vessel presence and length estimation."
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
            "vessel_inference_tiles",
            "trained_vessel_model",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel inference tile content or trained vessel model "
                    "content is missing before vessel presence and length "
                    "estimation."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "vessel_presence_probability": {
                "vessel_presence_probability_id": "vessel_presence_probability",
                "source_sar_tiles": sar_tiles,
                "source_model": model,
                "prediction_description": (
                    "Predicted probability that each candidate object is a vessel."
                ),
            },
            "estimated_length_m": {
                "estimated_length_m_id": "estimated_length_m",
                "source_sar_tiles": sar_tiles,
                "source_model": model,
                "prediction_description": (
                    "Estimated vessel length in meters for each candidate object."
                ),
            },
        }

        completed_state = SeaActivityStates.VESSEL_PRESENCE_AND_LENGTH_ESTIMATED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Vessel presence probability and vessel length have been "
                "estimated from SAR tiles."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def classify_infrastructure(
        self,
        sar_tiles: object,
        optical_tiles: object,
        model: object,
    ) -> dict[str, Any]:
        """
        Classify candidate offshore infrastructure detections using SAR and
        optical image tiles.

        This tool applies a trained multi-input ConvNeXt-based convolutional
        neural network to candidate infrastructure detections. The model takes
        Sentinel-1 SAR tiles and Sentinel-2 optical tiles for each candidate
        object, processes them through separate image branches, and outputs
        class probabilities for offshore infrastructure categories.

        Parameters
        ----------
        sar_tiles : object
            Sentinel-1 SAR image tiles centered on candidate infrastructure
            detections.
        optical_tiles : object
            Sentinel-2 optical image tiles centered on candidate infrastructure
            detections.
        model : object
            Trained infrastructure classification model or model weights.

        Returns
        -------
        infrastructure_class_probabilities : object
            Predicted probabilities for the infrastructure classes: wind, oil,
            other, and noise.
        predicted_infrastructure_class : object
            Most likely infrastructure class for each candidate object.

        Notes
        -----
        This tool performs neural-network inference for infrastructure
        classification only. It does not run SAR CFAR detection, construct SAR
        or optical tiles, train the infrastructure classifier, cluster repeated
        objects, or perform temporal aggregation.
        """
        tool_name = "classify_infrastructure"

        required_states = [
            SeaActivityStates.INFRASTRUCTURE_SAR_TILES_EXTRACTED,
            SeaActivityStates.INFRASTRUCTURE_OPTICAL_TILES_EXTRACTED,
            SeaActivityStates.INFRASTRUCTURE_MODEL_TRAINED_AND_VALIDATED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Infrastructure SAR tiles, optical tiles, and trained "
                    "infrastructure model must be prepared before "
                    "infrastructure classification."
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
            "infrastructure_sar_tiles",
            "infrastructure_optical_tiles",
            "trained_infrastructure_model",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Infrastructure SAR tile content, optical tile content, or "
                    "trained infrastructure model content is missing before "
                    "infrastructure classification."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "infrastructure_class_probabilities": {
                "infrastructure_class_probabilities_id": (
                    "infrastructure_class_probabilities"
                ),
                "source_sar_tiles": sar_tiles,
                "source_optical_tiles": optical_tiles,
                "source_model": model,
                "classes": ["wind", "oil", "other", "noise"],
            },
            "predicted_infrastructure_class": {
                "predicted_infrastructure_class_id": (
                    "predicted_infrastructure_class"
                ),
                "source_sar_tiles": sar_tiles,
                "source_optical_tiles": optical_tiles,
                "source_model": model,
                "classes": ["wind", "oil", "other", "noise"],
            },
        }

        completed_state = SeaActivityStates.INFRASTRUCTURE_CLASSIFICATION_COMPLETED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Infrastructure class probabilities and predicted classes have "
                "been produced from SAR and optical tiles."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def classify_fishing_nonfishing(
        self,
        feature_tiles: object,
        model: object,
    ) -> dict[str, Any]:
        """
        Classify vessel samples as fishing or non-fishing.

        This tool applies a trained fishing / non-fishing classification model
        to raster feature tiles generated from SAR vessel rasters, AIS vessel
        rasters, environmental and physical rasters, and vessel presence
        probabilities. It outputs class probabilities and predicted labels for
        each vessel sample.

        Parameters
        ----------
        feature_tiles : object
            Model-ready raster feature tiles generated from SAR vessel rasters,
            AIS vessel rasters, environmental rasters, and vessel presence
            probabilities.
        model : object
            Trained fishing / non-fishing classification model or model weights.

        Returns
        -------
        fishing_nonfishing_class_probabilities : object
            Predicted probabilities for fishing and non-fishing classes.
        predicted_fishing_nonfishing_class : object
            Most likely fishing / non-fishing class for each vessel sample.

        Notes
        -----
        This tool performs fishing / non-fishing model inference only. It does
        not construct raster feature tiles, build SAR or AIS rasters, train the
        classifier, estimate vessel presence, or aggregate vessel activity over
        space or time.
        """
        tool_name = "classify_fishing_nonfishing"

        required_states = [
            SeaActivityStates.RASTER_FEATURE_TILE_STACK_GENERATED,
            SeaActivityStates.FISHING_NONFISHING_MODEL_TRAINED_AND_VALIDATED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Fishing model feature tiles and trained fishing / "
                    "non-fishing model must be prepared before fishing and "
                    "non-fishing classification."
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
            "fishing_model_feature_tiles",
            "trained_fishing_nonfishing_model",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Fishing model feature tile content or trained fishing / "
                    "non-fishing model content is missing before fishing and "
                    "non-fishing classification."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "fishing_nonfishing_class_probabilities": {
                "fishing_nonfishing_class_probabilities_id": (
                    "fishing_nonfishing_class_probabilities"
                ),
                "source_feature_tiles": feature_tiles,
                "source_model": model,
                "classes": ["fishing", "non_fishing"],
            },
            "predicted_fishing_nonfishing_class": {
                "predicted_fishing_nonfishing_class_id": (
                    "predicted_fishing_nonfishing_class"
                ),
                "source_feature_tiles": feature_tiles,
                "source_model": model,
                "classes": ["fishing", "non_fishing"],
            },
        }

        completed_state = (
            SeaActivityStates.FISHING_NONFISHING_CLASSIFICATION_COMPLETED
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Fishing and non-fishing class probabilities and predicted "
                "classes have been produced from raster feature tiles."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

