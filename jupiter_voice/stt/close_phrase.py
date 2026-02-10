"""Close phrase detection for ending a voice query ("sudo out")."""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Common Whisper misrecognitions of "sudo out"
DEFAULT_PATTERNS = [
    r"sudo\s+out",
    r"pseudo\s+out",
    r"sue\s*do\s+out",
    r"sudo\s+doubt",
    r"su\s*do\s+out",
    r"sudah\s+out",
    r"sudu\s+out",
]


class ClosePhraseDetector:
    """Detects the close phrase 'sudo out' in transcribed text with fuzzy matching."""

    def __init__(
        self,
        primary: str = "sudo out",
        alternatives: Optional[list[str]] = None,
    ) -> None:
        self.primary = primary
        # Start with default patterns only if primary is "sudo out"
        if primary.lower().strip() in ("sudo out", "sudo  out"):
            self.patterns = list(DEFAULT_PATTERNS)
        else:
            # Custom primary — add it as a pattern, skip sudo defaults
            self.patterns = [re.escape(primary).replace(r"\ ", r"\s+")]

        if alternatives:
            for alt in alternatives:
                pattern = re.escape(alt).replace(r"\ ", r"\s+")
                if pattern not in self.patterns:
                    self.patterns.append(pattern)

    def detect(self, text: str) -> bool:
        """Returns True if close phrase found anywhere in text."""
        text_lower = text.lower().strip()
        for pattern in self.patterns:
            if re.search(pattern, text_lower):
                return True
        return False

    def strip(self, text: str) -> str:
        """Remove the close phrase and everything after it from text."""
        text_lower = text.lower()
        earliest_pos = len(text)

        for pattern in self.patterns:
            match = re.search(pattern, text_lower)
            if match and match.start() < earliest_pos:
                earliest_pos = match.start()

        cleaned = text[:earliest_pos].strip()
        return cleaned

    def detect_and_strip(self, text: str) -> tuple[bool, str]:
        """Check for close phrase and return (detected, cleaned_text)."""
        detected = self.detect(text)
        if detected:
            return True, self.strip(text)
        return False, text
