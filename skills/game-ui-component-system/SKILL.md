---
name: game-ui-component-system
description: Use when multiple game screens should share a UI component, a reusable control has drifted from approved references, or a shared component family needs versioning or review.
---

## Role
Decide whether repeated UI belongs to an approved reusable family. The core rule is: reuse is a versioned, evidence-backed contract, not a visual resemblance or a convenient shared helper.

## Inputs
- The current project's approved profile, including catalog location, supported representations, runtime adapter, evidence capabilities, presentation roles, and approval authority.
- Current authoritative references and their fingerprints.
- The proposed consumers, states, accessibility requirements, and known exceptions.

Keep missing values `OPEN` or `BLOCKED`. Never infer component roles, dimensions, locale, input modality, rendering technology, evidence tools, tolerances, commands, build/source identity fields, signing mechanisms, or approval identities from conventions.

## Work and handoff
1. Resolve family identity/version, allowed inputs, protected properties and reproducible evidence capabilities.
2. Follow [output and approval rules](references/output-contract.md) for this stage; preserve exact schemas and required coverage.
3. Produce the catalog/decision packet under its schema; do not self-approve, design screens or implement components.

## Verification boundary
Freeze artifact/revision, criteria, target and repair scope. A separate subagent verifies; the author repairs only returned in-scope failures and the verifier rechecks affected criteria. Preserve unaffected valid evidence. Follow the retry budget (default two); block on exhaustion or unavailable independent verification. Defer out-of-scope findings without new work/gates. Supervisors check report scope/evidence; do not create recursive reviewers.

## Iteration mode
For early editable screen drafts or an existing screen revision, read [fast iteration](../game-task-planning/references/ui-fast-iteration.md). Preserve role ownership and apply formal approval/readiness gates when promoting a draft or changing runtime.

## Shared workflow contract
Apply [role, output and language rules](../game-task-planning/references/role-contract.md), including direct calls. Resolve approval/selection through the [shared UI decision rules](../game-task-planning/references/ui-adapter.md); preserve exact UI schemas and independent quality gates.
