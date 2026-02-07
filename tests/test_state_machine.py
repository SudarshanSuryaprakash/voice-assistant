"""Tests for the state machine."""

from jupiter_voice.state_machine import Event, State, StateMachine


class TestStateMachine:
    def test_initial_state_is_idle(self):
        sm = StateMachine()
        assert sm.state == State.IDLE

    def test_idle_to_listening(self):
        sm = StateMachine()
        new = sm.transition(Event.WAKE_WORD_DETECTED)
        assert new == State.LISTENING
        assert sm.state == State.LISTENING

    def test_listening_to_processing(self):
        sm = StateMachine()
        sm.transition(Event.WAKE_WORD_DETECTED)
        new = sm.transition(Event.CLOSE_PHRASE_DETECTED)
        assert new == State.PROCESSING

    def test_processing_to_speaking(self):
        sm = StateMachine()
        sm.transition(Event.WAKE_WORD_DETECTED)
        sm.transition(Event.CLOSE_PHRASE_DETECTED)
        new = sm.transition(Event.RESPONSE_RECEIVED)
        assert new == State.SPEAKING

    def test_speaking_to_idle(self):
        sm = StateMachine()
        sm.transition(Event.WAKE_WORD_DETECTED)
        sm.transition(Event.CLOSE_PHRASE_DETECTED)
        sm.transition(Event.RESPONSE_RECEIVED)
        new = sm.transition(Event.PLAYBACK_COMPLETE)
        assert new == State.IDLE

    def test_full_cycle(self):
        sm = StateMachine()
        assert sm.state == State.IDLE
        sm.transition(Event.WAKE_WORD_DETECTED)
        assert sm.state == State.LISTENING
        sm.transition(Event.CLOSE_PHRASE_DETECTED)
        assert sm.state == State.PROCESSING
        sm.transition(Event.RESPONSE_RECEIVED)
        assert sm.state == State.SPEAKING
        sm.transition(Event.PLAYBACK_COMPLETE)
        assert sm.state == State.IDLE

    def test_invalid_transition_stays_in_current_state(self):
        sm = StateMachine()
        new = sm.transition(Event.CLOSE_PHRASE_DETECTED)
        assert new == State.IDLE
        assert sm.state == State.IDLE

    def test_invalid_transition_from_listening(self):
        sm = StateMachine()
        sm.transition(Event.WAKE_WORD_DETECTED)
        new = sm.transition(Event.RESPONSE_RECEIVED)
        assert new == State.LISTENING

    def test_cancel_from_listening(self):
        sm = StateMachine()
        sm.transition(Event.WAKE_WORD_DETECTED)
        new = sm.transition(Event.CANCEL)
        assert new == State.IDLE

    def test_error_from_processing(self):
        sm = StateMachine()
        sm.transition(Event.WAKE_WORD_DETECTED)
        sm.transition(Event.CLOSE_PHRASE_DETECTED)
        new = sm.transition(Event.ERROR)
        assert new == State.IDLE

    def test_error_from_speaking(self):
        sm = StateMachine()
        sm.transition(Event.WAKE_WORD_DETECTED)
        sm.transition(Event.CLOSE_PHRASE_DETECTED)
        sm.transition(Event.RESPONSE_RECEIVED)
        new = sm.transition(Event.ERROR)
        assert new == State.IDLE

    def test_on_enter_callback(self):
        sm = StateMachine()
        called = []
        sm.on_enter(State.LISTENING, lambda: called.append("listening"))
        sm.transition(Event.WAKE_WORD_DETECTED)
        assert called == ["listening"]

    def test_on_enter_not_called_on_invalid_transition(self):
        sm = StateMachine()
        called = []
        sm.on_enter(State.LISTENING, lambda: called.append("listening"))
        sm.transition(Event.CLOSE_PHRASE_DETECTED)  # invalid from IDLE
        assert called == []

    def test_reset(self):
        sm = StateMachine()
        sm.transition(Event.WAKE_WORD_DETECTED)
        sm.transition(Event.CLOSE_PHRASE_DETECTED)
        assert sm.state == State.PROCESSING
        sm.reset()
        assert sm.state == State.IDLE

    def test_multiple_listeners(self):
        sm = StateMachine()
        results = []
        sm.on_enter(State.LISTENING, lambda: results.append("a"))
        sm.on_enter(State.LISTENING, lambda: results.append("b"))
        sm.transition(Event.WAKE_WORD_DETECTED)
        assert results == ["a", "b"]
