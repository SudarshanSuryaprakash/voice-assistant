"""OpenClaw gateway client using the CLI."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess

logger = logging.getLogger(__name__)


class OpenClawError(Exception):
    """Raised when the OpenClaw gateway returns an error or is unreachable."""


class OpenClawGateway:
    """Sends messages to OpenClaw via the `openclaw agent` CLI and receives responses."""

    def __init__(
        self,
        session_id: str = "agent:main:main",
        timeout: int = 120,
        openclaw_bin: str | None = None,
    ) -> None:
        self.session_id = session_id
        self.timeout = timeout
        self.openclaw_bin = openclaw_bin or shutil.which("openclaw") or "openclaw"

    def send_message(self, message: str) -> str:
        """
        Send transcribed text to OpenClaw and return the response text.

        Uses `openclaw agent --message "..." --session-id ... --json`.

        Raises:
            OpenClawError: On any failure (timeout, CLI error, parse error).
        """
        cmd = [
            self.openclaw_bin,
            "agent",
            "--message", message,
            "--session-id", self.session_id,
            "--json",
            "--timeout", str(self.timeout),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 10,  # extra buffer beyond openclaw's own timeout
            )
        except subprocess.TimeoutExpired:
            raise OpenClawError("OpenClaw command timed out")
        except FileNotFoundError:
            raise OpenClawError(
                f"OpenClaw CLI not found at '{self.openclaw_bin}'. "
                "Is OpenClaw installed?"
            )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise OpenClawError(f"OpenClaw CLI error (exit {result.returncode}): {stderr}")

        # Parse JSON from stdout — the CLI may print non-JSON warnings before the JSON
        stdout = result.stdout.strip()
        return self._extract_response(stdout)

    def _extract_response(self, stdout: str) -> str:
        """Extract the response text from openclaw agent --json output."""
        # Find the JSON object in the output (skip any leading non-JSON lines)
        json_start = stdout.find("{")
        if json_start == -1:
            raise OpenClawError(f"No JSON found in OpenClaw output: {stdout[:200]}")

        json_str = stdout[json_start:]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise OpenClawError(f"Failed to parse OpenClaw JSON output: {e}")

        # Extract text from result.payloads[0].text
        status = data.get("status")
        if status != "ok":
            summary = data.get("summary", "unknown error")
            raise OpenClawError(f"OpenClaw returned status '{status}': {summary}")

        result = data.get("result", {})
        payloads = result.get("payloads", [])
        if not payloads:
            raise OpenClawError("OpenClaw returned no payloads")

        # Concatenate all payload texts
        texts = [p.get("text", "") for p in payloads if p.get("text")]
        if not texts:
            raise OpenClawError("OpenClaw returned empty response")

        return "\n".join(texts)

    def health_check(self) -> tuple[bool, str]:
        """Check if the OpenClaw CLI is available and gateway is running."""
        bin_path = shutil.which(self.openclaw_bin)
        if not bin_path:
            return False, f"OpenClaw CLI not found: {self.openclaw_bin}"

        try:
            result = subprocess.run(
                [self.openclaw_bin, "doctor", "--json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return True, f"OpenClaw CLI ready ({bin_path})"
            return False, f"OpenClaw doctor failed (exit {result.returncode})"
        except subprocess.TimeoutExpired:
            return False, "OpenClaw doctor timed out"
        except Exception as e:
            return False, str(e)
