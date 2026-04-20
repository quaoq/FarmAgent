"""
FieldOpsApp - ridge-level irrigation and manual spot spray controls.

Manual operations advance the simulation clock immediately. Some follow-up
effects, like bulk irrigation confirmation, are delivered asynchronously via
notification after the physical work is completed.
"""
from __future__ import annotations

import uuid
from typing import Any

from rsare.agents.agent.toolset_builder import agent_tool
from rsare.apps.farm_app import App
from rsare.apps.farm_world.farm_world_app import (
    FIELD_LENGTH_M,
    FarmWorldApp,
)
from rsare.apps.farm_world.weather_app import WeatherApp
from rsare.engine.event import NotificationEvent

# Irrigation setup time per ridge (s) — valve open/close, hose connection
_IRRIGATION_SETUP_S    = 300
_IRRIGATION_S_PER_HOUR = 3600
_IRRIGATION_VWC_PER_HOUR = 0.05
_IRRIGATION_EFFECT_DELAY_S = 2 * 60 * 60

# Manual backpack sprayer speed (m/s) — operator walking pace
_MANUAL_SPRAY_SPEED_MS = 0.8
_MANUAL_SPRAY_SETUP_S  = 15    # fill/prepare sprayer
# Pesticide drawn from warehouse per manual ridge spray (L) — backpack
# is more thorough/targeted than the tractor boom (8 L/ridge).
_MANUAL_PESTICIDE_L_PER_RIDGE = 3.0


def _manual_spray_duration() -> int:
    """Time in seconds to walk one ridge with a backpack sprayer."""
    return int(FIELD_LENGTH_M / _MANUAL_SPRAY_SPEED_MS) + _MANUAL_SPRAY_SETUP_S


