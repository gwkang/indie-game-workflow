---
name: game-ui-implementation
description: Use for bounded code-native UI runtime-source preparation or for runtime integration after approved specifications, handoff measurements, and required asset readiness.
---

## Role
Implement the approved UI contract without redesigning content, behavior, typography, navigation, or economy. Keep visual, live-data, layout, and input ownership explicit and testable.

## Bounded runtime-source preparation
Only when a `READY` row in an approved handoff and matching approved catalog declare an `ASSET_NOT_REQUIRED` code-native/native-widget binding whose exact source lacks target-size rendered parity, prepare that catalog-declared adapter/source and the minimal render fixture needed by game-ui-asset-production. Freeze the binding identity, fingerprint, allowed inputs, protected properties, states, declared adapter contract, intended source locator, target and consumer. If the source file is uncreated, record pre-state `ABSENT` without a pre-hash; hash the produced source and fixture before separate verification and asset parity. This is a separate candidate with its own scoped evidence and independent verification; leave asset packet and full implementation readiness `BLOCKED` until their owners verify the required evidence.

Do not integrate the screen, bind live content/input, implement navigation or behavior, substitute a helper for the declared adapter, change component design or produce replacement art in this mode. Return source and target-size rendered evidence to asset production for parity assessment. An uncreated file at the declared locator is permitted; a missing or conflicting approved handoff/catalog, adapter contract or intended locator returns to its owner. Full integration still requires every readiness gate below.

## Inputs for full integration
- Approved screen specification and handoff.
- The handoff's current `Component implementation binding matrix`.
- Resolved mockup selection under the shared UI decision rules, bound to exact composite hashes.
- Asset-readiness packet in an explicit production mode and its matching independent asset-review disposition.
- The asset packet's current `Component production disposition matrix`, binding readiness, and packet readiness.
- Source-parity records, supported targets, acceptance map, component/state IDs, and current code/data/input/test owners.

Before full integration tests/code, recompute locks: every visible family must be new production or verified reuse, none missing; target-size evidence must use intended runtime bytes. Return stale/incomplete/mismatched/unapproved inputs upstream. The bounded source-preparation mode above uses only its stated prerequisites and cannot be treated as full integration.

Produced/file-backed art requires `Decision: APPROVE ASSET QUALITY`; otherwise only that art verdict is NOT APPLICABLE. Packet readiness, parity and target-size rendered evidence remain required.

Each binding must share catalog identity/fingerprint across handoff, asset packet and current catalog. Require handoff READY and both asset binding/packet READY_FOR_IMPLEMENTATION. Code-native/native-widget ASSET_NOT_REQUIRED never waives readiness.

After full integration, compare each code-native source/build and relevant render dependency with the asset packet's exact parity evidence before handing off to runtime validation. If an affected source, fixture or dependency drifted, treat that binding and packet readiness as `BLOCKED` and return to asset production to record the updated disposition, recheck parity and obtain independent verification. Preserve unaffected valid evidence; resume full integration only after readiness is restored.

## Work and handoff
1. Implement only approved content, geometry, components and reviewed assets; separate live data, layout and input ownership.
2. Follow [output and approval rules](references/output-contract.md) for this stage; preserve exact schemas and required coverage.
3. Return the implementation packet for runtime validation. Do not redesign or claim acceptance from successful compilation.

## Verification boundary
Freeze artifact/revision, criteria, target and repair scope. A separate subagent verifies; the author repairs only returned in-scope failures and the verifier rechecks affected criteria. Preserve unaffected valid evidence. Follow the retry budget (default two); block on exhaustion or unavailable independent verification. Defer out-of-scope findings without new work/gates. Supervisors check report scope/evidence; do not create recursive reviewers.

## Iteration mode
For early editable screen drafts or an existing screen revision, read [fast iteration](../game-task-planning/references/ui-fast-iteration.md). Preserve role ownership and apply formal approval/readiness gates when promoting a draft or changing runtime.

## Shared workflow contract
Apply [role, output and language rules](../game-task-planning/references/role-contract.md), including direct calls. Resolve approval/selection through the [shared UI decision rules](../game-task-planning/references/ui-adapter.md); preserve exact UI schemas and independent quality gates.
