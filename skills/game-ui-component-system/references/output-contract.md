# Output and acceptance rules

Before each stage, read its rules below. Exact headers, tables, approvals and recovery routes are binding.

## Decision rule

Classify every repeated family as exactly one of:

| Decision | Use when |
|---|---|
| `reuse:<componentId>@<version>` | An approved entry covers the consumer, state, adapter, and evidence capability. |
| `screen-specific-exception` | Current authority requires a deliberate non-shared expression and records its scope. |
| `new-family-required` | No approved entry covers the requested structure or protected appearance. |
| `BLOCKED` | Authority, capability, compatibility, or approval evidence is missing or conflicting. |

Similarity, majority usage, averaged values, shared primitives or partial evidence never establish reuse.

## Output contract

Produce one concise **Component catalog decision** containing:

1. **Authority ledger** — current, supporting, superseded, conflicting, `OPEN`, and `BLOCKED` sources.
2. **Family inventory** — proposed stable ID, semantic version, representation kind, variants, consumers, and exceptions.
3. **Contract** — structure, allowed instance inputs, protected properties, states, and accessibility invariants.
4. **Adapter binding** — the project-declared implementation adapter and fallback owner.
5. **Evidence map** — declared capabilities, protected-property coverage, landmarks or probes, and project-owned tolerances.
6. **Compatibility** — covered presentation roles, consumers, and explicit incompatibilities.
7. **Decision and approval** — one classification per family plus the exact artifact fingerprint and approval status.
8. **Next route** — the smallest upstream decision or downstream owner allowed to proceed.

Use [the catalog schema](component-catalog.schema.json) for machine-readable catalogs. Run `scripts/validate_component_catalog.py CATALOG.json PROFILE.json` to check profile, evidence coverage, identity and approval invariants across fields.

## Scope boundary

- Do not design screen composition, invent product content, measure an unapproved reference, produce assets, or implement runtime components.
- Do not convert a conflicting family into a new standard by averaging values.
- Do not approve the catalog you authored or treat approval of one version as approval of another.
- Do not claim visual fidelity from evidence that fails to cover every protected property and required state.

## Verification and stop conditions

Require source-ledger traceability for each value, an evidence capability for every protected property and approval matching the exact catalog fingerprint. Missing required authority/capability/compatibility/approval blocks implementation. After approval, route measurements to handoff, applicable representation readiness to asset production, integration to implementation, and observed drift to runtime validation/independent acceptance.

## Common mistakes

- A shared low-level helper is not an approved component family.
- A new label or callback may be an allowed input; a new material treatment is a protected-property change.
- Lack of raster evidence does not block a project whose declared hierarchy, vector, command-trace, or native evidence covers the contract.
