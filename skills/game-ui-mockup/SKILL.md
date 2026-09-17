---
name: game-ui-mockup
description: Create editable exploratory game screens for early feedback, or formal full-screen visual candidates from approved direction and screen specifications.
---

## Role
Choose the exploratory draft path in [fast iteration](../game-task-planning/references/ui-fast-iteration.md) for early screen feedback before style/template approval. Its editable source and scoped draft record are separate from the formal path below. Formal mockups are immutable design evidence from approved direction and screen truth, not runtime screens or implementation shortcuts.

## Formal candidate inputs
- Approved `game-ui-art-direction` and `game-ui-screen-spec` artifacts.
- The screen specification's approved component binding inventory. For every `reuse:<componentId>@<version>` entry, require its catalog artifact fingerprint, consumer, allowed instance inputs, protected properties, required states, canonical representation, and declared evidence capability.
- Current and superseded references, each labeled by role.
- Representative content, states, target viewports, safe areas, and text-fit cases named by the screen specification.
- The protected content lock, including reproducible locators and hashes for content that must remain exact.
- Provenance requirements, output destination, and requested candidate count. A user-supplied generation-attempt budget is optional.

If an approved input is missing or conflicting, stop and mark it `OPEN` or `BLOCKED`. Do not replace it with placeholders, common layouts, remembered platform conventions, or implementation details.

## Formal candidate work and handoff
1. Compose full-screen candidates using approved content and canonical component bindings.
2. Follow [output and approval rules](references/output-contract.md) for this stage; preserve exact schemas and required coverage.
3. Return immutable candidate hashes and fidelity evidence. Keep DRAFT until exact selection under the shared UI decision rules; never turn a mockup into a runtime texture.

## Verification boundary
Freeze artifact/revision, criteria, target and repair scope. A separate subagent verifies; the author repairs only returned in-scope failures and the verifier rechecks affected criteria. Preserve unaffected valid evidence. Follow the retry budget (default two); block on exhaustion or unavailable independent verification. Defer out-of-scope findings without new work/gates. Supervisors check report scope/evidence; do not create recursive reviewers.

## Iteration mode
For early editable screen drafts or an existing screen revision, read [fast iteration](../game-task-planning/references/ui-fast-iteration.md). Preserve role ownership and apply formal approval/readiness gates when promoting a draft or changing runtime.

## Shared workflow contract
Apply [role, output and language rules](../game-task-planning/references/role-contract.md), including direct calls. Resolve approval/selection through the [shared UI decision rules](../game-task-planning/references/ui-adapter.md); preserve exact UI schemas and independent quality gates.
