import os
import re
import json
import logging
from typing import List, Dict, Type
from pydantic import BaseModel
from openai import OpenAI, OpenAIError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        base_url=os.environ.get("BASE_URL", "https://api.openai.com/v1"),
    )  # default to OpenAI API v1, but any compatible service can be used, including locally hosted LLMs
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    raise


def get_pii_identification_system_prompt() -> str:
    """
    Returns the system prompt used for PII (Personally Identifiable Information) identification.

    This function provides a static system prompt that instructs an AI model to:
    - Act as a PII identification expert
    - Detect PII from contextual clues
    - Classify PII accurately
    - Take a conservative approach by masking uncertain content

    Returns:
        str: A string containing the system prompt for PII identification
    """
    return (
        "You are an expert at identifying PII in text. "
        "You can accurately detect PII from context and classify it correctly. "
        "When uncertain, mask the content rather than risk PII exposure."
    )


def get_pii_extraction_instruct_prompt(text: str, types_str: str) -> str:
    """
    Generates an instruction prompt for PII (Personal Identifiable Information) extraction.

    This function creates a formatted prompt string that can be used to request extraction
    of PII elements from text, specifying which PII types should be identified.

    Args:
        text (str): The input text from which PII should be extracted
        types_str (str): Comma-separated string of PII types to look for

    Returns:
        str: A formatted prompt string requesting PII extraction with JSON output format specification
    """
    return (
        f"Extract all substrings from the text below that are personal identifiable information "
        f"of the following types: {types_str}. "
        "For each detected item, output a valid JSON array of objects with two keys:\n"
        "  - 'pii': the exact substring detected\n"
        f"  - 'type': the PII type (must match one of: {types_str})\n\n"
        f"Text: '{text}'"
    )


def parse_json_response(response: str) -> List[Dict[str, str]]:
    """
    Extracts and parses JSON content from an OpenAI API response string.

    Args:
        response: Raw response string containing JSON

    Returns:
        List of dictionaries containing PII data

    Raises:
        ValueError: If JSON parsing fails
    """
    try:
        pattern = r"```(?:json)?\s*([\s\S]*?)```"
        match = re.search(pattern, response)
        json_str = match.group(1).strip() if match else response.strip()
        return json.loads(json_str)

    except (re.error, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        raise ValueError(f"Invalid JSON response: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {str(e)}")
        raise


def extract_pii(text: str, pii_config: Type[BaseModel]) -> List[Dict[str, str]]:
    """
    Extract PII from the given text using OpenAI API.

    Args:
        text: Input text to analyze
        pii_config: PII configuration model class

    Returns:
        List of dictionaries containing detected PII and their types

    Raises:
        OpenAIError: If API call fails
        ValueError: If configuration is invalid
    """
    try:
        pii_types = list(pii_config.model_fields.keys())
        if not pii_types:
            raise ValueError("No PII types defined in configuration")

        types_str = ", ".join(pii_types)

        completion = client.beta.chat.completions.parse(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": get_pii_identification_system_prompt(),
                },
                {
                    "role": "user",
                    "content": get_pii_extraction_instruct_prompt(text, types_str),
                },
            ],
            temperature=0,
            timeout=30,
        )
        response = completion.choices[0].message.content

        # Parsing JSON response required as 'completion.choices[0].message.parsed' not reliable
        return parse_json_response(response)

    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error extracting PII: {str(e)}")
        raise


def mask_pii(
    input_text: str, extracted_pii: List[Dict[str, str]], config: Type[BaseModel]
) -> str:
    """
    Mask detected PII in the input text using configured mask values.

    Args:
        input_text: Original text containing PII
        extracted_pii: List of detected PII items with their types
        config: PII configuration class with mask definitions

    Returns:
        Text with all detected PII replaced by their corresponding masks

    Raises:
        ValueError: If PII configuration is invalid
    """
    try:
        masked_text = input_text
        if not hasattr(config, "model_fields"):
            raise ValueError("Invalid PII configuration model")

        config_fields = config.model_fields

        for pii in extracted_pii:
            pii_type = pii.get("type")
            pii_value = pii.get("pii")

            if not pii_value or not pii_type:
                logger.warning(f"Invalid PII entry: {pii}")
                continue

            if pii_type in config_fields:
                mask = config_fields[pii_type].json_schema_extra.get("mask")
                if mask:
                    masked_text = masked_text.replace(pii_value, mask)
                else:
                    logger.warning(f"No mask defined for PII type: {pii_type}")

        return masked_text

    except Exception as e:
        logger.error(f"Error masking PII: {str(e)}")
        raise
