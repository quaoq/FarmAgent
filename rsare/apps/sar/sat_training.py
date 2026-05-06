from __future__ import annotations
from typing import Any

from rsare.agents.agent.toolset_builder import agent_tool
from rsare.apps.sar.sea_activity_tools import (
    SeaActivityDefaults,
    SeaActivityStates,
    SeaActivityToolState,
    SeaActivityTools,
)


class SAT_Training(SeaActivityTools):
    """
    Training tools for SAR-based sea activity workflow testing.
    """

    def __init__(
        self,
        state: SeaActivityToolState | None = None,
        sat_defaults: SeaActivityDefaults | None = None,
    ):
        super().__init__(
            name="SAT_Training",
            state=state,
            sat_defaults=sat_defaults,
        )

    # -------------------------------------------------------------------------
    # Training tools
    # -------------------------------------------------------------------------

    @agent_tool
    def construct_vessel_training_dataset(
        self,
        valid_candidate_vessel_detections: object,
        clipped_sar_scenes: object,
        sar_ais_matches: object,
        tile_size_px: int,
        train_test_split: float,
        cross_validation_folds: int,
    ) -> dict[str, Any]:
        """
        Construct a labeled training dataset for vessel presence and length
        estimation.

        This tool builds training samples for the vessel presence and length
        estimation model. It uses valid candidate vessel detections, clipped
        Sentinel-1 SAR scenes, and SAR-AIS match records to construct labeled
        SAR tile samples for vessel/noise presence prediction and vessel length
        estimation.

        Parameters
        ----------
        valid_candidate_vessel_detections : object
            Candidate vessel detections after radar ambiguity filtering.
        clipped_sar_scenes : object
            Border-clipped Sentinel-1 SAR scenes used to extract
            detection-centered training tiles.
        sar_ais_matches : object
            SAR-AIS match records used to assign vessel presence and vessel
            length labels.
        tile_size_px : int
            Width and height of the square SAR training tile in pixels.
        train_test_split : float
            Fraction of labeled samples reserved for testing.
        cross_validation_folds : int
            Number of folds used for model selection within the training data.

        Returns
        -------
        vessel_training_dataset : object
            Labeled dataset containing SAR tiles, detection identifiers,
            presence labels, vessel length labels, and split assignment.
        vessel_dataset_indices : object
            Train, test, and cross-validation indices for model training and
            evaluation.

        Notes
        -----
        This tool constructs the vessel training dataset only. It does not train
        the vessel model, run model inference, perform CFAR detection, create
        SAR-AIS matches, or classify vessels as fishing or non-fishing.
        """
        tool_name = "construct_vessel_training_dataset"

        required_states = [
            SeaActivityStates.VESSEL_RADAR_AMBIGUITIES_EXCLUDED,
            SeaActivityStates.SAR_SCENE_BORDERS_CLIPPED,
            SeaActivityStates.SAR_AIS_MATCHES_CONSTRUCTED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Valid candidate vessel detections, clipped SAR scenes, and "
                    "SAR-AIS matches must be prepared before constructing the "
                    "vessel training dataset."
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
            "valid_candidate_vessel_detections",
            "clipped_sar_scenes",
            "sar_ais_matches",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Required vessel training dataset source content is missing "
                    "before constructing the vessel training dataset."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "vessel_training_dataset": {
                "vessel_training_dataset_id": "vessel_training_dataset",
                "source_valid_candidate_vessel_detections": (
                    valid_candidate_vessel_detections
                ),
                "source_clipped_sar_scenes": clipped_sar_scenes,
                "source_sar_ais_matches": sar_ais_matches,
                "tile_size_px": tile_size_px,
            },
            "vessel_dataset_indices": {
                "vessel_dataset_indices_id": "vessel_dataset_indices",
                "source_vessel_training_dataset": "vessel_training_dataset",
                "train_test_split": train_test_split,
                "cross_validation_folds": cross_validation_folds,
            },
        }

        completed_state = SeaActivityStates.VESSEL_TRAINING_DATASET_CONSTRUCTED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Vessel training dataset has been constructed from valid "
                "candidate vessel detections, clipped SAR scenes, and SAR-AIS "
                "matches."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def train_validate_vessel_model(
        self,
        vessel_training_dataset: object,
        vessel_dataset_indices: object,
    ) -> dict[str, Any]:
        """
        Train and validate the vessel presence and length estimation model.

        This tool trains a vessel model using a labeled SAR tile dataset and
        dataset split indices. The trained model predicts both vessel presence
        probability and vessel length from detection-centered Sentinel-1 SAR
        image tiles.

        Parameters
        ----------
        vessel_training_dataset : object
            Labeled SAR tile dataset for vessel presence and length estimation.
        vessel_dataset_indices : object
            Train, test, and cross-validation indices for model training and
            evaluation.

        Returns
        -------
        trained_vessel_model : object
            Trained vessel presence and length estimation model.
        vessel_model_weights : object
            Trained model weights.
        vessel_validation_metrics : object
            Validation and test metrics for vessel presence and length
            estimation.

        Notes
        -----
        This tool only trains and validates the vessel presence and length
        estimation model. It does not construct the training dataset, run CFAR
        detection, extract inference tiles, estimate vessel presence or length
        for new detections, or classify fishing and non-fishing activity.
        """
        tool_name = "train_validate_vessel_model"

        required_states = [
            SeaActivityStates.VESSEL_TRAINING_DATASET_CONSTRUCTED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel training dataset must be constructed before "
                    "training and validating the vessel model."
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
            "vessel_training_dataset",
            "vessel_dataset_indices",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Vessel training dataset content or vessel dataset indices "
                    "are missing before training and validating the vessel model."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "trained_vessel_model": {
                "trained_vessel_model_id": "trained_vessel_model",
                "source_vessel_training_dataset": vessel_training_dataset,
                "source_vessel_dataset_indices": vessel_dataset_indices,
            },
            "vessel_model_weights": {
                "vessel_model_weights_id": "vessel_model_weights",
                "source_trained_vessel_model": "trained_vessel_model",
            },
            "vessel_validation_metrics": {
                "vessel_validation_metrics_id": "vessel_validation_metrics",
                "source_trained_vessel_model": "trained_vessel_model",
                "metric_names": [
                    "presence_auc",
                    "presence_accuracy",
                    "length_mae",
                    "length_rmse",
                ],
            },
        }

        completed_state = SeaActivityStates.VESSEL_MODEL_TRAINED_AND_VALIDATED

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Vessel presence and length model has been trained and validated."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def construct_infrastructure_training_dataset(
        self,
        infrastructure_sar_tiles: object,
        infrastructure_optical_tiles: object,
        infrastructure_reference_data: object,
        train_test_split: float,
        cross_validation_folds: int,
    ) -> dict[str, Any]:
        """
        Construct a labeled training dataset for infrastructure classification.

        This tool builds labeled training samples for the offshore infrastructure
        classification model. It combines Sentinel-1 SAR tiles, Sentinel-2
        optical tiles, and offshore infrastructure reference data to assign
        class labels for infrastructure categories.

        Parameters
        ----------
        infrastructure_sar_tiles : object
            Candidate infrastructure detection centered Sentinel-1 SAR tiles.
        infrastructure_optical_tiles : object
            Candidate infrastructure detection centered Sentinel-2 optical tiles.
        infrastructure_reference_data : object
            Offshore infrastructure reference data used to assign class labels.
        train_test_split : float
            Fraction of labeled samples reserved for testing.
        cross_validation_folds : int
            Number of folds used for model selection within the training data.

        Returns
        -------
        infrastructure_training_dataset : object
            Labeled SAR-optical tile dataset for infrastructure classification.
        infrastructure_dataset_indices : object
            Train, test, and cross-validation indices for infrastructure model
            training and evaluation.

        Notes
        -----
        This tool constructs the infrastructure training dataset only. It does
        not train the infrastructure model, run CFAR detection, extract SAR or
        optical tiles, classify infrastructure, or aggregate infrastructure
        activity over time.
        """
        tool_name = "construct_infrastructure_training_dataset"

        required_states = [
            SeaActivityStates.INFRASTRUCTURE_SAR_TILES_EXTRACTED,
            SeaActivityStates.INFRASTRUCTURE_OPTICAL_TILES_EXTRACTED,
            SeaActivityStates.INFRASTRUCTURE_DATA_LOADED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Infrastructure SAR tiles, optical tiles, and reference data "
                    "must be prepared before constructing the infrastructure "
                    "training dataset."
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
            "infrastructure_reference_data",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Required infrastructure training dataset source content is "
                    "missing before constructing the infrastructure training "
                    "dataset."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "infrastructure_training_dataset": {
                "infrastructure_training_dataset_id": (
                    "infrastructure_training_dataset"
                ),
                "source_infrastructure_sar_tiles": infrastructure_sar_tiles,
                "source_infrastructure_optical_tiles": infrastructure_optical_tiles,
                "source_infrastructure_reference_data": (
                    infrastructure_reference_data
                ),
                "class_labels": [
                    "wind",
                    "oil",
                    "other",
                    "noise",
                ],
            },
            "infrastructure_dataset_indices": {
                "infrastructure_dataset_indices_id": (
                    "infrastructure_dataset_indices"
                ),
                "source_infrastructure_training_dataset": (
                    "infrastructure_training_dataset"
                ),
                "train_test_split": train_test_split,
                "cross_validation_folds": cross_validation_folds,
            },
        }

        completed_state = (
            SeaActivityStates.INFRASTRUCTURE_TRAINING_DATASET_CONSTRUCTED
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Infrastructure training dataset has been constructed from SAR "
                "tiles, optical tiles, and infrastructure reference data."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def train_validate_infrastructure_model(
        self,
        infrastructure_training_dataset: object,
        infrastructure_dataset_indices: object,
    ) -> dict[str, Any]:
        """
        Train and validate the infrastructure classification model.

        This tool trains an infrastructure classification model using a labeled
        SAR-optical tile dataset and dataset split indices. The trained model
        predicts offshore infrastructure classes from paired Sentinel-1 SAR
        tiles and Sentinel-2 optical tiles.

        Parameters
        ----------
        infrastructure_training_dataset : object
            Labeled SAR-optical tile dataset for infrastructure classification.
        infrastructure_dataset_indices : object
            Train, test, and cross-validation indices for infrastructure model
            training and evaluation.

        Returns
        -------
        trained_infrastructure_model : object
            Trained infrastructure classification model.
        infrastructure_model_weights : object
            Trained infrastructure model weights.
        infrastructure_validation_metrics : object
            Validation and test metrics for infrastructure classification.

        Notes
        -----
        This tool only trains and validates the infrastructure classification
        model. It does not construct the training dataset, run CFAR detection,
        extract SAR or optical tiles, classify infrastructure candidates, or
        aggregate infrastructure detections over space or time.
        """
        tool_name = "train_validate_infrastructure_model"

        required_states = [
            SeaActivityStates.INFRASTRUCTURE_TRAINING_DATASET_CONSTRUCTED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Infrastructure training dataset must be constructed before "
                    "training and validating the infrastructure model."
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
            "infrastructure_training_dataset",
            "infrastructure_dataset_indices",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Infrastructure training dataset content or infrastructure "
                    "dataset indices are missing before training and validating "
                    "the infrastructure model."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "trained_infrastructure_model": {
                "trained_infrastructure_model_id": (
                    "trained_infrastructure_model"
                ),
                "source_infrastructure_training_dataset": (
                    infrastructure_training_dataset
                ),
                "source_infrastructure_dataset_indices": (
                    infrastructure_dataset_indices
                ),
            },
            "infrastructure_model_weights": {
                "infrastructure_model_weights_id": (
                    "infrastructure_model_weights"
                ),
                "source_trained_infrastructure_model": (
                    "trained_infrastructure_model"
                ),
            },
            "infrastructure_validation_metrics": {
                "infrastructure_validation_metrics_id": (
                    "infrastructure_validation_metrics"
                ),
                "source_trained_infrastructure_model": (
                    "trained_infrastructure_model"
                ),
                "metric_names": [
                    "classification_accuracy",
                    "macro_f1",
                    "weighted_f1",
                    "class_precision",
                    "class_recall",
                ],
            },
        }

        completed_state = (
            SeaActivityStates.INFRASTRUCTURE_MODEL_TRAINED_AND_VALIDATED
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Infrastructure classification model has been trained and "
                "validated."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def construct_fishing_nonfishing_training_dataset(
        self,
        fishing_model_feature_tiles: object,
        ais_cfar_match_records: object,
        train_test_split: float,
        cross_validation_folds: int,
        class_sampling_ratio: float,
    ) -> dict[str, Any]:
        """
        Construct a labeled training dataset for fishing/non-fishing classification.

        This tool builds labeled training samples for the fishing/non-fishing
        classification model. It combines model-ready raster feature tiles with
        AIS-CFAR match records to assign fishing and non-fishing activity labels
        and applies the requested class sampling ratio.

        Parameters
        ----------
        fishing_model_feature_tiles : object
            Model-ready raster feature tiles generated from SAR vessel rasters,
            AIS vessel rasters, environmental rasters, and vessel presence
            probabilities.
        ais_cfar_match_records : object
            AIS-CFAR match records used as the activity label source for
            fishing/non-fishing training.
        train_test_split : float
            Fraction of labeled samples reserved for testing.
        cross_validation_folds : int
            Number of folds used for model selection within the training data.
        class_sampling_ratio : float
            Sampling ratio used to balance fishing and non-fishing training
            samples.

        Returns
        -------
        fishing_nonfishing_training_dataset : object
            Labeled raster feature tile dataset for fishing/non-fishing
            classification.
        fishing_nonfishing_dataset_indices : object
            Train, test, and cross-validation indices for fishing/non-fishing
            model training and evaluation.

        Notes
        -----
        This tool constructs the fishing/non-fishing training dataset only. It
        does not generate raster feature tiles, construct SAR or AIS vessel
        rasters, match AIS with CFAR results, train the fishing/non-fishing
        classifier, or perform model inference.
        """
        tool_name = "construct_fishing_nonfishing_training_dataset"

        required_states = [
            SeaActivityStates.RASTER_FEATURE_TILE_STACK_GENERATED,
            SeaActivityStates.AIS_CFAR_RESULTS_MATCHED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Fishing model feature tiles and AIS-CFAR match records must "
                    "be prepared before constructing the fishing/non-fishing "
                    "training dataset."
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
            "ais_cfar_match_records",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Fishing model feature tile content or AIS-CFAR match record "
                    "content is missing before constructing the fishing/non-fishing "
                    "training dataset."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "fishing_nonfishing_training_dataset": {
                "fishing_nonfishing_training_dataset_id": (
                    "fishing_nonfishing_training_dataset"
                ),
                "source_fishing_model_feature_tiles": fishing_model_feature_tiles,
                "source_ais_cfar_match_records": ais_cfar_match_records,
                "class_sampling_ratio": class_sampling_ratio,
                "class_labels": [
                    "fishing",
                    "non_fishing",
                ],
            },
            "fishing_nonfishing_dataset_indices": {
                "fishing_nonfishing_dataset_indices_id": (
                    "fishing_nonfishing_dataset_indices"
                ),
                "source_fishing_nonfishing_training_dataset": (
                    "fishing_nonfishing_training_dataset"
                ),
                "train_test_split": train_test_split,
                "cross_validation_folds": cross_validation_folds,
            },
        }

        completed_state = (
            SeaActivityStates
            .FISHING_NONFISHING_TRAINING_DATASET_CONSTRUCTED
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Fishing/non-fishing training dataset has been constructed from "
                "raster feature tiles and AIS-CFAR match records."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }

    @agent_tool
    def train_validate_fishing_nonfishing_model(
        self,
        fishing_nonfishing_training_dataset: object,
        fishing_nonfishing_dataset_indices: object,
    ) -> dict[str, Any]:
        """
        Train and validate the fishing/non-fishing classification model.

        This tool trains a fishing/non-fishing classification model using a
        labeled raster feature tile dataset and dataset split indices. The
        trained model predicts fishing and non-fishing activity classes from
        raster feature tiles.

        Parameters
        ----------
        fishing_nonfishing_training_dataset : object
            Labeled raster feature tile dataset for fishing/non-fishing
            classification.
        fishing_nonfishing_dataset_indices : object
            Train, test, and cross-validation indices for fishing/non-fishing
            model training and evaluation.

        Returns
        -------
        trained_fishing_nonfishing_model : object
            Trained fishing/non-fishing classification model.
        fishing_nonfishing_model_weights : object
            Trained fishing/non-fishing model weights.
        fishing_nonfishing_validation_metrics : object
            Validation and test metrics for fishing/non-fishing classification.

        Notes
        -----
        This tool only trains and validates the fishing/non-fishing
        classification model. It does not construct the training dataset,
        generate raster feature tiles, classify fishing/non-fishing activity,
        or aggregate vessel activity over space or time.
        """
        tool_name = "train_validate_fishing_nonfishing_model"

        required_states = [
            SeaActivityStates.FISHING_NONFISHING_TRAINING_DATASET_CONSTRUCTED,
        ]
        missing_states = self.get_missing_states(required_states)

        if missing_states:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Fishing/non-fishing training dataset must be constructed "
                    "before training and validating the fishing/non-fishing model."
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
            "fishing_nonfishing_training_dataset",
            "fishing_nonfishing_dataset_indices",
        ]:
            if content_key not in self.state.generated_contents:
                missing_generated_content.append(content_key)

        if missing_generated_content:
            return {
                "status": "failed",
                "tool": tool_name,
                "message": (
                    "Fishing/non-fishing training dataset content or dataset "
                    "indices are missing before training and validating the "
                    "fishing/non-fishing model."
                ),
                "missing_generated_content": missing_generated_content,
                "generated": {},
                "state": {
                    "completed": None,
                    "required": required_states,
                },
            }

        generated = {
            "trained_fishing_nonfishing_model": {
                "trained_fishing_nonfishing_model_id": (
                    "trained_fishing_nonfishing_model"
                ),
                "source_fishing_nonfishing_training_dataset": (
                    fishing_nonfishing_training_dataset
                ),
                "source_fishing_nonfishing_dataset_indices": (
                    fishing_nonfishing_dataset_indices
                ),
            },
            "fishing_nonfishing_model_weights": {
                "fishing_nonfishing_model_weights_id": (
                    "fishing_nonfishing_model_weights"
                ),
                "source_trained_fishing_nonfishing_model": (
                    "trained_fishing_nonfishing_model"
                ),
            },
            "fishing_nonfishing_validation_metrics": {
                "fishing_nonfishing_validation_metrics_id": (
                    "fishing_nonfishing_validation_metrics"
                ),
                "source_trained_fishing_nonfishing_model": (
                    "trained_fishing_nonfishing_model"
                ),
                "metric_names": [
                    "classification_accuracy",
                    "macro_f1",
                    "weighted_f1",
                    "fishing_precision",
                    "fishing_recall",
                    "non_fishing_precision",
                    "non_fishing_recall",
                ],
            },
        }

        completed_state = (
            SeaActivityStates.FISHING_NONFISHING_MODEL_TRAINED_AND_VALIDATED
        )

        self.mark_state(completed_state)
        for key, value in generated.items():
            self.store_generated_content(key, value)

        return {
            "status": "succeed",
            "tool": tool_name,
            "message": (
                "Fishing/non-fishing classification model has been trained and "
                "validated."
            ),
            "generated": generated,
            "state": {
                "completed": completed_state,
                "required": required_states,
            },
        }



