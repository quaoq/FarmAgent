from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from openai import OpenAI

from rsare.research_suite.executor import ScenarioRunConfig, run_single_scenario


class SuiteConfigError(ValueError):
    pass


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    pack_name: str
    family: str
    scenario_id: str
    model_profile: str
    model: str
    provider: str
    endpoint: str | None
    output_dir: str
    repeat_index: int
    export: bool
    temperature: float
    model_resolution: str
    a2a_enabled: bool
    a2a_app_prop: float
    a2a_policy: str
    a2a_app_agent: str
    a2a_model_profile: str | None
    a2a_model: str | None
    a2a_provider: str | None
    a2a_endpoint: str | None
    a2a_model_resolution: str | None


def load_suite_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise SuiteConfigError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise SuiteConfigError("Top-level suite config must be a mapping")
    for key in ["scenario_sets", "model_profiles", "packs"]:
        if key not in payload:
            raise SuiteConfigError(f"Missing required section: {key}")
    return payload


def _ensure_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise SuiteConfigError(f"{name} must be a non-empty list")
    cleaned = [str(item).strip() for item in value if str(item).strip()]
    if not cleaned:
        raise SuiteConfigError(f"{name} must contain non-empty string values")
    return cleaned


_PREFLIGHT_CACHE: dict[tuple[str, str, str | None], tuple[bool, str | None]] = {}


def _preflight_model_access(
    model: str,
    provider: str,
    endpoint: str | None,
) -> tuple[bool, str | None]:
    key = (provider, model, endpoint)
    if key in _PREFLIGHT_CACHE:
        return _PREFLIGHT_CACHE[key]
    provider_norm = provider.lower().strip()
    if provider_norm not in {"openai", "llama-api"}:
        result = (True, "skip_non_openai_provider")
        _PREFLIGHT_CACHE[key] = result
        return result

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLAMA_API_KEY")
    if not api_key:
        result = (False, "missing_api_key")
        _PREFLIGHT_CACHE[key] = result
        return result
    base_url = endpoint or os.getenv("OPENAI_BASE_URL") or os.getenv("LLAMA_API_BASE")
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            temperature=0,
        )
        result = (True, None)
    except Exception as exc:  # pragma: no cover - network/provider dependent
        result = (False, str(exc))
    _PREFLIGHT_CACHE[key] = result
    return result


def _resolve_real_model_with_fallback(
    model: str,
    provider: str,
    endpoint: str | None,
    resolution: str,
    enable_preflight: bool,
) -> tuple[str, str, str | None, str]:
    provider_norm = provider.lower().strip()
    endpoint_resolved = endpoint
    if provider_norm not in {"openai", "llama-api"}:
        return model, provider_norm, endpoint_resolved, resolution

    preferred, fallback = "o4-mini", "gpt-4o-mini"
    if not enable_preflight:
        return preferred, provider_norm, endpoint_resolved, "real_preflight_skipped_o4_mini"

    ok_preferred, _ = _preflight_model_access(preferred, provider_norm, endpoint_resolved)
    if ok_preferred:
        return preferred, provider_norm, endpoint_resolved, "real_preflight_o4_mini"

    ok_fallback, _ = _preflight_model_access(fallback, provider_norm, endpoint_resolved)
    if ok_fallback:
        return fallback, provider_norm, endpoint_resolved, "real_fallback_gpt_4o_mini"
    return fallback, provider_norm, endpoint_resolved, "real_fallback_unverified"


def _resolve_profile(
    profile_name: str,
    profiles: dict[str, Any],
    force_mock: bool,
    force_real: bool,
    enable_real_model_preflight: bool,
) -> tuple[str, str, str | None, str]:
    if profile_name not in profiles:
        raise SuiteConfigError(f"Unknown model profile '{profile_name}'")
    profile = profiles[profile_name]
    if not isinstance(profile, dict):
        raise SuiteConfigError(f"model_profiles.{profile_name} must be a mapping")

    model = str(profile.get("model", "")).strip()
    provider = str(profile.get("provider", "")).strip()
    endpoint = profile.get("endpoint")
    endpoint = str(endpoint) if endpoint is not None else None
    resolution = "profile"

    if force_mock:
        return "mock-model", "mock", None, "forced_mock"
    if force_real and provider == "mock":
        model = "o4-mini"
        provider = "openai"
        resolution = "force_real_from_mock_profile"
    if force_real:
        model, provider, endpoint, resolution = _resolve_real_model_with_fallback(
            model=model,
            provider=provider,
            endpoint=endpoint,
            resolution=resolution,
            enable_preflight=enable_real_model_preflight,
        )
    if not model:
        raise SuiteConfigError(f"model missing for profile '{profile_name}'")
    if not provider:
        raise SuiteConfigError(f"provider missing for profile '{profile_name}'")
    return model, provider, endpoint, resolution


