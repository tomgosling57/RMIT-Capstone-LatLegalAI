"""
LatMatrix Chainlit Application Package.

Exposes the refactored modules for the Chainlit application.
Modules are imported lazily (on access) rather than eagerly at import time,
so that test collection does not trigger the full import chain.
"""

import importlib
import typing as _t

_MODULES = ["auth", "database", "document_processor", "llm", "summary"]

__all__ = list(_MODULES)


def __getattr__(name: str) -> _t.Any:
    """Lazy-load submodules on attribute access."""
    if name in _MODULES:
        module = importlib.import_module(f".{name}", __package__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
