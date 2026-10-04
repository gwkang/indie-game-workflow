# Execution evidence for bounded changes

Use this reference when a selected project policy uses a common native runner or structured completion adapter. The project owns the runner, result schema, supported engine, entrypoints, commands, timeouts and exact locators. This contract does not install a runner, require a particular engine or replace functional/UI acceptance.

## Reproducible execution

Run from the frozen candidate's declared working directory, with an explicitly resolved executable and entrypoint. Verify the entrypoint belongs to that candidate and freeze the configuration, source, tests and fixtures it reads; do not combine an original checkout's tests with candidate source accidentally. Record the actual cwd, command, relevant environment, executable identity, exit status and elapsed time. An executable or input change invalidates affected execution evidence.

Use an explicit text encoding for the runner and child processes where output decoding affects validation. Select finite positive timeouts by operation and project observations. A timeout is an upper bound, not a required wait or performance target. Preserve partial stdout/stderr for timeout and abnormal exit; neither is PASS. Freeze the runner/adapter identity as well as the inputs when reusing results.

## Structured completion

The adapter checks the declared schema and supported version by exact type and value. For an integer version, booleans, strings and fractional numbers are not equivalent. Validate suite IDs, completed names, counts and failure counts against observed output and the expected scope. Reject zero work, missing or duplicated suites/names/completion markers, failure-mixed success, incomplete output, malformed JSON and inconsistent counts. Exit zero alone is insufficient.

If a project retains a historical text adapter, select one format for each execution; do not combine old and structured summaries to manufacture completion. Tests must show that the adapter accepts a genuine success and rejects applicable malformed, truncated, duplicated, wrong-type and failed observations. These adapter checks prove evidence handling, not the product behavior asserted by test expectations.

## Attempts and ownership

Allocate a fresh raw directory using run ID, candidate identity, attempt/check identity and a collision-resistant suffix. Create raw files exclusively; a reused attempt number in another record must not overwrite evidence. Link reports to the paths actually saved. Preserve failed attempts and the shared failure lineage instead of replacing them with the latest success.

Keep one sequential writer per evidence record. Independent parallel executions use separate records and output directories, with source-read isolation still required. Refresh the affected independent review when the candidate or consumed evidence changes; an appended check cannot inherit an earlier conclusion automatically.

Run focused checks while preparing or repairing a candidate, then the required final suite on stable inputs. Reuse unaffected observations only with explicit input/runner/environment comparisons and adapter revalidation when its interpretation changed. Record a reused engine execution separately from a new parse or a new engine run. Command durations and stage spans do not establish end-to-end time savings, device validation or release readiness.
