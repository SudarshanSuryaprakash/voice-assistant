"""Tests for close phrase detection."""

import pytest

from jupiter_voice.stt.close_phrase import ClosePhraseDetector


class TestClosePhraseDetector:
    def setup_method(self):
        self.detector = ClosePhraseDetector()

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("turn off the lights sudo out", True),
            ("turn off the lights pseudo out", True),
            ("turn off the lights sue do out", True),
            ("sudo doubt", True),
            ("su do out", True),
            ("SUDO OUT", True),
            ("  Sudo  Out  ", True),
            ("turn off the lights", False),
            ("", False),
            ("sudo", False),
            ("out", False),
            ("sudoout", False),
        ],
    )
    def test_detect(self, text: str, expected: bool):
        assert self.detector.detect(text) == expected

    def test_strip_removes_close_phrase_and_after(self):
        text = "What is the weather today sudo out please"
        result = self.detector.strip(text)
        assert result == "What is the weather today"

    def test_strip_handles_phrase_at_end(self):
        text = "check my balance sudo out"
        result = self.detector.strip(text)
        assert result == "check my balance"

    def test_strip_handles_phrase_at_start(self):
        text = "sudo out"
        result = self.detector.strip(text)
        assert result == ""

    def test_strip_preserves_text_without_phrase(self):
        text = "What is the weather today"
        result = self.detector.strip(text)
        assert result == "What is the weather today"

    def test_detect_and_strip(self):
        detected, cleaned = self.detector.detect_and_strip("hello world sudo out goodbye")
        assert detected is True
        assert cleaned == "hello world"

    def test_detect_and_strip_no_match(self):
        detected, cleaned = self.detector.detect_and_strip("hello world")
        assert detected is False
        assert cleaned == "hello world"

    def test_custom_alternatives(self):
        detector = ClosePhraseDetector(alternatives=["over and out", "end query"])
        assert detector.detect("check balance over and out")
        assert detector.detect("check balance end query")
        # Default patterns still work
        assert detector.detect("check balance sudo out")

    def test_multiple_occurrences_strips_at_first(self):
        text = "first sudo out second sudo out third"
        result = self.detector.strip(text)
        assert result == "first"
