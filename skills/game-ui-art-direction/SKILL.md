---
name: game-ui-art-direction
description: Use when an existing game's screen is visually inconsistent, off-brand, or needs an approved visual-direction brief before mockup or production work.
---

## Role
Define a screen's visual intent and source authority without redesigning product content or performing downstream production work.

## Inputs
- Current user decisions that affect the screen.
- The project's authoritative product and visual-design documents.
- Approved screen-specific references and their current or superseded status.
- The approved component catalog when repeated visual families, claimed reuse, or component drift are in scope.
- A current runtime capture when diagnosing an existing screen; treat it as evidence, not design authority.

Record unavailable inputs as `OPEN` or `BLOCKED`. Do not infer the project name, genre, platform, runtime, viewport, locale, content, interaction model, or accessibility requirements from common conventions.

## Work and handoff
1. Resolve source authority and the intended visual experience; classify reusable family needs.
2. Follow [output and approval rules](references/output-contract.md) for this stage; preserve exact schemas and required coverage.
3. Produce the direction brief only. Keep DRAFT until its decision is resolved under the shared UI decision rules; route family decisions to game-ui-component-system.

## Verification boundary
Freeze artifact/revision, criteria, target and repair scope. A separate subagent verifies; the author repairs only returned in-scope failures and the verifier rechecks affected criteria. Preserve unaffected valid evidence. Follow the retry budget (default two); block on exhaustion or unavailable independent verification. Defer out-of-scope findings without new work/gates. Supervisors check report scope/evidence; do not create recursive reviewers.

## Shared workflow contract
Apply [role, output and language rules](../game-task-planning/references/role-contract.md), including direct calls. Resolve approval/selection through the [shared UI decision rules](../game-task-planning/references/ui-adapter.md); preserve exact UI schemas and independent quality gates.
