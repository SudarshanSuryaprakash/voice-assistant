"""Tests for the OpenClaw gateway client."""

import json

import pytest

from jupiter_voice.gateway.openclaw import OpenClawError, OpenClawGateway


class TestOpenClawGateway:
    def test_construction(self):
        gw = OpenClawGateway(session_id="agent:main:main", timeout=60)
        assert gw.session_id == "agent:main:main"
        assert gw.timeout == 60

    def test_extract_response_success(self):
        gw = OpenClawGateway()
        stdout = json.dumps({
            "status": "ok",
            "summary": "completed",
            "result": {
                "payloads": [{"text": "Hello world!", "mediaUrl": None}],
            },
        })
        result = gw._extract_response(stdout)
        assert result == "Hello world!"

    def test_extract_response_with_prefix_noise(self):
        """CLI may print warnings before the JSON."""
        gw = OpenClawGateway()
        stdout = "Some warning text\nAnother line\n" + json.dumps({
            "status": "ok",
            "result": {"payloads": [{"text": "Response here"}]},
        })
        result = gw._extract_response(stdout)
        assert result == "Response here"

    def test_extract_response_multiple_payloads(self):
        gw = OpenClawGateway()
        stdout = json.dumps({
            "status": "ok",
            "result": {
                "payloads": [
                    {"text": "First part."},
                    {"text": "Second part."},
                ],
            },
        })
        result = gw._extract_response(stdout)
        assert result == "First part.\nSecond part."

    def test_extract_response_error_status(self):
        gw = OpenClawGateway()
        stdout = json.dumps({
            "status": "error",
            "summary": "agent failed",
            "result": {"payloads": []},
        })
        with pytest.raises(OpenClawError, match="status 'error'"):
            gw._extract_response(stdout)

    def test_extract_response_no_json(self):
        gw = OpenClawGateway()
        with pytest.raises(OpenClawError, match="No JSON found"):
            gw._extract_response("just some text without json")

    def test_extract_response_empty_payloads(self):
        gw = OpenClawGateway()
        stdout = json.dumps({
            "status": "ok",
            "result": {"payloads": []},
        })
        with pytest.raises(OpenClawError, match="no payloads"):
            gw._extract_response(stdout)

    def test_send_message_missing_cli(self):
        """Test that a missing CLI raises OpenClawError."""
        gw = OpenClawGateway(openclaw_bin="/nonexistent/path/openclaw")
        with pytest.raises(OpenClawError, match="not found"):
            gw.send_message("test")
