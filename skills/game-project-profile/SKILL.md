---
name: game-project-profile
description: Create or update an indie-game project profile from current project evidence without changing engine settings or product code.
---

## Inputs and output
Read existing equivalent profiles first. Own the project profile and source ledger only. Use assets/profile-template.md for a new profile; omit unrelated fields.

## Procedure
Inspect project documents, engine/config files and available tools. Record current facts separately from requested targets; give relevant fields a source and confirmed, unknown or conflicting status. Do not infer 2D physics from an orthographic camera.
Resolve target settings within their declared domain: explicit work override, target values, referenced defaults. Screen UI never inherits world camera/physics. Asset groups supply asset fields, not competing spatial defaults. Missing required IDs or conflicting fields need clarification; continue unaffected work.
Follow references/profile-contract.md for inheritance and existing UI profile projection. Reuse an approved UI profile when available. Profile confirmation is not artifact approval.
Validate required references and actual commands before claiming runnable configuration. Save only profile artifacts; installing engines, changing code, converting assets and installing skills are separate actions.

## Required contracts
Apply [role, output, language and independent verification rules](../game-task-planning/references/role-contract.md) even for direct invocation. Read only your role card and output type.
