---
name: game-ui-implementation
description: Use when approved game UI specifications, handoff measurements, and independently reviewed assets are ready for runtime integration.
---

## Role
Implement the approved UI contract without redesigning content, behavior, typography, navigation, or economy. Keep visual, live-data, layout, and input ownership explicit and testable.

## Inputs
- Approved screen specification and handoff.
- The handoff's current `Component implementation binding matrix`.
- Resolved mockup selection under the shared UI decision rules, bound to exact composite hashes.
- Asset-readiness packet in an explicit production mode and its matching independent asset-review disposition.
- The asset packet's current `Component production disposition matrix`, binding readiness, and packet readiness.
- Source-parity records, supported targets, acceptance map, component/state IDs, and current code/data/input/test owners.

Before tests/code, recompute locks: every visible family must be new production or verified reuse, none missing; target-size evidence must use intended runtime bytes. Return stale/incomplete/mismatched/unapproved inputs upstream.

Produced/file-backed art requires `Decision: APPROVE ASSET QUALITY`; otherwise only that art verdict is NOT APPLICABLE. Packet readiness, parity and target-size rendered evidence remain required.

Each binding must share catalog identity/fingerprint across handoff, asset packet and current catalog. Require handoff READY and both asset binding/packet READY_FOR_IMPLEMENTATION. Code-native/native-widget ASSET_NOT_REQUIRED never waives readiness.

## Work and handoff
1. Implement only approved content, geometry, components and reviewed assets; separate live data, layout and input ownership.
2. Follow [output and approval rules](references/output-contract.md) for this stage; preserve exact schemas and required coverage.
3. Return the implementation packet for runtime validation. Do not redesign or claim acceptance from successful compilation.

## Verification boundary
Freeze artifact/revision, criteria, target and repair scope. A separate subagent verifies; the author repairs only returned in-scope failures and the verifier rechecks affected criteria. Preserve unaffected valid evidence. Follow the retry budget (default two); block on exhaustion or unavailable independent verification. Defer out-of-scope findings without new work/gates. Supervisors check report scope/evidence; do not create recursive reviewers.

## Shared workflow contract
Apply [role, output and language rules](../game-task-planning/references/role-contract.md), including direct calls. Resolve approval/selection through the [shared UI decision rules](../game-task-planning/references/ui-adapter.md); preserve exact UI schemas and independent quality gates.
