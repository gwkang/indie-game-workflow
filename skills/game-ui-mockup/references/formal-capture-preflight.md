# Formal capture preflight

Use this preflight immediately before formal production-representative composition. It reduces wasted renderer runs without weakening the formal candidate contract.

## Phase 0: contract lint

Check without starting the renderer:

- approved direction, screen-spec, catalog and component fingerprints exist and match the current source locks;
- every required binding has a current consumer, allowed inputs, protected properties and declared evidence capability;
- the requested candidate count, target viewports, safe areas, coverage IDs, fixtures and text-fit cases are closed;
- protected content and provenance paths resolve inside the declared write scope.

Any missing, stale or conflicting input is `OPEN` or `BLOCKED`; do not substitute a placeholder or launch a formal capture.

## Phase 1: bounded smoke capture

Run the same compositor and renderer path against only a small, non-retained smoke set covering the highest-risk viewport, one state transition or dialog, and one dense content state. Check process exit, draw/readback availability, dimensions, crop safety and one repeated output hash. Do not count smoke images toward formal coverage or approval, and discard them or mark them explicitly as non-evidence.

If the environment cannot produce a stable smoke result, route the issue to test infrastructure and stop before formal composition. Do not spend formal repair attempts on an environment failure.

## Phase 2: formal batch

After the smoke gate passes, run the formal compositor once where the tool supports batching, producing exactly the requested candidate count and every named viewport/state. Keep the formal packet and its hashes separate from smoke outputs. The formal verifier still inspects every retained image and requires deterministic reproduction; the preflight never replaces that review.

Record the preflight input revision, renderer identity, smoke result, elapsed budget and the reason formal capture was allowed or blocked. A preflight failure is not a product or visual-quality verdict.
