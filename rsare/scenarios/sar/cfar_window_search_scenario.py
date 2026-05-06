from __future__ import annotations

from typing import Any, Literal

from rsare.scenarios.scenario.scenario import Scenario

from rsare.apps.sar import (
    SeaActivityDefaults,
    SeaActivityToolState,
    SAT_Data,
    SAT_Model,
    SAT_Training,
    SAT_Operation,
    SAT_Preparation,
)


CFARPromptMode = Literal[
    "direct_optimum",
    "choose_from_two",
    "self_propose",
]


class CFARWindowSearchScenario(Scenario):
    """
    Scenario for testing whether an Agent can use CFAR feedback to select
    inner/outer CFAR window parameters.

    This scenario preloads all CFAR prerequisites up to clipped_sar_scenes.
    The Agent receives the full SAR tool list and is asked to call
    SAT_Model__run_two_parameter_cfar_detection under one of three prompt modes.
    """

    scenario_class = "cfar_window_search"
    scenario_id = "cfar_window_search_2020_01_gulf_of_mexico"

    date_begin = "2020-01-01"
    date_end = "2020-01-31"
    region = [-95.0, 27.0, -90.0, 30.0]

    expected_tool_name = "SAT_Model__run_two_parameter_cfar_detection"

    # Other optimal vessel CFAR parameters are provided to the Agent.
    fixed_cfar_args = {
        "sar_image_or_composite": "clipped_sar_scenes",
        "target_type": "vessel",
        "detection_band": "VH",
        "threshold_multiplier_nt_s1a": 22,
        "threshold_multiplier_nt_s1b": 24,
        "dilation_radius": 60.0,
    }

    # Internal oracle optimum. Do not reveal in prompt mode 3.
    optimal_inner_window_px = 200
    optimal_outer_window_px = 600

    def __init__(
        self,
        prompt_mode: CFARPromptMode = "self_propose",
    ) -> None:
        self.prompt_mode = prompt_mode

        self.shared_state = SeaActivityToolState()
        self.sat_defaults = SeaActivityDefaults()

        sar_apps = [
            SAT_Data(state=self.shared_state, sat_defaults=self.sat_defaults),
            SAT_Model(state=self.shared_state, sat_defaults=self.sat_defaults),
            SAT_Training(state=self.shared_state, sat_defaults=self.sat_defaults),
            SAT_Operation(state=self.shared_state, sat_defaults=self.sat_defaults),
            SAT_Preparation(state=self.shared_state, sat_defaults=self.sat_defaults),
        ]

        super().__init__(
            scenario_id=f"{self.scenario_id}_{prompt_mode}",
            scenario_input="",
            apps=sar_apps,
            start_time=0.0,
            time_increment_in_seconds=1,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_succeed(
        self,
        result: dict[str, Any],
        tool_name: str,
    ) -> dict[str, Any]:
        if result.get("status") != "succeed":
            raise RuntimeError(
                f"{tool_name} failed.\n"
                f"message={result.get('message')}\n"
                f"missing_states={result.get('missing_states')}\n"
                f"missing_generated_content={result.get('missing_generated_content')}\n"
                f"full_result={result}"
            )
        return result

    def _get_generated(self, key: str) -> Any:
        if key not in self.shared_state.generated_contents:
            raise KeyError(
                f"Missing generated content: {key}. "
                f"Available keys: {list(self.shared_state.generated_contents.keys())}"
            )
        return self.shared_state.generated_contents[key]

    def _get_app(self, app_type):
        for app in self.apps or []:
            if isinstance(app, app_type):
                return app
        raise ValueError(f"App of type {app_type.__name__} not found.")

    def _state_summary_text(self) -> str:
        completed_states = sorted(self.shared_state.completed_states)
        generated_keys = list(self.shared_state.generated_contents.keys())

        return f"""
Current completed states:
{completed_states}

Current generated content keys:
{generated_keys}

Important generated input object:
- clipped_sar_scenes

When a tool argument requires the SAR input object, use the generated content key string exactly:
clipped_sar_scenes
""".strip()

    def _fixed_cfar_args_text(self) -> str:
        return """
For every vessel CFAR call, use these fixed parameters:
- sar_image_or_composite: clipped_sar_scenes
- target_type: vessel
- detection_band: VH
- threshold_multiplier_nt_s1a: 22
- threshold_multiplier_nt_s1b: 24
- dilation_radius: 60.0
""".strip()

    def _base_instructions_text(self) -> str:
        return f"""
You are testing a SAR-based sea activity workflow.

All prerequisite steps needed before vessel CFAR detection have already been completed.
You have access to the full SAR tool list, but this task is only about selecting
inner_window_px and outer_window_px for vessel CFAR.

The CFAR tool returns cfar_window_quality_score in the generated candidate
detections payload. The score is in [0, 1], and higher is better.

Rules:
1. Only call SAT_Model__run_two_parameter_cfar_detection for CFAR evaluation.
2. Do not repeat upstream loading, mask construction, SAR filtering, or border clipping.
3. Do not call infrastructure CFAR.
4. Do not continue to downstream AIS matching, training, preparation, or classification.
5. You may call vessel CFAR multiple times.
6. Stop once you have enough evidence to identify the best inner/outer window pair.
7. In your final answer, report every tested pair and its cfar_window_quality_score, then name the best pair.
""".strip()

    def _build_prompt_direct_optimum(self) -> str:
        return f"""
{self._base_instructions_text()}

{self._state_summary_text()}

{self._fixed_cfar_args_text()}

Use this known optimal vessel CFAR window pair:
- inner_window_px: 200
- outer_window_px: 600

Task:
Call the vessel CFAR tool once using the known optimal pair.
""".strip()

    def _build_prompt_choose_from_two(self) -> str:
        return f"""
{self._base_instructions_text()}

{self._state_summary_text()}

{self._fixed_cfar_args_text()}

Candidate vessel CFAR window pairs:
A. inner_window_px: 100, outer_window_px: 300
B. inner_window_px: 200, outer_window_px: 600

Task:
Evaluate both candidate pairs with the vessel CFAR tool, compare their
cfar_window_quality_score values, and select the better pair.
""".strip()

    def _build_prompt_self_propose(self) -> str:
        return f"""
{self._base_instructions_text()}

{self._state_summary_text()}

{self._fixed_cfar_args_text()}


Propose valid vessel CFAR window pairs yourself.
Each pair must satisfy:
- inner_window_px > 0
- outer_window_px > inner_window_px

Task:
Evaluate your proposed pairs with the vessel CFAR tool, compare their
cfar_window_quality_score values, and select the one best pair.

""".strip()

    def _build_prompt(self) -> str:
        if self.prompt_mode == "direct_optimum":
            return self._build_prompt_direct_optimum()

        if self.prompt_mode == "choose_from_two":
            return self._build_prompt_choose_from_two()

        if self.prompt_mode == "self_propose":
            return self._build_prompt_self_propose()

        raise ValueError(f"Unsupported prompt_mode: {self.prompt_mode}")

    # ------------------------------------------------------------------
    # Scenario lifecycle
    # ------------------------------------------------------------------

    def initiate_scenario(self):
        """
        Preload all vessel CFAR prerequisites into the shared tool state.
        """
        data = self._get_app(SAT_Data)
        operation = self._get_app(SAT_Operation)

        self._require_succeed(
            data.load_sar_scenes(
                date_begin=self.date_begin,
                date_end=self.date_end,
                region=self.region,
            ),
            "SAT_Data__load_sar_scenes",
        )

        self._require_succeed(
            data.load_synthetic_shoreline_data(
                date_begin=self.date_begin,
                date_end=self.date_end,
                region=self.region,
            ),
            "SAT_Data__load_synthetic_shoreline_data",
        )

        scene_collection = self._get_generated("scene_collection")
        synthetic_shoreline_data = self._get_generated("synthetic_shoreline_data")

        self._require_succeed(
            operation.construct_shoreline_buffer_mask(
                synthetic_shoreline_data=synthetic_shoreline_data,
                shoreline_buffer_km=1.0,
            ),
            "SAT_Operation__construct_shoreline_buffer_mask",
        )

        self._require_succeed(
            operation.construct_ocean_mask(
                synthetic_shoreline_data=synthetic_shoreline_data,
                shoreline_buffer_km=1.0,
            ),
            "SAT_Operation__construct_ocean_mask",
        )

        self._require_succeed(
            operation.filter_sar_scenes_with_mask(
                sar_scenes=scene_collection,
                mask_list=[
                    "valid_ocean_mask",
                    "shoreline_buffer_mask",
                ],
            ),
            "SAT_Operation__filter_sar_scenes_with_mask",
        )

        filtered_sar_scenes = self._get_generated("filtered_sar_scenes")

        self._require_succeed(
            operation.clip_sar_scene_borders(
                filtered_sar_scenes=filtered_sar_scenes,
                border_clipping_buffer_m=500.0,
            ),
            "SAT_Operation__clip_sar_scene_borders",
        )

        self._get_generated("clipped_sar_scenes")
        self.scenario_input = self._build_prompt()

    def oracle_solution(self, run_oracle=False):
        """
        Required by Scenario base class. Not used by this Agent test.
        """
        return None

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def _extract_cfar_score_from_step(self, step) -> float | None:
        content = getattr(step, "content", None)
        if not isinstance(content, dict):
            return None

        generated = content.get("generated", {})
        if not isinstance(generated, dict):
            return None

        detections = generated.get("candidate_vessel_detections")
        if not isinstance(detections, dict):
            return None

        score = detections.get("cfar_window_quality_score")
        if isinstance(score, (int, float)):
            return float(score)

        return None

    def evaluate_agent_workflow(self, agent_workflow) -> dict[str, Any]:
        """
        Evaluate whether the Agent used vessel CFAR appropriately.
        """
        tool_steps = [
            step
            for step in agent_workflow.dag.values()
            if getattr(step, "op_type", None) == "TOOL"
        ]

        cfar_steps = [
            step
            for step in tool_steps
            if step.tool_name == self.expected_tool_name
        ]

        failures: list[str] = []

        if not cfar_steps:
            return {
                "passed": False,
                "reason": "Agent did not call vessel CFAR.",
                "failures": [
                    f"Expected at least one call to {self.expected_tool_name}."
                ],
                "cfar_trials": [],
            }


        cfar_trials: list[dict[str, Any]] = []

        for step in cfar_steps:
            args = step.tool_args or {}
            score = self._extract_cfar_score_from_step(step)

            trial = {
                "inner_window_px": args.get("inner_window_px"),
                "outer_window_px": args.get("outer_window_px"),
                "target_type": args.get("target_type"),
                "detection_band": args.get("detection_band"),
                "threshold_multiplier_nt_s1a": args.get(
                    "threshold_multiplier_nt_s1a"
                ),
                "threshold_multiplier_nt_s1b": args.get(
                    "threshold_multiplier_nt_s1b"
                ),
                "dilation_radius": args.get("dilation_radius"),
                "cfar_window_quality_score": score,
            }
            cfar_trials.append(trial)

            if args.get("target_type") != "vessel":
                failures.append(
                    f"Non-vessel CFAR call found: target_type={args.get('target_type')!r}."
                )

            for key, expected_value in self.fixed_cfar_args.items():
                if key == "sar_image_or_composite":
                    if args.get(key) in (None, ""):
                        failures.append("sar_image_or_composite is missing.")
                    continue

                actual_value = args.get(key)
                if actual_value != expected_value:
                    failures.append(
                        f"{key}: expected {expected_value!r}, got {actual_value!r}."
                    )

            inner = args.get("inner_window_px")
            outer = args.get("outer_window_px")

            if not isinstance(inner, int):
                failures.append(f"inner_window_px must be int, got {inner!r}.")
            if not isinstance(outer, int):
                failures.append(f"outer_window_px must be int, got {outer!r}.")
            if isinstance(inner, int) and isinstance(outer, int):
                if inner <= 0:
                    failures.append(f"inner_window_px must be positive, got {inner}.")
                if outer <= inner:
                    failures.append(
                        f"outer_window_px must be greater than inner_window_px, "
                        f"got inner={inner}, outer={outer}."
                    )

        forbidden_tools = {
            "SAT_Data__load_sar_scenes",
            "SAT_Data__load_synthetic_shoreline_data",
            "SAT_Operation__construct_shoreline_buffer_mask",
            "SAT_Operation__construct_ocean_mask",
            "SAT_Operation__filter_sar_scenes_with_mask",
            "SAT_Operation__clip_sar_scene_borders",
            "SAT_Operation__exclude_radar_ambiguities",
            "SAT_Operation__extract_and_interpolate_ais_data",
            "SAT_Operation__match_ais_with_cfar_results",
            "SAT_Training__construct_vessel_training_dataset",
            "SAT_Model__estimate_vessel_presence_and_length",
        }

        forbidden_called = [
            step.tool_name
            for step in tool_steps
            if step.tool_name in forbidden_tools
        ]

        if forbidden_called:
            failures.append(
                "Agent called forbidden non-CFAR workflow tools: "
                f"{forbidden_called}."
            )

        best_trial = None
        scored_trials = [
            trial
            for trial in cfar_trials
            if isinstance(trial.get("cfar_window_quality_score"), float)
        ]

        if scored_trials:
            best_trial = max(
                scored_trials,
                key=lambda trial: trial["cfar_window_quality_score"],
            )
        else:
            failures.append("No CFAR trial returned a numeric quality score.")

        optimum_was_tested = any(
            trial.get("inner_window_px") == self.optimal_inner_window_px
            and trial.get("outer_window_px") == self.optimal_outer_window_px
            for trial in cfar_trials
        )

        if self.prompt_mode in {"direct_optimum", "choose_from_two"}:
            if not optimum_was_tested:
                failures.append(
                    "The known optimal pair inner=200, outer=600 was not tested."
                )

        if best_trial is not None:
            if self.prompt_mode in {"direct_optimum", "choose_from_two"}:
                if (
                    best_trial.get("inner_window_px") != self.optimal_inner_window_px
                    or best_trial.get("outer_window_px") != self.optimal_outer_window_px
                ):
                    failures.append(
                        "The best observed trial was not the known optimum "
                        "inner=200, outer=600."
                    )

        return {
            "passed": len(failures) == 0,
            "reason": (
                "Agent used vessel CFAR appropriately for this prompt mode."
                if not failures
                else "Agent did not satisfy the CFAR window search oracle."
            ),
            "prompt_mode": self.prompt_mode,
            "failures": failures,
            "cfar_call_count": len(cfar_steps),
            "cfar_trials": cfar_trials,
            "best_trial": best_trial,
        }