# Lua implementation and review

## Runtime and scope
Confirm the Lua dialect and embedding engine. Lua 5.1, LuaJIT, later Lua and Luau are not interchangeable. Verify required syntax/APIs and optional compatibility settings in the actual supported build; do not infer all extensions from a generic LuaJIT version label. The sources below provide a 5.1 baseline and LuaJIT compatibility context, not a command to migrate every project.

## Choose clear and correct code
- **Names and modules:** prefer lexical locals and small cohesive modules with an explicit returned interface. Declare intentional engine callbacks/globals where the host requires them; a global name is a finding only when it violates an actual ownership or collision boundary. Keep dependencies explicit rather than introducing hidden shared state through module loading.
- **Absent versus false:** only `nil` and `false` are falsey; zero and empty strings are truthy. Use `value == nil` for an absent-only default. `x or default` and `condition and a or b` lose a legitimate false result. Validate the intended numeric/string domain at external boundaries rather than relying on coercion.
- **Tables and order:** distinguish contiguous sequences from maps/sparse collections. `#t` is not a sparse entry count; `ipairs` stops at the first missing element. `pairs` supplies no ordering guarantee. If order affects RNG, rewards, serialization or replay, use the agreed explicit order; do not require sorting when order is irrelevant. Removing sequence elements shifts indexes: choose a safe iteration/update strategy. Adding new keys during `next` traversal has no defined behavior in 5.1; changing/removing existing fields is not automatically forbidden.
- **Ownership:** assigning/passing tables shares references. Define who may mutate nested state and whether a snapshot is shallow, deep or a projection. Copy only the state that must be isolated; unconditional deep copying can break intended identity and cost assumptions. Trace aliases at lifecycle boundaries.
- **Calls and results:** keep `:`/`.` receiver conventions consistent with the function contract. Lua multiple returns can be truncated by assignment/expression placement; preserve meaningful status/result/error positions. `pcall` reports whether an exception was raised, not whether the wrapped API returned success. Handle returned `nil, error` or `false, error` according to the API contract. Clean up owned resources on every applicable outcome.
- **Numbers and text:** check the runtime's numeric representation for persistent IDs, bounds and rounding; do not assume later-Lua integers or native bit operators. Byte-based string length/slicing is not Unicode character layout; use the actual supported text API when this matters.
- **Hot paths:** keep avoidable repeated loading, concatenation and temporary allocation out of affected update/draw loops when workload evidence warrants it. Preserve engine thread/lifetime constraints; coroutines do not imply OS-thread parallelism. Do not impose localization tricks, pooling or GC tuning without a concrete cost need.

## Small examples and checks
Preserve a user-selected false value:
```lua
local enabled = options.enabled
if enabled == nil then enabled = true end
```
Separate protected execution from an API's failure return:
```lua
local executed, result, err = pcall(read_resource, resource_id)
if not executed then return nil, result end
if result == nil then return nil, err end -- this API uses nil, error
return result
```
The second example is valid only for the named API convention; a legitimate nil payload needs a different success signal. It is not a universal loader wrapper or permission to swallow errors.

For implicated changes, choose observations such as false/zero/nil, holes versus dense sequences, caller-owned nested tables, repeated teardown and protected-call returned failures. Do not test a particular sparse `#t` result or require `pairs` to change order; absence of a guarantee is sufficient reason to use a specified order where required. Reuse valid guards and supported deliberate sharing as counterevidence.

## Primary sources
- [Lua 5.1 manual](https://www.lua.org/manual/5.1/manual.html): values/references (§2.2), locals (§2.3), operators/length/calls (§2.5), coroutine model (§2.11), `ipairs`/`next`/`pcall` (§5.1), byte strings (§5.4). Consult the corresponding manual for other versions.
- [LuaJIT extensions](https://luajit.org/extensions.html): runtime-specific compatibility and feature conditions. Consult the actual installed revision before adopting extensions.
