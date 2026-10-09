# Capability-tier model routing

Choose and record a capability tier for every actual dispatch. Tiers are portable; a concrete mapping is an optional override. Without a mapping, use the required common host-default decision. Host model availability and execution evidence are not project facts.

| Tier | Use when |
| --- | --- |
| `highest-judgment` | A wrong decision can invalidate product direction, architecture, shared state or final integration; ambiguity or cross-stage dependencies are high. |
| `complex-execution` | The contract is settled but implementation or review needs substantial reasoning, tools or long context. |
| `balanced-execution` | Scope and checks are clear, ordinary engineering judgment is sufficient and cost still matters. |
| `high-volume` | Work is repetitive, independently checkable, low risk and benefits from throughput. |

Consider error impact, dependency depth, ambiguity, context size, verification strength and repetition/cost in that order. Use the lowest tier that still covers the failure cost. Independent review requires a separate executor; it does not automatically require a different or stronger model.

## Resolution

1. Preserve a user-specified model. If it is unavailable or the execution tool cannot override models, block that dispatch and report the exact incompatibility.
2. Read any configured `modelRoutingProfilePath` (explicit override). With no mapping pass profile=None to the resolver: keep the host default, reasoningClass=null and a recorded common-host-default reason. With a mapping resolve current available models in its candidate order.
3. Apply the resolved model and reasoning effort only when the dispatch tool supports explicit overrides. The current root model never changes silently.
4. If no tier candidate is available, or overrides are unsupported, keep the host-selected default and continue. Record the fallback; do not invent a model ID.

Record `capabilityTier`, `reasoningClass`, `resolvedModel`, `resolutionSource`, `overrideSupported` and `fallbackReason` for each dispatch. Use `host-default` as the resolved model label when no override is applied. Re-resolve at dispatch time because host availability may change.

The required deterministic resolver in `scripts/resolve_model_route.py` validates a project mapping and applies these fallback rules. Its result is a dispatch input, not proof that the host actually used the model; retain the executor acknowledgement or raw runtime header as execution evidence.
