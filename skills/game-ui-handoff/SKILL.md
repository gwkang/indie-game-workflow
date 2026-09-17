---
name: game-ui-handoff
description: Use when an approved game UI mockup needs a measurable implementation contract before asset or code work.
---

## Role
Translate approved visual evidence into measurable geometry, ownership, scaling, and state rules without producing assets or code.

## Inputs
- Approved `game-ui-art-direction`, `game-ui-screen-spec`, and `game-ui-mockup` artifacts.
- The approved mockup's `Component reuse-fidelity matrix`, with a current `MATCH` row for every reusable binding.
- Exact selected composite paths, dimensions, hashes, represented states, provenance, and resolved selection authority.
- Protected-content and source-parity records.
- Supported targets, safe areas, reusable components, and current implementation evidence when available.

Stop when an input is missing, stale, conflicting, or bound to a different hash.

## Work and handoff
1. Measure approved references and transfer catalog state IDs plus mockup evidence into the binding contract.
2. Follow [output and approval rules](references/output-contract.md) for this stage; preserve exact schemas and required coverage.
3. Produce geometry, ownership and state rules with the exact binding matrix. Do not produce assets/code; unresolved bindings return to component-system.

## Verification boundary
Freeze artifact/revision, criteria, target and repair scope. A separate subagent verifies; the author repairs only returned in-scope failures and the verifier rechecks affected criteria. Preserve unaffected valid evidence. Follow the retry budget (default two); block on exhaustion or unavailable independent verification. Defer out-of-scope findings without new work/gates. Supervisors check report scope/evidence; do not create recursive reviewers.

## Iteration mode
For early editable screen drafts or an existing screen revision, read [fast iteration](../game-task-planning/references/ui-fast-iteration.md). Preserve role ownership and apply formal approval/readiness gates when promoting a draft or changing runtime.

## Shared workflow contract
Apply [role, output and language rules](../game-task-planning/references/role-contract.md), including direct calls. Resolve approval/selection through the [shared UI decision rules](../game-task-planning/references/ui-adapter.md); preserve exact UI schemas and independent quality gates.
