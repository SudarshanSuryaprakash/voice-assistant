"""Core state machine for Jupiter Voice."""

from __future__ import annotations

import logging
import threading
from enum import Enum, auto
from typing import Callable

logger = logging.getLogger(__name__)


class State(Enum):
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()


class Event(Enum):
    WAKE_WORD_DETECTED = auto()
    CLOSE_PHRASE_DETECTED = auto()
    RESPONSE_RECEIVED = auto()
    PLAYBACK_COMPLETE = auto()
    ERROR = auto()
    CANCEL = auto()


# Valid state transitions: (current_state, event) -> new_state
TRANSITIONS: dict[tuple[State, Event], State] = {
    (State.IDLE, Event.WAKE_WORD_DETECTED): State.LISTENING,
    (State.LISTENING, Event.CLOSE_PHRASE_DETECTED): State.PROCESSING,
    (State.LISTENING, Event.CANCEL): State.IDLE,
    (State.PROCESSING, Event.RESPONSE_RECEIVED): State.SPEAKING,
    (State.PROCESSING, Event.ERROR): State.IDLE,
    (State.SPEAKING, Event.PLAYBACK_COMPLETE): State.IDLE,
    (State.SPEAKING, Event.ERROR): State.IDLE,
}


class StateMachine:
    """Thread-safe state machine with listener support."""

    def __init__(self) -> None:
        self._state = State.IDLE
        self._lock = threading.Lock()
        self._listeners: dict[State, list[Callable[[], None]]] = {}

    @property
    def state(self) -> State:
        with self._lock:
            return self._state

    def transition(self, event: Event) -> State:
        """Attempt a state transition. Returns the new state (or current if invalid)."""
        with self._lock:
            key = (self._state, event)
            if key not in TRANSITIONS:
                logger.warning(
                    "Invalid transition: %s + %s (ignored)", self._state.name, event.name
                )
                return self._state
            old_state = self._state
            self._state = TRANSITIONS[key]
            logger.info("State: %s -> %s (via %s)", old_state.name, self._state.name, event.name)
            new_state = self._state

        # Notify listeners outside the lock to avoid deadlocks
        for cb in self._listeners.get(new_state, []):
            try:
                cb()
            except Exception:
                logger.exception("Error in state listener for %s", new_state.name)

        return new_state

    def on_enter(self, state: State, callback: Callable[[], None]) -> None:
        """Register a callback to be called when entering a state."""
        self._listeners.setdefault(state, []).append(callback)

    def reset(self) -> None:
        """Reset to IDLE state without triggering listeners."""
        with self._lock:
            self._state = State.IDLE
