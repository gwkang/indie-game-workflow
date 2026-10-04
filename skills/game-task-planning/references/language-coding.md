# Language coding guidance

Use this reference only when implementing or reviewing changed Lua or Python code. Determine the supported interpreter/runtime, dependency/API versions and repository conventions from actual configuration or runtime evidence; the newest documentation is not the project's compatibility contract. Keep exact host versions and commands in the project profile/run, not portable skills.

- Changed Lua code: read [Lua guidance](code-quality-lua.md).
- Changed Python code: read [Python guidance](code-quality-python.md).
- Mixed-language changes: read both relevant sections; include scripts, tests and adapters in their assigned scope. Other languages continue under existing project/shared contracts.

Implementation turns applicable language risks into the smallest correct change and meaningful checks. Review traces the same risks through actual callers/tests and counterevidence, reporting only concrete scoped violations. Select checks by affected behavior; this is not an exhaustive checklist, style migration, new test quota or gate. Prefer clear data ownership, cohesive functions, explicit effects and supported standard APIs over clever expressions or speculative frameworks.

Reuse configured formatters, linters and type checks; do not install or mandate tools merely because they are popular. Formatting preferences, missing annotations or a language pattern name alone are not defects. Record unavailable required checks separately from product failures. This guidance does not grant product edits, refactors, dependency upgrades or external actions.
