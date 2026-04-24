Prefer layered Python architecture:
- keep orchestration separate from infrastructure
- use small dataclasses and explicit interfaces
- avoid hidden global state unless it is session-local CLI runtime state
- prefer extendable registries for tools and skills