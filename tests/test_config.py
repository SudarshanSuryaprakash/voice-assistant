"""Tests for configuration loading."""

from jupiter_voice.config import JupiterConfig, load_config


class TestJupiterConfig:
    def test_default_values(self):
        config = JupiterConfig()
        assert config.wake.model == "hey_jarvis"
        assert config.wake.threshold == 0.5
        assert config.stt.model == "distil-medium.en"
        assert config.tts.voice == "af_heart"
        assert config.close_phrase.primary == "sudo out"
        assert config.audio.sample_rate == 16000
        assert config.gateway.timeout == 120
        assert config.gateway.session_id == "agent:main:main"
        assert config.cues.enabled is True

    def test_load_from_yaml(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "wake:\n  model: 'hey_jupiter'\n  threshold: 0.7\nstt:\n  model: 'large'\n"
        )
        config = load_config(str(config_file))
        assert config.wake.model == "hey_jupiter"
        assert config.wake.threshold == 0.7
        assert config.stt.model == "large"
        # Other defaults preserved
        assert config.tts.voice == "af_heart"

    def test_load_missing_file_uses_defaults(self, tmp_path):
        config = load_config(str(tmp_path / "nonexistent.yaml"))
        assert config.wake.model == "hey_jarvis"

    def test_env_override(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("stt:\n  model: 'small'\n")
        monkeypatch.setenv("JUPITER_VOICE_STT_MODEL", "large")
        config = load_config(str(config_file))
        assert config.stt.model == "large"

    def test_env_override_float(self, monkeypatch, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        monkeypatch.setenv("JUPITER_VOICE_WAKE_THRESHOLD", "0.8")
        config = load_config(str(config_file))
        assert config.wake.threshold == 0.8

    def test_gateway_session_id_from_yaml(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("gateway:\n  session_id: 'agent:test:test'\n")
        config = load_config(str(config_file))
        assert config.gateway.session_id == "agent:test:test"

    def test_env_override_session_id(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        monkeypatch.setenv("JUPITER_VOICE_SESSION_ID", "agent:custom:session")
        config = load_config(str(config_file))
        assert config.gateway.session_id == "agent:custom:session"
