# Output and acceptance rules

Before each stage, read its rules below. Exact headers, tables, approvals and recovery routes are binding.

## Tool routing

Use an available image tool only for bitmap generation/editing required by approved direction. Inspect references first; follow tool rights/editing rules.

If existing assets/code-native primitives suffice, record `concept-not-required` and make deterministic production-representative composites only. Do not generate to fill a slot.

## Candidate contract

Produce two distinct artifact types when generation is required:

- **Concept candidate** — retained output bytes used to evaluate visual treatment. Generated text, data, icons, or protected content are illustrative and never source-parity evidence.
- **Production-representative composite** — deterministic composition of approved visual treatment, exact protected bytes, and exact rendered live content. Record the compositor or reproducible procedure, inputs, output dimensions, and hash.

Only a production-representative composite can receive mockup approval or enter downstream evidence.

### Component reuse fidelity

Preserve bound catalog identity/version, protected properties and required states. Vary only approved screen-owned inputs and placement.

Generated appearance may explore surroundings but never proves reuse or replaces, retouches, averages or approximates the canonical component. Helpers, screenshots and visual matches count only when the same-fingerprint catalog declares that evidence capability.

For each candidate packet, emit this block in order:

`Component reuse-fidelity matrix`

`binding | catalog artifact fingerprint | consumer | represented states | allowed instance inputs | protected-property evidence | result`

One row per binding. represented states lists every required state and representation status. protected-property evidence lists each property with a locator or explicit missing/drift status; never summarize untouched/unavailable properties away.

Use only these results:

- `MATCH` — the exact bound identity and fingerprint are current, every required represented state is visible, all protected properties have declared reproducible evidence, and only allowed instance inputs vary.
- `DRIFT` — evidence exists but a protected property, state, identity, fingerprint, or allowed-input boundary differs. Reject that composite.
- `BLOCKED` — required binding, fingerprint, canonical representation, state, evidence capability, or protected-property evidence is absent, stale, or conflicting. Do not claim fidelity or select the composite.

- Build prompts and compositions only from approved inputs; label each reference as composition, style, subject, or edit target.
- Produce exactly the requested candidate count and every target viewport named by the screen specification. Do not infer one target from another.
- Show one identified representative state per image. A candidate does not prove states it does not show.
- Use exact approved copy, symbols, data formats, controls, and protected content. Reject corrupt or substituted content instead of calling it illustrative.
- Preserve approved hierarchy, safe-area intent, responsive regions, and live-content space; record every departure.
- Keep retained concept bytes unchanged. Save deterministic composites separately with stable versioned names; never overwrite an approved reference.
- Record prompt, tool and mode, reference roles, generation identifier when available, dimensions, hashes, transformations, target screen and state, rights, and current/superseded status.
- Follow the supplied attempt budget. If none exists, stop after three failed attempts for one requested candidate and target, recording rejected hashes and the unresolved visual region.

## Output contract

Return one **Mockup candidate packet** containing:

1. concept path or `concept-not-required`, plus production-representative composite paths and previews
2. exact prompt or deterministic composition procedure, with reference roles
3. screen-spec compliance matrix mapping each required region, content family, and represented state to visible evidence
4. component reuse-fidelity matrix for every reusable binding
5. observed defects, rejected candidates, and intentional differences
6. provenance, hashes, and current/superseded status
7. selection record under the shared UI decision rules; include a question only for a remaining required user decision

## Scope boundary

- Do not load a full-screen mockup as a runtime texture or production atlas.
- Do not create production assets, manifests, scene code, layout code, or invisible input regions.
- Do not continue into handoff, asset production, implementation, runtime validation, or approval review.
- Do not create, revise, approve, or version a component catalog from mockup work.
- Do not treat visual similarity, generation success, or the author's preference as approval.

## Verification and approval

- Inspect every retained image at original detail; verify dimensions, hashes, crop safety, text, data, controls, and protected-content parity.
- Reproduce deterministic composites and require identical output hashes.
- Trace every visible requirement to the approved screen specification; there must be no orphan content or controls.
- Keep every candidate `DRAFT` until its exact composite hashes have a resolved selection under the shared UI decision rules.

Missing/stale/conflicting binding, fingerprint, canonical representation, required state, capability or property evidence makes the row BLOCKED. Return to game-ui-component-system before handoff.

Use this exact recovery handoff:

`Next route: game-ui-component-system`
`Blocked downstream: game-ui-handoff`

Stop after the packet. Only production-representative composites selected under the shared UI decision rules enter game-ui-handoff.