---
name: game-ui-runtime-validation
description: Use when an implemented game UI needs actual-runtime evidence for rendering, content, states, input, and fidelity before acceptance review.
---

## Role
Validate an unchanged build in its actual runtime. Static tests do not prove rendered fidelity, loaded assets, content boundaries, or usable input geometry.

## Inputs
- Approved screen specification, mockup, handoff comparison map, asset verdict, and implementation evidence.
- The implementation packet's current `Component runtime integration matrix` and matching catalog artifact fingerprint.
- Exact build fingerprint, launch/capture method, fixture data, expected states, targets, locales, and safe areas.
- Approved composite hashes and source-parity records.

Use the declared browser/engine/emulator/simulator/device/harness. Record environment, scale, target dimensions, safe area, fixture, state, locale, timestamp and fingerprint; recheck fingerprint after capture.

Separate design identity from capture freshness: code changes need not erase historical design approval, but that approval proves nothing about the current build. Review changed design authorities for relevance. Before requesting current approval, run the declared freshness/readiness check on current source/build, not archived evidence. Scoped PASS or author readiness cannot override overall BLOCKED, missing coverage/raw evidence or changed inputs. Without an executable check, explicitly compare complete locked source/build inventories and required coverage with raw evidence. Unresolved/stale evidence remains BLOCKED from acceptance and the runtime decision.

Keep the repository read-only. Use normal runtime controls and isolated fixtures; do not fix code/assets/data/evidence or self-approve.

## Work and handoff
1. Observe an unchanged candidate in its actual runtime using selected screen/state/viewport coverage and source identity.
2. Follow [output and approval rules](references/output-contract.md) for this stage; preserve exact schemas and required coverage.
3. Return raw observations and coverage verdicts for acceptance review. Do not repair product or evidence during verification.

Before judging, apply [current-state and prior-record review](../game-task-planning/references/verification-scope.md#review-the-current-state-before-alleging-a-defect): inspect relevant implementation and available wiki/decision/review records, check counterevidence, and report no findings when warranted. Do not expand scope or manufacture defects.

## Verification boundary
Freeze artifact/revision, criteria, target and repair scope. A separate subagent verifies; the author repairs only returned in-scope failures and the verifier rechecks affected criteria. Preserve unaffected valid evidence. Follow the retry budget (default two); block on exhaustion or unavailable independent verification. Defer out-of-scope findings without new work/gates. Supervisors check report scope/evidence; do not create recursive reviewers.

## Shared workflow contract
Apply [role, output and language rules](../game-task-planning/references/role-contract.md), including direct calls. Resolve approval/selection through the [shared UI decision rules](../game-task-planning/references/ui-adapter.md); preserve exact UI schemas and independent quality gates.
