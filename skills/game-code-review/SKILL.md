---
name: game-code-review
description: Review game-code changes against an agreed contract and current evidence without editing the implementation.
---

## Input/output
Use request, changed source, relevant callers and verification results. Output actionable findings with location, trigger, consequence, severity and repair owner; otherwise state the reviewed scope and limits.
Prioritize state ownership, duplicate rewards/events, lifetime/cancellation, save compatibility, boundary handling and real regression risks. Do not request speculative refactoring unrelated to the change.
Read callers and tests before asserting a defect. Distinguish inspected facts, execution evidence and inference. If authored by the same reviewer, label it self-review; do not claim independent approval.
Do not patch code, edit tests to pass, or declare rendered/art quality from code. Return concrete findings to implementation and require evidence against the final candidate.

Apply the [shared coding decisions](../game-task-planning/references/delivery-contract.md#implementation-completion) to changed code: identify concrete invariant bypasses, responsibility/dependency coupling or avoidable cost. Report their trigger and impact; missing pattern names or unrelated cleanup are not findings.

When the change has a technical-design revision, check the changed callers and consumers against its responsibility, state-owner, interface, lifecycle and provisional-structure boundaries. Treat an undocumented expansion of provisional code, or its promotion into a shared baseline without recorded criteria, as a finding only when you can name the concrete ownership, invariant, lifecycle or change-risk consequence. Return missing or conflicting architecture to `game-technical-design`; do not prescribe a speculative refactor from review.

Check the assembled change and cross-module tests when multiple owners contributed. Apply the project's review policy using [the delivery contract's review and final-candidate sections](../game-task-planning/references/delivery-contract.md). Review changed callers, existing conventions and maintainability consequences relevant to the request; do not impose a new pattern merely for stylistic consistency. Runtime parallel changes also need scrutiny of the declared data ownership, execution thread and cancellation/shutdown behavior.

Before judging, apply [current-state and prior-record review](../game-task-planning/references/verification-scope.md#review-the-current-state-before-alleging-a-defect): inspect relevant implementation and available wiki/decision/review records, check counterevidence, and report no findings when warranted. Do not expand scope or manufacture defects.

For changed Lua or Python code, read the relevant [language coding guidance](../game-task-planning/references/language-coding.md). Apply it to implementation, callers and test expectations within the assigned scope; unsupported-version assumptions, style preferences and intentional sharing are not automatic findings.

## Review sequence
1. Fix the request, acceptance criteria, candidate identity and assigned scope before judging. Read the agreed design and relevant prior decisions; an author summary or passing CI is context, not proof.
2. Read every assigned handwritten change, including deletions, configuration and tests, in a logical caller-to-effect order. Inspect surrounding code and affected consumers as needed. Declare sampled/generated portions and unread scope; do not grant full approval over unreviewed code.
3. Trace the changed behavior through valid inputs, boundary inputs and failure paths. Use the change-driven risk prompts below, not a mandatory whole-project checklist.
4. Read test expectations and fixtures, not just test results. Check that assertions express the required behavior, exercise the affected path and would fail for the relevant defect; mocks must not hide the integration boundary being claimed. Test count and coverage percentage alone do not prove correctness. Missing tests alone are not a finding without a scoped requirement or a concrete uncovered risk.
5. Check counterevidence before reporting: caller guards, supported configurations, engine/API guarantees, tests and accepted decisions. Unclear requirements or missing specialist expertise return to their owner with the affected criterion marked inconclusive; do not guess a defect or approve that criterion.
6. Return supported findings and reviewed limits. After repairs, check the affected evidence against the new candidate under the shared delivery contract; old approval does not automatically transfer.

## Change-driven risk prompts
Select only prompts implicated by the change and existing requirements; these do not authorize new product rules, broad security audits or performance gates.
- **Rules and boundaries:** empty/zero/maximum values, ordering, repeated commands and re-entry; keep rewards, costs and RNG effects consistent with the specified invariant.
- **Failure and persistence:** partial failure, retries, fallback and recovery must preserve the agreed state; inspect schema/default/migration compatibility when save data changes. A swallowed error or optimistic success must not conceal a failed required operation.
- **Lifetime and concurrency:** initialization/teardown, subscription cleanup, late callbacks, cancellation and shared-handle ownership; inspect thread affinity and data access when execution boundaries change. Async syntax alone is not evidence of safe concurrency.
- **Trust boundaries:** when changed code consumes external/untrusted data or handles credentials, check validation, authorization, secret disclosure in logs and dependency/API assumptions against the supported environment. Never reproduce secrets in findings.
- **Cost and clarity:** inspect allocations, repeated work and blocking I/O in affected hot paths. Ground performance claims in workload or measurements; require clearer naming/comments/docs only for concrete misunderstanding or contract drift, not personal taste. Let existing automation handle routine formatting.

## Finding priority and communication
Use the project's severity scale when defined. Otherwise use this fallback consistently:
- P0: immediate critical loss or exposure under supported operation; urgent containment required.
- P1: major broken behavior, data loss or security impact on a supported path; repair urgently.
- P2: a concrete correctness, compatibility or maintainability defect with a bounded trigger; normal repair priority.
- P3: a concrete low-impact defect; lower priority. Personal preferences are not P3 findings.
State impact and trigger separately from evidence confidence; a hypothetical scenario is not automatically P0/P1. Severity alone does not invent an acceptance gate: use existing scoped requirements and review policy.

Write about the code, not the author. Explain the violated requirement and consequence with the smallest useful location/trace. Separate required corrections from optional suggestions or clarification questions; optional advice does not block acceptance. Do not prescribe a specific refactor when several valid repairs exist. With no supported findings, report that result, candidate, reviewed coverage and limitations; do not equate no findings with runtime or visual acceptance.

These refinements are grounded in [Google review guidance](https://google.github.io/eng-practices/review/reviewer/looking-for.html), [comment guidance](https://google.github.io/eng-practices/review/reviewer/comments.html) and [Microsoft reviewer guidance](https://microsoft.github.io/code-with-engineering-playbook/code-reviews/process-guidance/reviewer-guidance/). Source adoption and project-specific evidence belong in the project run/wiki, not this portable skill.

## Required contracts
Apply [role, output, language and independent verification rules](../game-task-planning/references/role-contract.md) even for direct invocation. Read only your role card and output type.