def _resolve_a2a_block(pack_name: str, pack: dict[str, Any]) -> dict[str, Any]:
    a2a = pack.get("a2a")
    if a2a is None:
        return {
            "enabled": False,
            "app_prop": 0.0,
            "policy": "generic",
            "app_agent": "default_app_agent",
            "model_profile": None,
        }
    if not isinstance(a2a, dict):
        raise SuiteConfigError(f"packs.{pack_name}.a2a must be a mapping")

    enabled = bool(a2a.get("enabled", False))
    app_prop = float(a2a.get("app_prop", 0.5 if enabled else 0.0))
    if app_prop < 0.0 or app_prop > 1.0:
        raise SuiteConfigError(f"packs.{pack_name}.a2a.app_prop must be in [0.0, 1.0]")
    if not enabled:
        app_prop = 0.0
    policy = str(a2a.get("policy", "typed_experts" if enabled else "generic")).strip()
    if policy not in {"typed_experts", "generic"}:
        raise SuiteConfigError(f"packs.{pack_name}.a2a.policy must be typed_experts|generic")
    if not enabled:
        policy = "generic"
    app_agent = str(a2a.get("app_agent", "default_app_agent")).strip()
    model_profile = a2a.get("model_profile")
    if model_profile is not None:
        model_profile = str(model_profile).strip() or None
    return {
        "enabled": enabled,
        "app_prop": app_prop,
        "policy": policy,
        "app_agent": app_agent,
        "model_profile": model_profile,
    }


def expand_run_specs(
    config: dict[str, Any],
    force_mock: bool = False,
    force_real: bool = False,
    enable_real_model_preflight: bool = True,
) -> list[RunSpec]:
    defaults = config.get("defaults", {})
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, dict):
        raise SuiteConfigError("defaults must be a mapping")

    base_output = str(defaults.get("output_root", "outputs/agent_suite")).strip()
    export = bool(defaults.get("export", True))
    default_repeats = int(defaults.get("repeats", 1))
    temperature = float(defaults.get("temperature", 0.1))

    scenario_sets = config["scenario_sets"]
    model_profiles = config["model_profiles"]
    packs = config["packs"]

    run_specs: list[RunSpec] = []
    for pack_name in sorted(packs.keys()):
        pack = packs[pack_name]
        if not isinstance(pack, dict):
            raise SuiteConfigError(f"Pack '{pack_name}' must be a mapping")
        families = _ensure_list(pack.get("families"), f"packs.{pack_name}.families")
        referenced_sets = _ensure_list(
            pack.get("scenario_sets"), f"packs.{pack_name}.scenario_sets"
        )
        profile_name = str(pack.get("model_profile", "")).strip()
        if not profile_name:
            raise SuiteConfigError(f"packs.{pack_name}.model_profile is required")
        repeats = int(pack.get("repeats", default_repeats))
        if repeats <= 0:
            raise SuiteConfigError(f"packs.{pack_name}.repeats must be > 0")
        a2a = _resolve_a2a_block(pack_name, pack)

        model, provider, endpoint, model_resolution = _resolve_profile(
            profile_name=profile_name,
            profiles=model_profiles,
            force_mock=force_mock,
            force_real=force_real,
            enable_real_model_preflight=enable_real_model_preflight,
        )
        a2a_model_profile = None
        a2a_model = None
        a2a_provider = None
        a2a_endpoint = None
        a2a_model_resolution = None
        if a2a["enabled"]:
            a2a_model_profile = a2a["model_profile"]
            if a2a_model_profile is None:
                a2a_model = model
                a2a_provider = provider
                a2a_endpoint = endpoint
                a2a_model_resolution = "inherit_main_model"
            else:
                (
                    a2a_model,
                    a2a_provider,
                    a2a_endpoint,
                    a2a_model_resolution,
                ) = _resolve_profile(
                    profile_name=a2a_model_profile,
                    profiles=model_profiles,
                    force_mock=force_mock,
                    force_real=force_real,
                    enable_real_model_preflight=enable_real_model_preflight,
                )

        scenarios: list[str] = []
        for set_name in referenced_sets:
            if set_name not in scenario_sets:
                raise SuiteConfigError(
                    f"Unknown scenario_set '{set_name}' in pack '{pack_name}'"
                )
            scenarios.extend(_ensure_list(scenario_sets[set_name], f"scenario_sets.{set_name}"))
        deduped_scenarios = list(dict.fromkeys(scenarios))
        for family in families:
            for scenario_id in deduped_scenarios:
                for repeat_index in range(repeats):
                    run_id = f"{pack_name}__{family}__{scenario_id}__r{repeat_index + 1}"
                    output_dir = Path(base_output) / run_id
                    run_specs.append(
                        RunSpec(
                            run_id=run_id,
                            pack_name=pack_name,
                            family=family,
                            scenario_id=scenario_id,
                            model_profile=profile_name,
                            model=model,
                            provider=provider,
                            endpoint=endpoint,
                            output_dir=str(output_dir),
                            repeat_index=repeat_index,
                            export=export,
                            temperature=temperature,
                            model_resolution=model_resolution,
                            a2a_enabled=a2a["enabled"],
                            a2a_app_prop=a2a["app_prop"],
                            a2a_policy=a2a["policy"],
                            a2a_app_agent=a2a["app_agent"],
                            a2a_model_profile=a2a_model_profile,
                            a2a_model=a2a_model,
                            a2a_provider=a2a_provider,
                            a2a_endpoint=a2a_endpoint,
                            a2a_model_resolution=a2a_model_resolution,
                        )
                    )
    return run_specs


