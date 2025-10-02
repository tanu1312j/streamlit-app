from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    # for type checkers, import the real type
    from langfuse.callback import CallbackHandler  # type: ignore
else:
    CallbackHandler = None  # type: ignore


def get_tracer() -> Optional[object]:
    if CallbackHandler is None:
        return None
    try:
        return CallbackHandler()
    except Exception:
        return None


tracer = get_tracer()