class FieldOpsApp(App):
    """Ridge-level irrigation and manual spot spraying."""

    def __init__(self, farm_world_app: FarmWorldApp, weather_app: WeatherApp) -> None:
        super().__init__(name="FieldOpsApp")
        self._farm_world_app = farm_world_app
        self._weather_app = weather_app
        self._irrigation_log: list[dict[str, Any]] = []
        self._manual_spray_log: list[dict[str, Any]] = []
        self._pending_irrigation_sessions: list[dict[str, Any]] = []

    def get_state(self) -> dict[str, Any]:
        return {
            "app_name": self.name,
            "irrigation_log": list(self._irrigation_log),
            "manual_spray_log": list(self._manual_spray_log),
            "pending_irrigation_sessions": list(self._pending_irrigation_sessions),
        }

    def load_state(self, state_dict: dict[str, Any]) -> None:
        self._irrigation_log = [dict(item) for item in state_dict.get("irrigation_log", [])]
        self._manual_spray_log = [dict(item) for item in state_dict.get("manual_spray_log", [])]
        self._pending_irrigation_sessions = [
            dict(item) for item in state_dict.get("pending_irrigation_sessions", [])
        ]

    def reset(self) -> None:
        super().reset()
        self._irrigation_log = []
        self._manual_spray_log = []
        self._pending_irrigation_sessions = []

    # ------------------------------------------------------------------
    # Agent tools
    # ------------------------------------------------------------------

    @agent_tool()
    def irrigate_ridge(self, ridge_id: int, duration_hours: float) -> dict[str, Any]:
        """
        Irrigate a single ridge.

        The physical irrigation work completes immediately, but the moisture
        effect should be confirmed after a 2-hour follow-up notification.

        Args:
            ridge_id:       Ridge to irrigate (0-63).
            duration_hours: Irrigation run time in hours.
        """
        if not 0 <= ridge_id < self._farm_world_app.num_ridges:
            return {"error": f"Invalid ridge_id {ridge_id}"}
        if float(duration_hours) <= 0:
            return {"error": "duration_hours must be positive"}
        ridge = self._farm_world_app.get_ridge(ridge_id)
        if ridge.soil_vwc >= 0.30:
            return {"error": f"Ridge {ridge_id} soil VWC {ridge.soil_vwc:.3f} already >= 0.30"}
        return self._start_irrigation(
            irrigated_ridges=[ridge_id],
            duration_hours=float(duration_hours),
        )

    @agent_tool()
    def irrigate_range(self, start: int, end: int, duration_hours: float) -> dict[str, Any]:
        """
        Irrigate a contiguous range of ridges.

        Args:
            start:          First ridge to irrigate (0-63).
            end:            Last ridge to irrigate (0-63, >= start).
            duration_hours: Irrigation run time per ridge in hours.
        """
        if not 0 <= start <= end < self._farm_world_app.num_ridges:
            return {"error": f"Invalid ridge range [{start}, {end}]"}
        if float(duration_hours) <= 0:
            return {"error": "duration_hours must be positive"}
        for ridge_id in range(start, end + 1):
            ridge = self._farm_world_app.get_ridge(ridge_id)
            if ridge.soil_vwc >= 0.30:
                return {"error": f"Ridge {ridge_id} soil VWC {ridge.soil_vwc:.3f} already >= 0.30"}
        return self._start_irrigation(
            irrigated_ridges=list(range(start, end + 1)),
            duration_hours=float(duration_hours),
        )

    @agent_tool()
    def apply_pesticide_manual(self, ridge_id: int) -> dict[str, Any]:
        """
        Apply pesticide to a single ridge using the handheld backpack sprayer.
        Suitable for small, localised problems. For larger outbreaks use the
        tractor spray boom instead.

        Args:
            ridge_id: Ridge to spray (0-63).
        """
        if not 0 <= ridge_id < self._farm_world_app.num_ridges:
            return {"error": f"Invalid ridge_id {ridge_id}"}
        if not self._weather_app.is_sprayable:
            return {"error": "Weather conditions do not allow spraying (rain or wind >= 5 m/s)"}
        if not self._farm_world_app.consume_pesticide(_MANUAL_PESTICIDE_L_PER_RIDGE):
            return {
                "error": (
                    f"Insufficient pesticide in warehouse: "
                    f"need {_MANUAL_PESTICIDE_L_PER_RIDGE:.1f} L"
                )
            }

        self.time_manager.add_offset(_manual_spray_duration())
        self._farm_world_app.update_ridge_pesticide(ridge_id)

        self._manual_spray_log.append({
            "ridge_id": ridge_id,
            "date": self._farm_world_app.get_state()["sim_date"],
            "method": "manual_backpack",
            "pesticide_used_liters": _MANUAL_PESTICIDE_L_PER_RIDGE,
            "duration_s": _manual_spray_duration(),
        })
        self.is_state_modified = True
        return {
            "status": "ok",
            "ridge_id": ridge_id,
            "pesticide_used_liters": _MANUAL_PESTICIDE_L_PER_RIDGE,
        }

    @agent_tool()
    def get_irrigation_log(self) -> dict[str, Any]:
        """
        Return the irrigation history for all ridges.
        """
        return {"irrigation_log": list(self._irrigation_log)}

    def _complete_irrigation_session(self, session_id: str) -> None:
        for index, session in enumerate(self._pending_irrigation_sessions):
            if session["session_id"] != session_id:
                continue
            for ridge_id in session["irrigated_ridges"]:
                self._farm_world_app.set_irrigation_pending(ridge_id, session["add_vwc"])
            del self._pending_irrigation_sessions[index]
            self.is_state_modified = True
            return

    def _start_irrigation(
        self,
        *,
        irrigated_ridges: list[int],
        duration_hours: float,
    ) -> dict[str, Any]:
        pending_response = self._get_pending_irrigation_response(irrigated_ridges)
        if pending_response is not None:
            return pending_response

        duration_s = _IRRIGATION_SETUP_S + int(duration_hours * _IRRIGATION_S_PER_HOUR)
        add_vwc = duration_hours * _IRRIGATION_VWC_PER_HOUR
        self.time_manager.add_offset(duration_s)

        start = irrigated_ridges[0]
        end = irrigated_ridges[-1]
        session_id = str(uuid.uuid4())[:8]
        requested_at = self.time_manager.time()
        effect_ready_at = requested_at + _IRRIGATION_EFFECT_DELAY_S
        session = {
            "session_id": session_id,
            "start": start,
            "end": end,
            "irrigated_ridges": list(irrigated_ridges),
            "duration_hours": duration_hours,
            "add_vwc": add_vwc,
            "requested_at": requested_at,
            "effect_ready_at": effect_ready_at,
        }
        self._pending_irrigation_sessions.append(session)
        self.schedule_event(
            NotificationEvent(
                time_start=effect_ready_at,
                time_duration=0,
                message=(
                    f"{self.name}: irrigation effect ready for ridges {start}-{end}. "
                    "Re-read soil sensors to confirm."
                ),
                callback=lambda: self._complete_irrigation_session(session_id),
            )
        )

        for ridge_id in irrigated_ridges:
            self._irrigation_log.append({
                "ridge_id": ridge_id,
                "duration_hours": duration_hours,
                "duration_s": duration_s,
                "date": self._farm_world_app.get_state()["sim_date"],
            })

        self.is_state_modified = True
        response = {
            "status": "irrigation_started",
            "irrigated_ridges": list(irrigated_ridges),
            "duration_hours_per_ridge": duration_hours,
            "total_duration_minutes": round(duration_s / 60, 1),
            "effect_ready_at": effect_ready_at,
            "eta_minutes_to_confirmation": round(_IRRIGATION_EFFECT_DELAY_S / 60.0, 1),
            "message": (
                "Irrigation run finished. Soil moisture response should be checked "
                "after the 2-hour notification arrives."
            ),
        }
        if len(irrigated_ridges) == 1:
            response["ridge_id"] = irrigated_ridges[0]
            response["duration_hours"] = duration_hours
            response["duration_minutes"] = round(duration_s / 60, 1)
        return response

    def _get_pending_irrigation_response(
        self,
        irrigated_ridges: list[int],
    ) -> dict[str, Any] | None:
        requested_ridges = set(irrigated_ridges)
        for session in self._pending_irrigation_sessions:
            if requested_ridges.isdisjoint(session["irrigated_ridges"]):
                continue
            return {
                "status": "irrigation_pending",
                "irrigated_ridges": list(session["irrigated_ridges"]),
                "effect_ready_at": session["effect_ready_at"],
                "message": (
                    "Irrigation effect is still pending for part of this range. "
                    "Wait for the notification before confirming soil moisture."
                ),
            }
        return None
