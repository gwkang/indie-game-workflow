---
name: game-workflow-audit
description: Audit a selected indie-game workflow event from current run evidence, classify quality and efficiency findings, and propose bounded skill-improvement candidates without editing the product or skills.
---

# Workflow audit

## Role and boundary
Act as a separate read-only auditor for one event selected by the overall `game-workflow-supervision`. Inspect only the actual run slice, dispatched skills, returned artifacts/evidence, and immediately adjacent handoffs named in the dispatch. Do not inventory or review every installed skill, monitor a run continuously, infer hidden agent reasoning, edit product or workflow files, create tasks or gates, or approve completion.

Accept required event audits and optional retrospectives under the supervisor's [event contract](../game-workflow-supervision/references/execution-supervision.md#event-driven-workflow-audit). Findings inform the overall supervisor but do not change acceptance, authority or dispatch by themselves; the supervisor owns event holds and follow-up decisions. Apply the [common role contract](../game-task-planning/references/role-contract.md), read only the `game-workflow-audit@1` role card, and return [`workflow-audit@1`](references/output-contract.md).

## Required dispatch
Require the event ID, required T1–T4 or optional retrospective classification, cause lineage/criteria/input revisions and prior event link if any; expected benefit and budget (cost cannot waive required events); run/task/attempt and candidate identities; exact source locators and revisions; actual consumed skill contracts and adjacent handoffs; exclusions and stop condition. If identities are stale, sources are unavailable, or scope becomes a whole-installation review, return `inconclusive` with the smallest evidence gap, next observation and owner, then stop. A trigger permits observation only. Do not schedule yourself on every dispatch or remain resident between events.

## Audit method
1. Reconstruct the selected path from current run, dispatch, result, artifact, and raw evidence locators. Distinguish the reference target from the produced candidate and mark stale or absent evidence.
2. Compare each producer and consumer only with the contract actually used at that handoff. Check whether the failure came from the product, environment/tooling, evidence/record, execution/handoff, or the skill contract itself. Do not attribute a skill defect merely because the outcome was poor.
3. Classify each supported finding as `confirmed-defect`, `recording-gap`, `operational-risk`, or `efficiency-loss`. Keep evidence strength separate from urgency and authority.
4. For a possible skill-contract cause, test limited-improvement eligibility. Return a proposal only when current evidence identifies the owning skill and boundary, the existing contract cannot adequately prevent or detect the problem, and either one severe failure or a repeated same-cause pattern justifies the added burden.
5. Link each finding to the next changed action, owner and success observation, including product/observation/requirement/execution corrections when no skill candidate is eligible. Return findings, non-findings and limitations within budget. Stop when cause/next action is sufficiently identified or the investigation limit is reached; unresolved observation needs return `inconclusive`, not a fabricated cause or quality PASS.

## Independence and follow-up
The auditor does not implement its proposal. A later authorized skill change needs a separate author and a verifier different from both auditor and author. Follow the [candidate evaluation contract](references/output-contract.md#candidate-evaluation-and-adoption) for scope, protected criteria/evidence, original/held-out/normal behavioral comparison and adoption. Static checks or a forward walkthrough prove only their stated properties, not game quality, production behavior, or measured time savings.

This Markdown role has no persistent process, telemetry, atomic scheduling, or access to internal reasoning. It can observe only preserved prompts/dispatches, files, run records, results, tool outputs and evidence made available to it. Count the auditor against available concurrent-agent slots and stop it when its bounded event review ends.
