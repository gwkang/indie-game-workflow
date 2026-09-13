# Execution supervision

Apply [bounded artifact verification](../../game-task-planning/references/verification-scope.md) to each selected output. Freeze its criteria and repair scope before dispatch; carry the same contract into every retry and UI handoff. Out-of-scope findings are deferred observations, never automatic tasks or new gates.

## Preparation and ownership
Use the run template; the overall supervisor alone edits the shared record. Workers return results using its result envelope. Resolve request intent before executing. Require a template and rules for each selected output: reuse the producing skill's existing format; if absent, have its owner define a scoped format and content checks before production. Do not label all bundle outputs standardized merely because this envelope exists.

For a small workflow supervise directly. Introduce a part supervisor only for a useful independent group with clear input/output and internal coordination. Default to overall plus one part level; count actual supervisors against available slots. Programming supervision watches interfaces, state ownership and integration risk; UI supervision watches selected references, coverage and asset/runtime readiness. Neither can overrule specialist verdicts or alter another part's scope. Refer cross-part conflicts to overall supervision and technical/product owners.

## Questions and part reassignment
Specialists return observations, decision sources, recommended options and blocked criteria internally. The overall supervisor resolves existing/delegated choices and sends only remaining material questions together; direct specialist calls follow the common question route.

Use the run template's supervisor assignment table. To add/remove/reassign a part: identify affected tasks and current owner → stop dispatch for those tasks → confirm active affected workers stopped → record new plan revision, task/read/write/resource boundary and shared remaining retry budget → retire the old assignment → activate the new assignment once. If stop/ownership is uncertain, block affected dispatch. Transfer result locators; retain results only when input/criterion revisions and independence remain valid. Preserve independent branches. Adding a supervisor never resets retry counts or changes product scope. This is a single-writer procedure, not atomic ownership or crash recovery.

For UI decisions apply [the UI adapter](../../game-task-planning/references/ui-adapter.md); delegate selection and actual PO approval are distinct records.

## Readiness and result acceptance
A task is ready only if selected, predecessors' required results passed, current required inputs exist and are semantically usable, material decisions are settled/delegated-and-decided, authority/tools exist, resources are available and no active attempt owns the scope. A skipped branch needs a reason and must not hide an unmet requirement.

Before a dispatch record its ID and attempt, actual skill path, input revisions, write/read scopes, resources and result location. After spawning record the actual executor ID. Missing creation acknowledgement means uncertain dispatch, not permission to spawn a duplicate. Inspect available host state or block/isolate the affected scope. This Markdown procedure is not atomic dispatch.

On return inspect artifacts and observations, not only prose. Match run/task/attempt and consumed revisions. Record execution state separately from verdict: a verifier can complete its checks and return fail. Reject late or stale results as evidence for the current candidate. Require a result envelope even for failures. Missing content returns to its owner.

## Failure, repair and restart
Distinguish product failure, incorrect/missing input, and environment/tool blockage. Route product failure to its implementation/diagnosis owner, expectation ambiguity to specification, harness failure to test infrastructure. Verifiers do not fix product code to pass. Default repair limit is two attempts per failing task unless a known project policy supplies another value; record the limit before execution. Meaningfully change the hypothesis/input on retry; do not restart a new task to evade the limit.

Before reassigning a scope, confirm the old worker stopped. On input changes revise the plan and invalidate affected evidence. Preserve completed independent work. On resumption inspect current files, active workers and input versions before continuing. Never infer termination from silence. Preserve partial writes and user changes; do not blindly reset shared files.

## Integration and completion
Assign an implementation owner for integration code; the supervisor's join is a control operation. Freeze or isolate the assembled candidate before checks. Link every in-scope acceptance criterion to artifacts and current verification; all-success tasks with uncovered criteria are not complete. Run required project gates and independent reviews, plus actual UI acceptance where selected. After repairs rerun affected checks and reviews on the new candidate within the frozen verification contract. Preserve unaffected valid evidence; passing scoped criteria end the loop.

Use the final-report section to distinguish complete, partially complete, blocked and failed, with actual evidence and remaining work. No generic final permission is needed when all authorized work and required decisions are satisfied. Out-of-scope publication stays separate.
