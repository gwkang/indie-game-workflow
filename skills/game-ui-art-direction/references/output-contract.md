# Output and acceptance rules

Before each stage, read its rules below. Exact headers, tables, approvals and recovery routes are binding.

## Authority order

Resolve conflicts in this order and record the result:

1. current user decisions that explicitly revise earlier direction
2. authoritative product and design requirements
3. current approved screen-specific direction
4. shared visual language from current canonical references
5. runtime implementation, used only to inventory the present state and defects

References may supply visual language without prescribing layout/content. Exclude superseded sources.

## Output contract

Return one concise **Art-direction brief** with these slots, in order:

1. **Authority ledger** — current, supporting, superseded, `OPEN`, and `BLOCKED` sources.
2. **Visual thesis** — the intended player impression in one sentence, or `BLOCKED` when authority is insufficient.
3. **Shared visual language** — palette roles, materials, contour, lighting, typography, icons, and depth supported by current sources.
4. **Component-family decisions** — for every repeated visible family, record exactly `reuse:<componentId>@<version>`, `screen-specific-exception`, `new-family-required`, or `BLOCKED`, with its authority. Similarity alone never establishes reuse.
5. **Screen-specific expression** — qualitative hierarchy, mood, density, and distinction.
6. **Protected invariants** — supplied content, data, navigation, interaction, font, accessibility, and gameplay facts.
7. **Anti-goals** — concrete inconsistent or unreadable outcomes.
8. **Open decisions and handoff** — unresolved decisions and the exact inputs needed by `game-ui-component-system`, `game-ui-screen-spec`, and `game-ui-mockup`. When visual or motion choice is unresolved, first record matching [sample-library](sample-library.md) IDs, versions, source fingerprints, preview selectors, fit and limits. If none fit, record searched IDs and the missing capability before a minimal project-local comparison addition. Preserve selected, rejected and unresolved choices separately; a library-ready sample is not approval.

## Scope boundary

- Exploratory style frames and playable motion samples may use an appropriate image, vector or code-native tool when a choice is unresolved. They are comparison evidence, not production assets, component templates, runtime layout or product implementation.
- Invent no copy/data/controls/states/fonts/navigation/accessibility; specify no pixel geometry, asset manifests, test matrices or runtime verdicts.
- Classify family needs and route to game-ui-component-system; do not create/revise/approve catalogs.
- Stop at this brief; do not perform mockup, asset production, implementation or runtime validation in the same response.

## Verification and approval

- Confirm every cited source exists or is explicitly marked `OPEN` or `BLOCKED`.
- Confirm every output slot is present and each factual statement traces to a listed authority.
- For a cited playable sample, inspect its intended viewport, exact selector, relevant states and reduced-motion behavior. Confirm no component catalog/template, final-screen mockup or product artifact was produced.
- Keep the brief `DRAFT` until its decision is resolved under the shared UI decision rules. Cite applicable approval reuse or authorized delegation; superseded references and author preference are not approval.

Stop at the draft. Route new-family-required/BLOCKED families to game-ui-component-system before reuse claims. If authority cannot support the visual thesis, request only the necessary product decision/source.
