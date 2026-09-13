# Bounded artifact verification

Apply to every selected output: profile, specification, design, plan, code, asset, build, measurement, review and final report. Direct invocation also applies. Reuse an existing verification record; a small output may use a short checklist in its handoff. The verifier must be a separate subagent from the artifact producer. Author self-checks are preparation, never the required verification; switching roles in one agent does not satisfy independence. One independent verifier may check several compatible outputs without spawning an agent for every file. If no separate subagent is available, keep verification blocked rather than substituting self-review. Verification reports are checked for scope, identity and evidence at supervisor join; they do not recursively create verifier-of-verifier tasks. This control check does not replace independent verification of production artifacts, including authored review deliverables.

## Freeze the verification contract before checking

Record these fields in the run template's Artifact verification section or inline with the same fields:
- Artifact ID/location and revision; producer and separate verifier executor IDs (they must differ).
- Scope source: authorized request and applicable existing project/role requirements.
- Included criteria IDs, observable pass conditions and excluded concerns.
- Necessary read dependencies, permitted repair paths/resources, checks and evidence required at this stage.
- Repair owner, retry budget and current attempt. Use the existing supervisor limit; for direct invocation default to two repair attempts.

Every selected artifact needs appropriate content/semantic and format checks; field presence alone is insufficient. Use the smallest checks sufficient for its criteria. Read dependencies only as necessary to judge those criteria: permission to inspect a caller does not make it another repair target. A broad project-required gate must be identified up front; its execution does not authorize fixing every failure it reports. Do not add quality dimensions, new platforms, redesign, cleanup, benchmarks or new acceptance criteria during review merely because they would be useful. Do not silently drop an applicable mandatory gate to make the scope smaller.

If the intended check cannot answer a frozen criterion, correct that check within the same criterion and record why. Changing the product expectation or adding a criterion is a scope change, not a test correction.

## Classify findings and close the scoped loop

1. Bind each failure to an included criterion and current artifact evidence. Return it to the artifact's repair owner; a verifier does not silently edit the artifact it judges. The producer repairs and the separate verifier rechecks; record both executor IDs on every attempt. A replacement verifier must also be independent of the producer.
2. Repair only that defect within the permitted scope. Recheck the failed criterion and predeclared checks affected by the repair. Preserve passing evidence whose inputs remain valid. Do not restart every stage or add unrelated tests after each failure.
3. Repeat until scoped criteria pass, the recorded budget is exhausted, or a genuine blocker prevents the next attempt. Never change expected results to hide a failure, reset attempt counts through a new task, or keep cycling without a changed hypothesis. On exhaustion return blocked with evidence and the smallest unresolved decision; continue independent authorized work.
4. An out-of-scope observation is a separate deferred record, not a failed scoped criterion, automatic task, repair or mandatory gate. Record location, observation and why it is outside scope without investigating it further. It does not block this artifact unless evidence shows an existing included criterion or mandatory gate actually cannot pass.
5. If satisfying an included criterion requires a change outside the permitted scope, mark that criterion blocked. Present the concrete dependency, minimum proposed scope change and impact to the scope owner. Only explicit user authorization can enlarge the authorized request; supervisors cannot invent it. While waiting, do not perform the extra work. This exception is not permission to expand validation.

The supervisor preserves the frozen contract across reassignment and retries. Report artifact pass/fail/inconclusive separately from execution completion and project-wide gate status. Once required scoped checks pass on valid inputs, finish; optional improvement observations do not start a new cycle.

## Existing UI dependency handoff

The workflow planner/supervisor supplies this contract alongside the original UI templates, selected screens/states/targets and existing approval rules. Preserve those schemas and independent acceptance requirements. A finding on an unselected screen is deferred; a shared component defect affecting a selected criterion returns to its existing repair owner within the assigned component scope. If that scope is insufficient, use the blocked path above. This wrapper does not claim to govern standalone UI calls outside this workflow.
