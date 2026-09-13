---
name: game-task-planning
description: Break an agreed indie-game change into a small dependency-ordered set of specialist tasks and verification checkpoints.
---

## Input/output
Require scope, available specialist contracts and existing artifacts. Produce tasks with owner, input revisions, output, dependencies, acceptance evidence and completion state.
For supervised runs, use the Tasks and Acceptance coverage sections of [the run template](../game-workflow-supervision/assets/run-template.md). Every selected output needs a real template and rules; have its specialist define missing scoped formats before production. Planning must preserve intent and acceptance IDs, identify unresolved decisions blocking implementation, and hand off to the supervisor without dispatching workers itself.
Choose only necessary roles. Missing skills are explicit prerequisites, not names to invent and execute. Small changes need only a short ordered list in the work record. Do not create a feature-sized document set for a local repair.
Assign one writer per shared artifact. Separate test infrastructure from test execution. Identify UI approval stops and resumption inputs. Recompute only affected downstream work when a dependency changes.
Do not rewrite product requirements, decide specialist output, install tools or start parallel agents just because tasks are independent.

Read [the delivery contract](references/delivery-contract.md) when planning execution and completion. Name cross-module test designers, code writers and executors, and the owner of the assembled candidate. For potentially parallel work record write paths, relevant read/verification scope, exclusive resources, input revisions and the join owner. Plan isolation or waiting when a check reads an active writer's inputs; the entry workflow dispatches only when authorized. Planning owns this assignment, not worker execution or specialist implementation.

## Select by owned state or artifact
Check each selected skill's availability and actual inputs. This table covers the implemented programming roles; it does not make every role a required stage.

| Need | Owner |
| --- | --- |
| Evidence-backed implementation approach, data/algorithm design and state/interface/lifecycle contracts | game-technical-design |
| Domain rules and semantic outcomes | game-rule-implementation |
| Device input to commands | game-input-implementation |
| Position and collision response | game-movement-implementation |
| Runtime observation and camera control | game-camera-implementation |
| Session transitions and shared pause | game-session-implementation |
| Resource acquisition, handles and release | game-content-loading |
| Serialization, persistence and migration | game-save-implementation |
| External SDK/service adapter | game-platform-integration |
| Measurements and bottleneck evidence | game-performance-profiling |
| Local build candidate and manifest | game-build-packaging |
| Scenarios and observable expectations | game-test-design |
| Shared harness, fixtures and diagnostic tools | game-test-infrastructure |
| Test execution and functional verdict | game-functional-verification |
| Read-only technical findings | game-code-review |

UI work uses the installed existing UI chain and its approval/coverage contracts. Audio, art, animation, AI, navigation and other specialists must be checked separately; do not assign their production work to the nearest programming role. Do not select build packaging unless a candidate package is part of the requested outcome.

## Required contracts
Apply [role, output, language and independent verification rules](references/role-contract.md) even for direct invocation. Read only your role card and output type.
