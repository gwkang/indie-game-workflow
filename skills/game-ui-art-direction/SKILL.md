---
name: game-ui-art-direction
description: Use when an existing game's screen is visually inconsistent, off-brand, or needs an approved visual-direction brief before mockup or production work.
---

## Role
Define a screen's visual intent and source authority. If no compatible selected style and motion language exists, create enough comparable visual and playable motion options for the authorized decision-maker to make an informed choice before new component templates are fixed. Organize unresolved choices by functionally required component family, with independently identifiable form options and playable motion for each applicable style. Each consequential choice needs at least two materially distinct, feasible alternatives; a single proposal or cosmetic recolors do not constitute a choice. A combined board may supplement comparison, but cannot replace family-level options or become a prerequisite for choosing or revising one family. Let project inputs determine the relevant independent axes, including form, depth, corners, text density, actual font candidates and motion; do not predetermine minimal text or typography for the user. Preserve functional meaning and access to necessary information across variants and supported languages.

## Inputs
- Current user decisions that affect the screen.
- A lightweight player persona or audience statement when the direction affects information priority, tone, motion, or accessibility. If none exists, record the smallest evidence-backed working persona and mark it provisional; do not invent demographics or preferences.
- For a formal new/changed screen, the resolved UX decision; for unchanged UX, its documented compatible reuse; for an exploratory draft, provisional UX framing. Preserve player task and information priority while selecting visual treatment.
- Optional user reference URLs for style, component or motion choices. Explicitly offer this input in the selection prompt; proceeding without a URL remains valid. Record intended scope and desired/avoided elements under the reference rules below.
- The project's authoritative product and visual-design documents.
- Approved screen-specific references and their current or superseded status.
- The approved component catalog when repeated visual families, claimed reuse, or component drift are in scope.
- A current runtime capture when diagnosing an existing screen; treat it as evidence, not design authority.

Record unavailable inputs as `OPEN` or `BLOCKED`. Do not infer the project name, genre, platform, runtime, viewport, locale, content, interaction model, or accessibility requirements from common conventions.

For full-screen multi-state/target direction work that is expensive to expand, or after a prior whole-screen visual-quality rejection, resolve visual grounding before expansion. Reuse an exact compatible selected or canonical visual authority when one exists. Otherwise select only bounded project, canonical, professional or genre references that can change the current decision under the shared professional-reference and optional-link rules, or record why additional reference evidence is unnecessary. A user URL, network access or external reference is never mandatory, and reference evidence never authorizes copied assets, features or layouts.

## Work and handoff
1. Resolve source authority and the intended visual experience; classify reusable family needs. If a style or text-density option would obscure the UX decision's primary task or necessary feedback, revise the option or return the conflict to game-ui-ux-design rather than silently changing the flow.
2. Translate the evidence-backed persona or audience statement into no more than three observable visual consequences, such as primary-task prominence, information density or motion restraint, while preserving the resolved UX hierarchy. Keep unconfirmed persona-derived consequences provisional until the product owner confirms them; return conflicts with the UX decision to game-ui-ux-design.
3. Follow [output and approval rules](references/output-contract.md) for this stage; preserve exact schemas and required coverage. When style or motion choices are unresolved, use the [independent sample guide](references/independent-samples.md) to choose meaningful variation axes, build isolated examples and check choice sufficiency; its menus are examples, not project requirements.
4. Reuse a compatible selected style and motion language by exact identity. Otherwise consult the [sample library](references/sample-library.md) and its manifest first, present matching prebuilt options without regenerating them, and create only missing project-local samples under the output contract. Keep them DRAFT until the authorized choice is recorded; when the user retained that choice, show the samples and wait for it. Route selected treatment and family needs to game-ui-component-system. Do not freeze new component appearance from an unselected sample.

When a craft failure can be repaired without revising protected upstream decisions, return `ART_DIRECTION_REVISION_REQUIRED`. When the necessary change belongs upstream, return `BLOCKED_BY_UPSTREAM_CONSTRAINT` with the blocked surface and narrow owner: player task, flow or information hierarchy to `game-ui-ux-design`; screen content, region, state or target contract to `game-ui-screen-spec`; protected font, copy, control or product policy to its product/content owner; missing authority for the visual thesis to the narrow decision owner. Do not spend art-direction repair retries against an unchanged upstream constraint, and keep independent unaffected work moving.

## Verification boundary
Freeze the exact candidate fingerprint, decision/selection scope, criteria, target and repair scope. A separate subagent verifies the same scope and reports `COMPARISON_INTEGRITY` and `VISUAL_CRAFT_READINESS` independently under the [output contract](references/output-contract.md); both need a current `PASS` before the options are offered for selection. If no option passes craft readiness, return `DRAFT_REVISION_REQUIRED` instead of forcing a choice. The author repairs only returned in-scope failures and the verifier rechecks affected criteria. Preserve unaffected valid evidence. Follow the retry budget (default two); block on exhaustion or unavailable independent verification. Defer out-of-scope findings without new work/gates. Supervisors check identity, scope and evidence; do not create recursive reviewers. An exact selected or approved baseline with a proven nonvisual-only change may reuse its still-valid visual verdict without new alternatives or reselection.

Before producing an expensive full-screen multi-state/target packet, or after a prior whole-screen visual-quality rejection, apply the representative craft preflight in the output contract. Freeze the smallest applicable high-risk state/target set, inspect original-detail evidence and obtain a separate verifier result before expansion. A passing preflight permits expansion only; it does not establish the final full-scope verdict. Reuse unchanged preflight evidence only when candidate identity, representative scope and visual-impact proof still match. Do not impose this gate on isolated family/motion samples or an exact approved nonvisual repair.

## Iteration mode
For early editable screen drafts or an existing screen revision, read [fast iteration](../game-task-planning/references/ui-fast-iteration.md). Preserve role ownership and apply formal approval/readiness gates when promoting a draft or changing runtime.

## Shared workflow contract
Apply [role, output and language rules](../game-task-planning/references/role-contract.md), including direct calls. Resolve approval/selection through the [shared UI decision rules](../game-task-planning/references/ui-adapter.md); preserve exact UI schemas and independent quality gates.
