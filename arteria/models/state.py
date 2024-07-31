from enum import Enum


class State(Enum):
    NONE = "none"
    READY = "ready"
    PENDING = "pending"
    STARTED = "started"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"
