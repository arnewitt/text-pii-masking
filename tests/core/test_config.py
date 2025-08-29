import pytest
from src.core.config import Settings
from pydantic import ValidationError


def test_env_vars_override(monkeypatch):
    """Environment variables should override values."""
    monkeypatch.setenv("OPENAI_BASE_URL", "http://custom-url")
    monkeypatch.setenv("OPENAI_API_KEY", "custom-key")
    monkeypatch.setenv("OPENAI_MODEL_NAME", "custom-model")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9090")

    s = Settings()
    assert s.openai_base_url == "http://custom-url"
    assert s.openai_api_key == "custom-key"
    assert s.openai_model_name == "custom-model"
    assert s.host == "127.0.0.1"
    assert s.port == 9090


def test_dotenv_file(tmp_path, monkeypatch):
    """Settings should load values from a .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_BASE_URL=http://dotenv-url\n"
        "OPENAI_API_KEY=dotenv-key\n"
        "OPENAI_MODEL_NAME=dotenv-model\n"
        "HOST=192.168.1.1\n"
        "PORT=1234\n"
    )

    monkeypatch.chdir(tmp_path)  # change CWD so Settings picks up this .env

    s = Settings()
    assert s.openai_base_url == "http://dotenv-url"
    assert s.openai_api_key == "dotenv-key"
    assert s.openai_model_name == "dotenv-model"
    assert s.host == "192.168.1.1"
    assert s.port == 1234


def _clear_openai_env(monkeypatch):
    for k in ["OPENAI_BASE_URL", "OPENAI_API_KEY", "OPENAI_MODEL_NAME", "HOST", "PORT"]:
        monkeypatch.delenv(k, raising=False)


def test_defaults_for_host_and_port(monkeypatch, tmp_path):
    # Ensure no env or .env is visible
    _clear_openai_env(monkeypatch)
    monkeypatch.chdir(tmp_path)

    # Without required fields -> must raise ValidationError
    with pytest.raises(ValidationError):
        Settings()

    # Provide required vars, defaults for host/port should apply
    monkeypatch.setenv("OPENAI_BASE_URL", "http://fake-url")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    monkeypatch.setenv("OPENAI_MODEL_NAME", "gpt-5-mini")

    s = Settings()
    assert s.host == "0.0.0.0"
    assert s.port == 8081


def test_env_vars_override(monkeypatch, tmp_path):
    _clear_openai_env(monkeypatch)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setenv("OPENAI_BASE_URL", "http://custom-url")
    monkeypatch.setenv("OPENAI_API_KEY", "custom-key")
    monkeypatch.setenv("OPENAI_MODEL_NAME", "custom-model")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9090")

    s = Settings()
    assert s.openai_base_url == "http://custom-url"
    assert s.openai_api_key == "custom-key"
    assert s.openai_model_name == "custom-model"
    assert s.host == "127.0.0.1"
    assert s.port == 9090


def test_dotenv_file(tmp_path, monkeypatch):
    _clear_openai_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_BASE_URL=http://dotenv-url\n"
        "OPENAI_API_KEY=dotenv-key\n"
        "OPENAI_MODEL_NAME=dotenv-model\n"
        "HOST=192.168.1.1\n"
        "PORT=1234\n"
    )
    monkeypatch.chdir(tmp_path)

    s = Settings()
    assert s.openai_base_url == "http://dotenv-url"
    assert s.openai_api_key == "dotenv-key"
    assert s.openai_model_name == "dotenv-model"
    assert s.host == "192.168.1.1"
    assert s.port == 1234


def test_missing_required_fields(monkeypatch, tmp_path):
    _clear_openai_env(monkeypatch)
    monkeypatch.chdir(tmp_path)  # ensure no project .env is loaded

    with pytest.raises(ValidationError):
        Settings()
