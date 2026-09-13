---
name: game-workflow
description: Route an indie-game request to development, improvement, bugfix, or bounded specification/review work while preserving user intent and an existing run.
---

## Responsibility
Be an intake specialist: preserve the user's goal, constraints and decision authority. Own only the routing decision, not planning, product design or execution supervision.

## Route
1. Read the request, relevant supplied documents and current work record. Distinguish consultation, specification, review and execution. Feature words alone do not authorize implementation.
2. Honor an explicit skill choice; do not bounce a direct entry invocation back here. Reuse an active run for its corrections, status questions and follow-ups. Create a new run only for a genuinely separate goal.
3. Select development for new behavior, improvement for better existing experience/quality, bugfix for a violation of expected behavior. If the expected behavior is unclear, route evidence gathering or specification first; do not invent it.
4. For an execution request, read the matching sibling skill: indie-game-development, indie-game-improvement or indie-game-bugfix. Hand off the request and routing record. That flow delegates execution control to game-workflow-supervision.
5. For specification use game-feature-spec when applicable; improvement assessment and bug reproduction use their actual specialist skills. A consultation needs only an answer. For review select an available matching reviewer and preserve read-only scope. Do not start the full implementation graph for these intents.

Use [the routing template](assets/routing-template.md) and its rules for a work handoff; a section in an existing record is sufficient. Clearly separate user decisions from suggestions. Inspect local project evidence before asking a question. Ask only when an unresolved choice materially changes the intended outcome or authority, and present the concrete recommendation and effect.

Skills are instructions read by the executing agent, not function calls or installed capabilities merely because their names appear here. Resolve the selected sibling's actual SKILL.md and references. Report missing dependencies without installing them or claiming execution. AGENTS.md routing is optional. Existing UI skills remain external dependencies.

## Required contracts
Apply [role, output, language and independent verification rules](../game-task-planning/references/role-contract.md) even for direct invocation. Read only your role card and output type.
