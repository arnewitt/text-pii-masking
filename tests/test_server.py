# tests/api/test_server.py
import pytest
from fastapi.testclient import TestClient

from src.server import app as fastapi_app
import src.server as server_module  # for monkeypatching names used inside the endpoint


@pytest.fixture()
def client():
    return TestClient(fastapi_app)


@pytest.fixture()
def dummy_config_class():
    class DynamicPIIConfig:
        # mimic a pydantic model class just enough for our mocks
        model_fields = {"email": object()}

    return DynamicPIIConfig


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


def test_mask_pii_success(monkeypatch, client, dummy_config_class):
    # Arrange: dynamic config creation
    monkeypatch.setattr(
        server_module, "create_dynamic_pii_config", lambda cfg: dummy_config_class
    )

    # Arrange: extract & mask behavior
    def fake_extract_pii(text, Config):
        return (
            [{"type": "email", "pii": "alice@example.com"}] if "alice@" in text else []
        )

    def fake_mask_pii(text, detected, Config):
        masked = text
        for item in detected:
            masked = masked.replace(item["pii"], "[EMAIL]")
        return masked

    monkeypatch.setattr(server_module, "extract_pii", fake_extract_pii)
    monkeypatch.setattr(server_module, "mask_pii", fake_mask_pii)

    payload = {
        "texts": ["Hi alice@example.com", "No PII"],
        "pii_config": {"email": {"mask": "[EMAIL]"}},
    }

    r = client.post("/mask-pii", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["original_texts"] == payload["texts"]
    assert body["masked_texts"] == ["Hi [EMAIL]", "No PII"]
    assert body["detected_pii"] == [[{"type": "email", "pii": "alice@example.com"}], []]


def test_mask_pii_empty_config_400(client):
    payload = {"texts": ["foo"], "pii_config": {}}
    r = client.post("/mask-pii", json=payload)
    assert r.status_code == 400
    assert r.json()["detail"] == "PII configuration cannot be empty"


def test_mask_pii_empty_texts_400(client):
    payload = {"texts": [], "pii_config": {"email": {"mask": "[EMAIL]"}}}
    r = client.post("/mask-pii", json=payload)
    assert r.status_code == 400
    assert r.json()["detail"] == "Input texts cannot be empty"


def test_mask_pii_whitespace_text_400(client):
    payload = {"texts": ["   "], "pii_config": {"email": {"mask": "[EMAIL]"}}}
    r = client.post("/mask-pii", json=payload)
    assert r.status_code == 400
    assert (
        r.json()["detail"] == "Input texts cannot be empty strings or whitespace only"
    )


def test_mask_pii_validationerror_branch(monkeypatch, client):
    # Make the app catch its ValidationError branch deterministically
    class FakeValidationError(Exception):
        pass

    monkeypatch.setattr(server_module, "ValidationError", FakeValidationError)

    def raise_validation_error(_):
        raise FakeValidationError("bad pii config")

    monkeypatch.setattr(
        server_module, "create_dynamic_pii_config", raise_validation_error
    )

    payload = {"texts": ["hello"], "pii_config": {"email": {"mask": "[EMAIL]"}}}
    r = client.post("/mask-pii", json=payload)
    assert r.status_code == 400
    assert "Invalid PII configuration" in r.json()["detail"]


def test_mask_pii_internal_error_500(monkeypatch, client, dummy_config_class):
    # create config ok
    monkeypatch.setattr(
        server_module, "create_dynamic_pii_config", lambda cfg: dummy_config_class
    )

    # make extract_pii blow up -> generic 500 except path
    def boom(*args, **kwargs):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(server_module, "extract_pii", boom)

    payload = {"texts": ["hello"], "pii_config": {"email": {"mask": "[EMAIL]"}}}
    r = client.post("/mask-pii", json=payload)
    assert r.status_code == 500
    assert r.json()["detail"] == "Internal server error"
