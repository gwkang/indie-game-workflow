---
name: game-code-review
description: Review game-code changes against an agreed contract and current evidence without editing the implementation.
---

## Input/output
Use request, changed source, relevant callers and verification results. Output actionable findings with location, trigger, consequence, severity and repair owner; otherwise state the reviewed scope and limits.
Prioritize state ownership, duplicate rewards/events, lifetime/cancellation, save compatibility, boundary handling and real regression risks. Do not request speculative refactoring unrelated to the change.
Read callers and tests before asserting a defect. Distinguish inspected facts, execution evidence and inference. If authored by the same reviewer, label it self-review; do not claim independent approval.
Do not patch code, edit tests to pass, or declare rendered/art quality from code. Return concrete findings to implementation and require evidence against the final candidate.

Check the assembled change and cross-module tests when multiple owners contributed. Apply the project's review policy using [the delivery contract's review and final-candidate sections](../game-task-planning/references/delivery-contract.md). Review changed callers, existing conventions and maintainability consequences relevant to the request; do not impose a new pattern merely for stylistic consistency. Runtime parallel changes also need scrutiny of the declared data ownership, execution thread and cancellation/shutdown behavior.

## Required contracts
Apply [role, output, language and independent verification rules](../game-task-planning/references/role-contract.md) even for direct invocation. Read only your role card and output type.
