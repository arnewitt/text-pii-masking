import pytest
from pydantic import ValidationError

from src.models import (
    PIITypeConfig,
    MaskRequest,
    MaskResponse,
    create_dynamic_pii_config,
)


def test_pii_type_config_requires_mask():
    # valid
    cfg = PIITypeConfig(mask="[MASK]")
    assert cfg.mask == "[MASK]"

    # missing mask -> ValidationError
    with pytest.raises(ValidationError):
        PIITypeConfig()  # type: ignore[call-arg]


def test_mask_request_parses_and_validates():
    req = MaskRequest(
        texts=["John's email is john@example.com"],
        pii_config={
            # dict values should be parsed into PIITypeConfig automatically
            "email": {"mask": "[EMAIL]"},
            "first_name": PIITypeConfig(mask="[FN]"),
        },
    )
    assert req.texts == ["John's email is john@example.com"]
    assert isinstance(req.pii_config["email"], PIITypeConfig)
    assert req.pii_config["email"].mask == "[EMAIL]"

    # texts must be a list of strings
    with pytest.raises(ValidationError):
        MaskRequest(texts="not-a-list", pii_config={"email": {"mask": "[X]"}})  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        MaskRequest(texts=[123], pii_config={"email": {"mask": "[X]"}})  # type: ignore[list-item]


def test_mask_response_validates_nested_detected_pii():
    resp = MaskResponse(
        original_texts=["a", "b"],
        masked_texts=["A", "B"],
        detected_pii=[[{"pii": "john@example.com", "type": "email"}], []],
    )
    assert resp.original_texts == ["a", "b"]
    assert resp.masked_texts == ["A", "B"]
    assert resp.detected_pii[0][0]["pii"] == "john@example.com"


def test_create_dynamic_pii_config_builds_required_fields_with_masks():
    cfg = {
        "email": PIITypeConfig(mask="[EMAIL]"),
        "first_name": PIITypeConfig(mask="[FN]"),
    }
    Dynamic = create_dynamic_pii_config(cfg)

    # Should be a pydantic model class with the fields specified
    assert hasattr(Dynamic, "model_fields")
    fields = Dynamic.model_fields
    assert set(fields.keys()) == {"email", "first_name"}

    # Fields are required (i.e., no default) and have json_schema_extra.mask set
    assert fields["email"].is_required()
    assert (fields["email"].json_schema_extra or {}).get("mask") == "[EMAIL]"
    assert fields["first_name"].is_required()
    assert (fields["first_name"].json_schema_extra or {}).get("mask") == "[FN]"

    # The generated model validates the required string fields
    with pytest.raises(ValidationError):
        Dynamic()  # missing required fields

    # Provide values to satisfy the required fields
    instance = Dynamic(email="alice@example.com", first_name="Alice")
    assert instance.email == "alice@example.com"
    assert instance.first_name == "Alice"


def test_create_dynamic_pii_config_empty_returns_model_with_no_fields():
    Dynamic = create_dynamic_pii_config({})
    assert hasattr(Dynamic, "model_fields")
    assert Dynamic.model_fields == {}

    # With no fields, instance can be created without values
    instance = Dynamic()
    assert instance.model_dump() == {}
