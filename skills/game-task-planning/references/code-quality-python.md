# Python implementation and review

## Runtime and scope
Confirm supported Python versions and existing packaging/tool settings before choosing syntax, standard-library APIs or typing features. Current online documentation may describe a newer interpreter. Style guidance is subordinate to the project's adopted rules and compatibility; avoid unrelated reformatting or mandatory new tooling.

## Choose clear and correct code
- **Readable responsibility:** use descriptive names, small cohesive functions and simple control flow. Prefer a clear comprehension for a simple transformation and an ordinary loop when branches/effects become difficult to follow. Keep decision logic testable apart from storage, network and process effects where the changed contract warrants it. Do not introduce a class/dataclass/framework solely to meet a pattern preference.
- **Defaults and closures:** mutable defaults are created at definition time and shared across calls. Use a fresh value per call when isolation is required; an intentional shared cache is not automatically a defect. Choose an explicit sentinel when `None` is meaningful. Closures resolve captured names when invoked; bind per-iteration values when callbacks require a distinct snapshot.
- **Aliasing and collections:** assignment shares objects; shallow copies retain nested references. Match copying/projection to the required ownership boundary rather than deep-copying everything. Preserve caller-provided empty collections with an absent-only check when the contract requires that identity. Avoid mutating an iterated collection in ways that skip items or invalidate traversal; choose a clear snapshot/rebuild where needed. Use membership/index structures appropriate to actual workload, not speculative optimization.
- **Contracts and typing:** use supported annotations where they clarify changed interfaces or configured checks require them. Annotations do not validate untrusted runtime data. Distinguish `None`, false, zero and empty values according to the API; `is None` expresses an absence check, while `is` is not general value equality. Do not impose strict typing on unrelated code or assume a checker has run.
- **Errors and cleanup:** catch the expected exception at the boundary that can recover; broad handlers require a deliberate error policy, not unconditional success. Preserve useful causes when translating failures and keep protected data out of diagnostics. Use context managers or `try/finally` for owned resources; inspect `return`/`break`/`continue` in `finally` when they can hide a pending outcome. Imports should not perform unrequested external actions; use a guarded entry point for executable script behavior where appropriate.
- **Async ownership:** track who awaits/retains tasks and handles exceptions. `await` does not make blocking disk/network/CPU calls nonblocking. On cancellation, complete owned cleanup and normally propagate `asyncio.CancelledError`; deliberate suppression needs the existing cancellation contract. Check supported-version structured-concurrency APIs before using them. Do not require `TaskGroup` or threads for ordinary synchronous code.
- **I/O and trust:** use explicit encodings and path/base-directory contracts when reproducibility depends on them. Treat decoded JSON and external inputs as unvalidated until their required shape/ranges are checked. Do not use `assert` as required runtime input validation: optimized Python can remove it. For subprocess or deserialization changes, preserve the agreed trust boundary and error/exit handling; do not turn this into an unrelated security audit.

## Small examples and checks
Create per-call state while preserving a caller's empty list:
```python
def collect(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```
Use a separate sentinel if the API permits `None` as actual data. Do not replace the absence check with `items = items or []` when caller identity matters.

Bind the intended value for deferred callbacks:
```python
callbacks = [lambda value=value: value for value in values]
```
Use that binding only when each callback needs its own value; reading the latest shared state can also be intentional.

For implicated changes, select repeated calls, explicit empty/false inputs, nested alias mutation, delayed callbacks, expected/unexpected exceptions, cleanup or cancellation. Verify meaningful assertions and actual process exit codes. Successful type/lint/syntax checks do not replace runtime behavior evidence.

## Primary sources
- [PEP 8](https://peps.python.org/pep-0008/): readability, project consistency, comparisons and exception handling; do not break compatibility for style.
- [Python control flow](https://docs.python.org/3/tutorial/controlflow.html#default-argument-values): default evaluation and function behavior.
- [Python copying](https://docs.python.org/3/library/copy.html): bindings, shallow/deep sharing and excessive copying risks.
- [Python typing](https://docs.python.org/3/library/typing.html): annotation/runtime distinction and version-specific typing APIs.
- [Python exceptions](https://docs.python.org/3/tutorial/errors.html): recovery, chaining and resource cleanup.
- [Python asyncio tasks](https://docs.python.org/3/library/asyncio-task.html): task ownership, cancellation and cleanup.
- [Python programming FAQ](https://docs.python.org/3/faq/programming.html): closure late binding.
- [Python assert statement](https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement): optimization can remove assert checks. Check the supported version rather than transferring current-version APIs.
