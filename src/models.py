from pydantic import BaseModel, Field, create_model
from typing import List, Dict


class PIITypeConfig(BaseModel):
    """Model for PII type configuration."""

    mask: str = Field(
        ...,
        title="Mask String",
        description="The string to replace this PII type with",
        example="[!MASKED!]",
    )


class MaskResponse(BaseModel):
    """API response model for masked PII text."""

    original_texts: List[str] = Field(
        ...,
        title="Original Texts",
        description="List of original input texts before masking",
    )
    masked_texts: List[str] = Field(
        ..., title="Masked Texts", description="List of texts with PII masked"
    )
    detected_pii: List[List[Dict[str, str]]] = Field(
        ...,
        title="Detected PII",
        description="List of PII detected in each text. Each inner list contains dictionaries of PII found in the corresponding text.",
    )


class MaskRequest(BaseModel):
    """API request model for masking PII in text."""

    texts: List[str] = Field(
        ...,
        title="Input Texts",
        description="List of texts to analyze and mask PII from",
        example=[
            "John Doe's email is john.doe@example.com",
            "John Doe's other email is johns.other.mail@example.com",
        ],
    )
    pii_config: Dict[str, PIITypeConfig] = Field(
        ...,
        title="PII Configuration",
        description="Dictionary mapping PII types to their mask configurations",
        example={
            "first_name": {"mask": "[!FIRST-NAME!]"},
            "last_name": {"mask": "[!LAST-NAME!]"},
            "email": {"mask": "[!EMAIL-ADDRESS!]"},
        },
    )


def create_dynamic_pii_config(pii_config_dict: Dict[str, PIITypeConfig]) -> type:
    """
    Dynamically create a PIIConfig class from the request configuration.

    Args:
        pii_config_dict: Dictionary of PII types and their configurations

    Returns:
        Dynamically created PIIConfig class
    """
    fields = {
        pii_type: (str, Field(..., json_schema_extra={"mask": config.mask}))
        for pii_type, config in pii_config_dict.items()
    }

    return create_model("DynamicPIIConfig", __base__=BaseModel, **fields)
