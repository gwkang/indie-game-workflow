# Project profile

Revision: <revision>. Keep only applicable rows, translate prose into the artifact language, and retain machine keys. Values are current unless marked unknown, conflicting or proposed.

| Setting | Value | Source |
| --- | --- | --- |
| Engine/version; 2D/3D | | |
| Platform | | |
| Display/input | Value or exact existing settings reference | |
| Game locale | | |
| communication.preferredLanguage | ko unless explicitly overridden | User preference or workflow default |
| communication.artifactLanguage | Omit unless different from preferredLanguage | |
| workflowRunRegistryPath | Exact project-relative path when stateful workflow reuse is supported | |
| modelRoutingProfilePath | Optional explicit project override; bundled common model/effort mapping is automatically used when omitted | |
| workflow.requirementsPath | Exact required preparation manifest; default planning/workflow-requirements.json | [Required preparations](../../game-workflow-supervision/references/mandatory.md) |
| workflow.roadmapPath | Required development list; preserve unknown scope | |
| workflow.smallChangePolicyPath | Omit for the common bounded default; exact plain relative path for an explicit project override | Project authority |
| workflow.stateToolPath | Omit for the installed native tool on new supervised runs; exact plain relative path for an explicit project tool | Existing run sources are preserved |

Consume actual `workflowDefaults` from the preparation check, then apply the resolved [small-change contract](../../game-task-planning/references/small-change.md) only to eligible settled work. Missing/invalid explicit selections block. Keep the three machine-key override values as exact plain relative paths, without links or descriptions in the value cell. The common defaults do not grant product, tool installation, commit or publication authority.

## Required knowledge settings

During authorized workflow setup, record `knowledge.enabled`, stable `knowledge.projectName`, `knowledge.root` (`<project-name>-wiki/`), `knowledge.indexPath` and `knowledge.policyPath`. Keep exact project-relative locators here; source authority, write policy and checks stay in the referenced project policy. Missing integration is required preparation. Set enabled=true and connect source-backed content. Follow the [knowledge contract](../../game-task-planning/references/knowledge-contract.md); do not migrate an existing wiki while collecting settings.

## Commands

Working directory: <path>. State whether definitions were inspected or execution tested; keep logs elsewhere.

| Purpose | Command |
| --- | --- |
| Run / build / relevant checks | | |

## References

Link existing product criteria, UI settings and workflow policy as needed. Do not copy their rules. Add only unresolved settings that affect upcoming work; omit this section if there are none. Keep source hashes, reviewer identity and detailed results in the existing handoff, not this settings table.
