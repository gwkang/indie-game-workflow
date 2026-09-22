---
name: game-ui-screen-spec
description: Use when an existing game screen needs an exact content, state, interaction, text-fit, or responsive contract before visual mockup work.
---

## Role
Turn approved visual direction and product authority into a truthful screen contract. Every visible or interactive requirement has a source, certainty, and responsive rule.

## Inputs
- An approved `game-ui-art-direction` brief with the exact selected style/motion identity or a compatible previously approved style.
- A current persona contract from [persona-contract.md](references/persona-contract.md), or an explicitly marked provisional contract when product authority has not supplied one.
- Current user decisions, authoritative product documents, and approved screen references.
- The approved `game-ui-component-system` catalog decision, visible template evidence, and exact artifact fingerprint when a repeated family or reuse claim is in scope. Existing templates are reused; only missing or incompatible components require additions.
- Content, data, behavior, navigation, font, input, and accessibility contracts.
- Supported target environments, viewports, safe areas, locales, and runtime evidence when an implementation exists.

Record unavailable required inputs as `OPEN` or `BLOCKED`. Do not replace them with platform conventions, placeholder copy, remembered standards, or values from unrelated projects.

## Work and handoff
1. Trace visible content, state, input and responsive rules to product authority and exact reusable bindings.
2. Convert the persona into a small information-priority contract: primary task, first-read region, secondary/disclosed content, maximum simultaneous groups, and state-specific visibility. Do not treat a complete content inventory as a requirement to show everything at once.
3. Follow [output and approval rules](references/output-contract.md) for this stage; preserve exact schemas and required coverage.
4. Produce the screen contract and runtime coverage map. Keep required design approval separate from changing implementation evidence; do not invent thresholds or downstream work.

## Verification boundary
Freeze artifact/revision, criteria, target and repair scope. A separate subagent verifies; the author repairs only returned in-scope failures and the verifier rechecks affected criteria. Preserve unaffected valid evidence. Follow the retry budget (default two); block on exhaustion or unavailable independent verification. Defer out-of-scope findings without new work/gates. Supervisors check report scope/evidence; do not create recursive reviewers.

## Shared workflow contract
Apply [role, output and language rules](../game-task-planning/references/role-contract.md), including direct calls. Resolve approval/selection through the [shared UI decision rules](../game-task-planning/references/ui-adapter.md); preserve exact UI schemas and independent quality gates.
