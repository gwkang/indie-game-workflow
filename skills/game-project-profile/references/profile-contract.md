# Target resolution and UI projection

Resolve communication and artifact language using [the language contract](artifact-language.md), separately from target/game locales. communication.preferredLanguage supplies the default; communication.artifactLanguage is an optional artifact-only override. Preserve source/status and avoid injecting workflow language fields into existing UI schemas.

Resolve within a domain: explicit authorized work value, target value, referenced default group. Merge nested objects by field and replace explicitly supplied lists. Omission inherits; none means explicitly unused. Unknown or conflicting required values block only dependent work. Screen UI cannot inherit world camera or physics. Asset and spatial groups defining the same field are a conflict, not last-writer-wins.

For existing UI skills, prefer a reference to the approved UI JSON profile. If creating a projection, provide artifactFingerprint, supportedKinds, adapters, evidenceCapabilities, authorityRefs, approvalAuthorities and fallbackOwners. These lists contain actual declared IDs, not inferred engine features. Keep source revision and field provenance in a companion ledger. Do not approve the projection or catalog merely because fields are present.

Preserve the project's fingerprint convention. For a new convention, hash UTF-8 JSON with sorted keys and compact separators excluding artifactFingerprint. Require the catalog profileFingerprint to match. Validate with the selected UI catalog validator and report unresolved adapters or evidence capabilities. A changed projection reopens dependent approvals.
