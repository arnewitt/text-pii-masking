import json
import pytest
from pydantic import BaseModel, Field

import src.masking as masking_mod
from src.core.config import Settings


class _FakeCompletion:
    def __init__(self, content: str):
        self.choices = [
            type("Choice", (), {"message": type("Msg", (), {"content": content})()})()
        ]


class _FakeCompletions:
    def __init__(self, content: str = None, to_raise: Exception | None = None):
        self._content = content
        self._to_raise = to_raise

    def parse(self, **kwargs):
        if self._to_raise:
            raise self._to_raise
        return _FakeCompletion(self._content)


class _FakeClient:
    """Emulates client.beta.chat.completions.parse(...)"""

    def __init__(self, content: str = None, to_raise: Exception | None = None):
        self.beta = type(
            "Beta",
            (),
            {
                "chat": type(
                    "Chat",
                    (),
                    {
                        "completions": _FakeCompletions(
                            content=content, to_raise=to_raise
                        )
                    },
                )()
            },
        )()


class _DummySettings(Settings):
    # Avoid reading any .env by giving explicit defaults for required fields
    openai_base_url: str = "http://test"
    openai_api_key: str = "sk-test"
    openai_model_name: str = "gpt-test"


class PIIConfig(BaseModel):
    email: str = Field(default="", json_schema_extra={"mask": "[EMAIL]"})
    phone: str = Field(default="", json_schema_extra={"mask": "[PHONE]"})


class NoMaskConfig(BaseModel):
    email: str = Field(default="")  # no json_schema_extra -> no mask


class EmptyConfig(BaseModel):
    pass


# ---------------------------
# Prompt helpers
# ---------------------------


def test_get_pii_identification_system_prompt():
    s = masking_mod.get_pii_identification_system_prompt()
    # basic sanity checks
    assert "identifying PII" in s or "PII" in s
    assert isinstance(s, str) and len(s) > 10


def test_get_pii_extraction_instruct_prompt():
    text = "Hi alice@example.com"
    types = "email, phone"
    p = masking_mod.get_pii_extraction_instruct_prompt(text, types)
    assert "alice@example.com" in p
    assert types in p
    assert "valid JSON array" in p


# ---------------------------
# JSON response parser
# ---------------------------


def test_parse_json_response_plain_json():
    payload = [{"pii": "alice@example.com", "type": "email"}]
    out = masking_mod.parse_json_response(json.dumps(payload))
    assert out == payload


def test_parse_json_response_fenced_block_with_lang():
    payload = [{"pii": "1234567890", "type": "phone"}]
    raw = "```json\n" + json.dumps(payload) + "\n```"
    out = masking_mod.parse_json_response(raw)
    assert out == payload


def test_parse_json_response_fenced_block_without_lang():
    payload = [{"pii": "1234567890", "type": "phone"}]
    raw = "```\n" + json.dumps(payload) + "\n```"
    out = masking_mod.parse_json_response(raw)
    assert out == payload


def test_parse_json_response_invalid_raises_valueerror():
    with pytest.raises(ValueError):
        masking_mod.parse_json_response("this is not json")


# ---------------------------
# extract_pii
# ---------------------------


def test_extract_pii_success(monkeypatch):
    # Arrange: fake OpenAI client returning JSON list
    response_items = [{"pii": "alice@example.com", "type": "email"}]
    fake_client = _FakeClient(content=json.dumps(response_items))

    # Patch the global client used by the module
    monkeypatch.setattr(masking_mod, "client", fake_client)

    # Use dummy settings to avoid real env
    s = _DummySettings()

    out = masking_mod.extract_pii("Hello alice@example.com", PIIConfig, settings=s)
    assert out == response_items


def test_extract_pii_no_pii_types_raises_valueerror():
    s = _DummySettings()
    with pytest.raises(ValueError, match="No PII types defined"):
        masking_mod.extract_pii("hello", EmptyConfig, settings=s)


def test_extract_pii_openai_error_bubbles(monkeypatch):
    # Arrange: fake client that raises OpenAIError from parse()
    fake_err = masking_mod.OpenAIError("boom")
    fake_client = _FakeClient(to_raise=fake_err)
    monkeypatch.setattr(masking_mod, "client", fake_client)

    s = _DummySettings()
    with pytest.raises(masking_mod.OpenAIError):
        masking_mod.extract_pii("hello", PIIConfig, settings=s)


# ---------------------------
# mask_pii
# ---------------------------


def test_mask_pii_happy_path():
    text = "Contact me at alice@example.com or 123-456."
    extracted = [
        {"pii": "alice@example.com", "type": "email"},
        {"pii": "123-456", "type": "phone"},
    ]
    masked = masking_mod.mask_pii(text, extracted, PIIConfig)
    assert masked == "Contact me at [EMAIL] or [PHONE]."


def test_mask_pii_missing_mask_keeps_text():
    text = "Contact me at alice@example.com"
    extracted = [{"pii": "alice@example.com", "type": "email"}]
    # NoMaskConfig has no json_schema_extra mask; should not replace
    masked = masking_mod.mask_pii(text, extracted, NoMaskConfig)
    assert masked == text


def test_mask_pii_invalid_config_raises():
    text = "Contact me at alice@example.com"
    with pytest.raises(ValueError, match="Invalid PII configuration"):
        masking_mod.mask_pii(
            text, [{"pii": "alice@example.com", "type": "email"}], object()
        )


def test_mask_pii_ignores_malformed_entries():
    text = "Contact me at alice@example.com"
    extracted = [
        {"pii": None, "type": "email"},  # missing pii value
        {"pii": "alice@example.com"},  # missing type
        {},  # empty
    ]
    masked = masking_mod.mask_pii(text, extracted, PIIConfig)
    # no valid entries -> no change
    assert masked == text
