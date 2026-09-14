# Output and acceptance rules

Before each stage, read its rules below. Exact headers, tables, approvals and recovery routes are binding.

## Component runtime integration contract

Emit the exact undecorated plain-text title once, immediately before its header:

`Component runtime integration matrix`

Use the exact header once, without outer pipes:

`binding | catalog artifact fingerprint | consumer | implementation target | declared adapter | allowed instance inputs | protected-property evidence | required states | implementation evidence | integration status`

Use ten-cell rows. Copy the approved handoff matrix's first eight cells verbatim, preserving reuse: prefixes, identifiers and list order; add no notes. Cell 9 maps project-declared tests/probes/capabilities to implementation evidence; cell 10 is READY/OPEN/BLOCKED only.

- `READY` means the consumer uses the exact declared adapter for the same catalog identity and fingerprint, passes only the allowed instance inputs, preserves every protected property, maps all required states one-to-one, and has passing current evidence from the focused tests or scoped observations selected under the Implementation contract. This is integration readiness, not rendered-fidelity acceptance.
- `OPEN` is only an optional internal implementation choice that cannot alter identity, adapter, inputs, protected properties, states, or behavior.
- `BLOCKED` covers an added or undeclared input, any protected-property override, a substituted or renamed helper, a missing state or probe, a stale fingerprint, or evidence that does not map to the declared catalog capability.

Pass only approved instance inputs across the screen/component boundary. Generic style/theme/skin/tint/scale escape props cannot change protected properties unless explicitly allowed. Pointer handlers cannot simulate missing component states. Dimensions, unrelated tests, similar names or appearance do not prove adapter/fingerprint identity.

Map each protected property/state to project-declared tests, probes or capabilities. This proves wiring; game-ui-runtime-validation owns pixel fidelity.

If implementation would change a binding, representation, declared adapter, allowed input, protected property, required state, or catalog fingerprint, emit these lines exactly once:

`Next route: game-ui-component-system`

`Blocked downstream: game-ui-runtime-validation`

Missing/stale/conflicting/non-READY handoff → `Next route: game-ui-handoff`. Missing/blocked disposition, binding or packet readiness → `Next route: game-ui-asset-production`. Both retain `Blocked downstream: game-ui-runtime-validation`.

## Implementation contract

Inspect repository impacts and preserve unrelated changes using project-provided tools. Match verification to the scoped regression risk:

1. Reuse an adequate focused test or observation; add a test only when a behavior, input, state or responsive boundary lacks meaningful regression coverage.
2. For a defect, observe the pre-change failure when reproducible. Record unavailable RED evidence honestly; never invent it or build a harness just to fill the packet.
3. Implement the smallest complete change. For a small static layout edit, existing target-size before/after captures and scoped runtime observation may suffice; do not duplicate coordinate literals in tests merely to obtain RED/GREEN.
4. Recheck affected criteria on the current candidate. Preserve valid unaffected evidence and existing mandatory project gates. Runtime fidelity still belongs to runtime validation; independent verification is not waived.

Keep public operations invariant-safe; expose no mutable internals or hidden globals that bypass ownership/inputs. Separate layout, live-data binding and effects where responsibility becomes clearer. Reuse adapters; avoid speculative inheritance/interfaces or unrelated per-frame work.

Map every component and state to its asset, layout owner, live text/data owner, input owner, states, and fallback. Keep dynamic values live. Use declared intrinsic/visible geometry, anchors, safe areas, and fit modes. A mockup or screenshot is never a runtime hit surface.

For changed subscriptions, timers/tweens or async requests, name start/stop owners. On close, release unused subscriptions/timers and cancel obsolete requests where supported. Apply responses only to their current screen instance/request; reopening must not duplicate handlers or let old results overwrite newer state. Release unused results through their owner without cancelling shared work other consumers need. Reuse adapter cleanup; return unclear ownership to the existing session/loading/technical owner, not a new lifecycle framework.

Do not change approved copy, content, currency, font, navigation, Back behavior, persistence, availability, or state rules to simplify implementation. Do not use runtime tint, outline, scale, glow, or spacing to conceal missing or mismatched production art.

## Output contract

Maintain an **implementation evidence packet** with:

1. input lock, hashes, approvals, parity records, supported targets, and exclusions
2. impact map, consumers, shared files, and preserved changes
3. Component integration map containing the Component runtime integration matrix, plus asset/frame, layout, live content, input rectangle, and fallback ownership; for changed subscriptions, timers or requests, link start/stop owners and cancellation/late-response rules here without changing matrix columns
4. verification choice and regression boundary; pre-change failure/evidence when applicable, otherwise an explicit reason RED is unavailable or not applicable
5. implementation result: minimal code path and current focused test or scoped observation evidence; do not label an unexecuted test GREEN
6. contract preservation before/after for product-owned content and behavior
7. deviation ledger: zero deviations or exact source, reason, measured effect, owner decision, and approval
8. changed files, tests, purposes, and commands
9. open decisions and locked build inputs for `game-ui-runtime-validation`

## Scope and verification

- Do not generate, repair, or compensate for art; return art defects to `game-ui-asset-production`.
- Do not invent missing geometry, responsive behavior, states, or product facts.
- Execute the focused tests or scoped observations selected for affected layout, content binding, states, input geometry, navigation, persistence and approved boundaries; do not add unrelated checks. Use meaningful regression tests for changed behavior when required by the selected risk and project policy.
- For the subscriptions, timers or requests changed by this task, select relevant close/reopen, interrupted-request or late-response cases within the existing regression boundary. Check duplicate actions and stale updates; reuse valid adapter evidence where it covers the change. Static position/color edits do not trigger these cases. Return failures to the author and have the separate verifier recheck only affected criteria.
- Confirm every handoff row has a runtime consumer and no extra UI or behavior was introduced.
- Run project-required test/build/audit commands, but do not claim rendered fidelity before runtime validation.

Missing approval, parity, measurements, states, assets or product authority blocks work; so does an out-of-scope contract change. After selected checks pass on current evidence, send the unchanged build to runtime validation. Observations are neither unexecuted test results nor final visual acceptance.