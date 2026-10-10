"""Resolve portable task tiers and prepare supported new-worker spawn arguments."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TIERS = ("highest-judgment", "complex-execution", "balanced-execution", "high-volume")
EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}
SKILLS = (
    "art-asset-review", "game-bug-diagnosis", "game-bug-reproduction",
    "game-build-packaging", "game-camera-implementation", "game-code-review",
    "game-content-loading", "game-feature-spec", "game-functional-verification",
    "game-improvement-assessment", "game-input-implementation", "game-knowledge-maintenance",
    "game-movement-implementation", "game-performance-profiling", "game-platform-integration",
    "game-project-profile", "game-rule-implementation", "game-save-implementation",
    "game-session-implementation", "game-task-planning", "game-technical-design",
    "game-test-design", "game-test-infrastructure", "game-ui-acceptance-review",
    "game-ui-art-direction", "game-ui-asset-production", "game-ui-component-system",
    "game-ui-handoff", "game-ui-implementation", "game-ui-mockup", "game-ui-runtime-validation",
    "game-ui-screen-spec", "game-ui-ux-design", "game-workflow", "game-workflow-audit",
    "game-workflow-supervision", "indie-game-bugfix", "indie-game-development",
    "indie-game-improvement",
)


class ProfileError(ValueError):
    pass


def text(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def common_profile_path():
    """The bundled asset is independent of cwd and project-specific settings."""
    target = Path(__file__).absolute().parent.parent / "references/model-routing-defaults.json"
    for part in (target, *target.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ProfileError("bundled model profile must not use linked files or folders")
    return target


def validate_profile(data):
    required = {"schemaVersion", "revision", "tiers"}
    if not isinstance(data, dict) or not required <= set(data):
        raise ProfileError("profile requires schemaVersion, revision and tiers")
    if type(data["schemaVersion"]) is not int or data["schemaVersion"] != 1 or not text(data["revision"]):
        raise ProfileError("unsupported model-routing profile")
    if not isinstance(data["tiers"], dict) or set(data["tiers"]) != set(TIERS):
        raise ProfileError("profile must define exactly the four capability tiers")
    for tier, row in data["tiers"].items():
        if not isinstance(row, dict) or set(row) != {"preferredModels", "reasoningEffort"}:
            raise ProfileError(f"invalid tier row: {tier}")
        models = row["preferredModels"]
        if (not isinstance(models, list) or not models or not all(text(model) for model in models)
                or len(models) != len(set(models))):
            raise ProfileError(f"invalid preferredModels: {tier}")
        if not isinstance(row["reasoningEffort"], str) or row["reasoningEffort"] not in EFFORTS:
            raise ProfileError(f"invalid reasoningEffort: {tier}")
    for key in ("onUnavailable", "onUnsupportedOverride"):
        if key in data and (not isinstance(data[key], str) or data[key] not in ("blocked", "host-default")):
            raise ProfileError(f"invalid {key}")
    if "skillTiers" in data:
        table = data["skillTiers"]
        if (not isinstance(table, dict) or set(table) != set(SKILLS)
                or any(not isinstance(tier, str) or tier not in TIERS for tier in table.values())):
            raise ProfileError("skillTiers must map exactly the 39 bundled skills to known tiers")
    return data


def parse_profile(data):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ProfileError(f"duplicate profile key: {key}")
            result[key] = value
        return result
    return validate_profile(json.loads(data, object_pairs_hook=unique_keys))


def validate_common_profile(data):
    validate_profile(data)
    supported = {"schemaVersion", "revision", "tiers", "skillTiers",
                 "onUnavailable", "onUnsupportedOverride"}
    if set(data) - supported:
        raise ProfileError("unknown keys in common model-routing profile")
    if ("skillTiers" not in data or data.get("onUnavailable") != "blocked"
            or data.get("onUnsupportedOverride") != "blocked"):
        raise ProfileError("common profile requires the skill table and strict blocked policies")
    return data


def load_profile(path=None):
    data = parse_profile((common_profile_path() if path is None else Path(path)).read_text(encoding="utf-8-sig"))
    return validate_common_profile(data) if path is None else data


def resolve(profile, tier, available_models, override_supported, explicit_model=None, *, explicit_effort=None):
    """Legacy selection API; effort entitlement is checked when preparing a dispatch."""
    if tier not in TIERS:
        raise ProfileError("unknown capability tier")
    profile = load_profile() if profile is None else validate_profile(profile)
    if (not isinstance(available_models, (list, tuple, set))
            or not all(text(model) for model in available_models) or type(override_supported) is not bool):
        raise ProfileError("available models and override support require current host metadata")
    if explicit_model is not None and not text(explicit_model):
        raise ProfileError("invalid explicit model")
    if explicit_effort is not None and not text(explicit_effort):
        raise ProfileError("invalid explicit effort")
    available = set(available_models)
    row = profile["tiers"][tier]
    result = {"capabilityTier": tier, "reasoningClass": explicit_effort or row["reasoningEffort"],
              "resolvedModel": None, "resolutionSource": "profile-tier",
              "overrideSupported": override_supported, "fallbackReason": None}

    def unavailable(reason, policy):
        decision = profile.get(policy, "host-default")
        result.update(decision=decision, resolvedModel="host-default" if decision == "host-default" else None,
                      resolutionSource="host-default", fallbackReason=reason)
        return result

    if explicit_model is not None:
        result.update(resolutionSource="explicit-user", reasoningClass=explicit_effort)
        if not override_supported or explicit_model not in available:
            result.update(decision="blocked", fallbackReason=("explicit-model-override-unsupported"
                          if not override_supported else "explicit-model-unavailable"))
        else:
            result.update(decision="override", resolvedModel=explicit_model)
        return result
    if not override_supported:
        if explicit_effort is not None:
            result.update(decision="blocked", resolutionSource="explicit-user",
                          fallbackReason="explicit-effort-override-unsupported")
            return result
        return unavailable("model-override-unsupported", "onUnsupportedOverride")
    selected = next((model for model in row["preferredModels"] if model in available), None)
    if selected is None:
        return unavailable("no-tier-candidate-available", "onUnavailable")
    result.update(decision="override", resolvedModel=selected,
                  fallbackReason=None if selected == row["preferredModels"][0] else "preferred-model-unavailable")
    return result


def select_tier(profile, *, skill=None, tier=None, tier_reason=None):
    if tier is not None and tier not in TIERS:
        raise ProfileError("unknown capability tier")
    if tier_reason is not None and not text(tier_reason):
        raise ProfileError("invalid task tier reason")
    if skill is None:
        if tier is None:
            raise ProfileError("a skill or explicit capability tier is required")
        return tier, None, tier_reason or "explicit-tier"
    if not text(skill):
        raise ProfileError("invalid skill ID")
    table = profile.get("skillTiers")
    if table is None:
        table = load_profile()["skillTiers"]
    default = table.get(skill)
    if default is None and (tier is None or not text(tier_reason)):
        raise ProfileError("external skill requires explicit tier and reason")
    if tier is not None and tier != default and not text(tier_reason):
        raise ProfileError("task tier override requires a reason")
    return tier or default, default, tier_reason or "skill-default"


def validate_host_support(support):
    if not isinstance(support, dict) or not all(text(model) for model in support):
        raise ProfileError("host support must map model IDs to supported effort lists")
    for efforts in support.values():
        if (not isinstance(efforts, list) or not efforts or not all(text(effort) for effort in efforts)
                or len(efforts) != len(set(efforts))):
            raise ProfileError("host support requires nonempty unique effort lists")
    return support


def resolve_task(profile=None, *, skill=None, tier=None, tier_reason=None, host_support,
                 override_supported, explicit_model=None, explicit_effort=None):
    """Prepare a new worker; do not switch the root or claim an actual runtime identity."""
    profile = load_profile() if profile is None else validate_profile(profile)
    support = validate_host_support(host_support)
    selected_tier, default, reason = select_tier(profile, skill=skill, tier=tier, tier_reason=tier_reason)
    effort = explicit_effort or profile["tiers"][selected_tier]["reasoningEffort"]
    candidates = list(support) if explicit_model is not None else [model for model in support if effort in support[model]]
    result = resolve(profile, selected_tier, candidates, override_supported, explicit_model,
                     explicit_effort=explicit_effort)
    if explicit_effort is not None and result['decision'] == 'host-default':
        result.update(decision='blocked', resolvedModel=None,
                      fallbackReason='explicit-effort-unavailable', resolutionSource='explicit-user')
    if (explicit_model is None and result["decision"] == "override"
            and profile["tiers"][selected_tier]["preferredModels"][0] in support
            and result["fallbackReason"] == "preferred-model-unavailable"):
        result["fallbackReason"] = "preferred-model-effort-unsupported"
    # Legacy explicit-model selection leaves effort unset; spawn uses the chosen tier default.
    if result["decision"] == "override" and result["reasoningClass"] is None:
        result["reasoningClass"] = profile["tiers"][selected_tier]["reasoningEffort"]
    result.update(profileRevision=profile["revision"], skillId=skill, defaultTier=default,
                  tierSelectionReason=reason, hostSupportConfirmed=False, spawnArgs=None)
    if result["decision"] == "override":
        model, effort = result["resolvedModel"], result["reasoningClass"]
        if effort not in support[model]:
            result.update(decision="blocked", fallbackReason=("explicit-effort-unsupported"
                          if explicit_effort is not None else "model-effort-unsupported"))
        else:
            result.update(hostSupportConfirmed=True,
                          spawnArgs={"model": model, "reasoning_effort": effort, "fork_turns": "none"})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, nargs="?")
    parser.add_argument("--tier", choices=TIERS)
    parser.add_argument("--skill")
    parser.add_argument("--tier-reason")
    parser.add_argument("--available-model", action="append", default=[])
    parser.add_argument("--host-support", type=Path, help="JSON model ID -> effort list from current tool metadata")
    parser.add_argument("--override-supported", action="store_true")
    parser.add_argument("--explicit-model")
    parser.add_argument("--explicit-effort")
    args = parser.parse_args(argv)
    try:
        profile = load_profile(args.profile)
        if args.host_support:
            support = json.loads(args.host_support.read_text(encoding="utf-8-sig"))
            result = resolve_task(profile, skill=args.skill, tier=args.tier, tier_reason=args.tier_reason,
                                  host_support=support, override_supported=args.override_supported,
                                  explicit_model=args.explicit_model, explicit_effort=args.explicit_effort)
        else:
            tier, default, reason = select_tier(profile, skill=args.skill, tier=args.tier, tier_reason=args.tier_reason)
            result = resolve(profile, tier, args.available_model, args.override_supported,
                             args.explicit_model, explicit_effort=args.explicit_effort)
            result.update(profileRevision=profile["revision"], skillId=args.skill, defaultTier=default,
                          tierSelectionReason=reason, hostSupportConfirmed=False, spawnArgs=None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result["decision"] == "blocked" else 0
    except (ProfileError, OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
