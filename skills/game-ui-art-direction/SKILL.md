---
name: game-ui-art-direction
description: Use when an existing game's screen is visually inconsistent, off-brand, or needs an approved visual-direction brief before mockup or production work.
---

## Role
Define a screen's visual intent and source authority without redesigning product content or performing downstream production work.

## Inputs
- Current user decisions that affect the screen.
- Optional user reference URLs for style, component or motion choices; proceeding without one remains valid.
- The project's authoritative product and visual-design documents.
- Approved screen-specific references and their current or superseded status.
- The approved component catalog when repeated visual families, claimed reuse, or component drift are in scope.
- A current runtime capture when diagnosing an existing screen; treat it as evidence, not design authority.

Record unavailable inputs as `OPEN` or `BLOCKED`. Do not infer the project name, genre, platform, runtime, viewport, locale, content, interaction model, or accessibility requirements from common conventions.

## Work and handoff
1. Resolve source authority and the intended visual experience; classify reusable family needs.
2. Follow [output and approval rules](references/output-contract.md) for this stage; preserve exact schemas and required coverage.
3. When style or motion is unresolved, consult the [sample library](references/sample-library.md) before producing new samples. Present compatible immutable samples by exact ID/version/fingerprint; create only the smallest project-local addition for a recorded missing capability and follow the [independent sample guide](references/independent-samples.md).
4. Produce the direction brief and only the comparison evidence required for the unresolved decision. Keep DRAFT until its decision is resolved under the shared UI decision rules; route family decisions to game-ui-component-system. A library entry is selectable evidence, not a selected component or product approval.

## Verification boundary
Freeze artifact/revision, criteria, target and repair scope. A separate subagent verifies; the author repairs only returned in-scope failures and the verifier rechecks affected criteria. Preserve unaffected valid evidence. Follow the retry budget (default two); block on exhaustion or unavailable independent verification. Defer out-of-scope findings without new work/gates. Supervisors check report scope/evidence; do not create recursive reviewers.

## Iteration mode
For early editable screen drafts or an existing screen revision, read [fast iteration](../game-task-planning/references/ui-fast-iteration.md). Preserve role ownership and apply formal approval/readiness gates when promoting a draft or changing runtime.

## Shared workflow contract
Apply [role, output and language rules](../game-task-planning/references/role-contract.md), including direct calls. Resolve approval/selection through the [shared UI decision rules](../game-task-planning/references/ui-adapter.md); preserve exact UI schemas and independent quality gates.
