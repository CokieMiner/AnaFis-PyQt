from typing import Protocol, runtime_checkable

from anafis.core.data_structures import TabState


@runtime_checkable
class HasGetState(Protocol):
    def get_state(self) -> TabState: ...