def _flatten_row(row: dict[str, Any]) -> dict[str, Any]:
    flat = dict(row)
    telemetry = flat.pop("telemetry", {})
    if isinstance(telemetry, dict):
        for key, value in telemetry.items():
            flat[f"telemetry_{key}"] = value
    converted_apps = flat.get("a2a_converted_apps")
    if isinstance(converted_apps, list):
        flat["a2a_converted_apps"] = json.dumps(converted_apps)
    return flat


def run_suite(
    run_specs: list[RunSpec],
    dry_run: bool = False,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    if repo_root is None:
        repo_root = Path.cwd()
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suite_output_root = repo_root / "outputs" / "agent_suite_runs" / timestamp
    suite_output_root.mkdir(parents=True, exist_ok=True)

    manifest_rows = [asdict(spec) for spec in run_specs]
    manifest_path = suite_output_root / "suite_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest_rows, handle, indent=2)

    if dry_run:
        return {
            "mode": "dry_run",
            "suite_output_root": str(suite_output_root),
            "manifest_path": str(manifest_path),
            "runs": manifest_rows,
        }

    rows: list[dict[str, Any]] = []
    for spec in run_specs:
        output_dir = suite_output_root / spec.run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        config = ScenarioRunConfig(
            run_id=spec.run_id,
            pack_name=spec.pack_name,
            family_id=spec.family,
            scenario_id=spec.scenario_id,
            model=spec.model,
            provider=spec.provider,
            endpoint=spec.endpoint,
            output_dir=str(output_dir),
            export=spec.export,
            temperature=spec.temperature,
            a2a_enabled=spec.a2a_enabled,
            a2a_app_prop=spec.a2a_app_prop,
            a2a_policy=spec.a2a_policy,
            a2a_app_agent=spec.a2a_app_agent,
            model_resolution=spec.model_resolution,
        )
        try:
            row = run_single_scenario(config)
        except Exception as error:  # pragma: no cover - runtime/environment dependent
            row = {
                "run_id": spec.run_id,
                "pack_name": spec.pack_name,
                "family": spec.family,
                "scenario_id": spec.scenario_id,
                "model": spec.model,
                "provider": spec.provider,
                "endpoint": spec.endpoint,
                "status": "failed",
                "error": str(error),
                "telemetry": {},
                "infra_exit_ok": False,
                "infra_auth_ok": "auth" not in str(error).lower(),
                "infra_connectivity_ok": "connection" not in str(error).lower(),
                "infra_llm_calls_positive": False,
                "infra_trace_exported": False,
                "infra_pass": False,
                "a2a_enabled": spec.a2a_enabled,
                "a2a_app_prop": spec.a2a_app_prop,
                "a2a_policy": spec.a2a_policy,
                "a2a_app_agent": spec.a2a_app_agent,
                "a2a_converted_apps": [],
                "output_dir": str(output_dir),
            }
        row.update(
            {
                "model_profile": spec.model_profile,
                "model_resolution": spec.model_resolution,
                "repeat_index": spec.repeat_index,
                "a2a_model_profile": spec.a2a_model_profile,
                "a2a_model": spec.a2a_model,
                "a2a_provider": spec.a2a_provider,
                "a2a_endpoint": spec.a2a_endpoint,
                "a2a_model_resolution": spec.a2a_model_resolution,
            }
        )
        rows.append(row)

    json_path = suite_output_root / "suite_results.json"
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)

    csv_path = suite_output_root / "suite_results.csv"
    flat_rows = [_flatten_row(row) for row in rows]
    field_names: list[str] = []
    for row in flat_rows:
        for key in row.keys():
            if key not in field_names:
                field_names.append(key)
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        for row in flat_rows:
            writer.writerow(row)

    return {
        "mode": "run",
        "suite_output_root": str(suite_output_root),
        "manifest_path": str(manifest_path),
        "json_path": str(json_path),
        "csv_path": str(csv_path),
        "rows": rows,
    }
