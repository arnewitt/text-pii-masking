import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

import logging
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pprint import pprint

load_dotenv()

from masking import extract_pii, mask_pii


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PIIConfig(BaseModel):
    """Configuration model for PII types."""

    first_name: str = Field(
        ...,
        title="First Name",
        description="First name of a person",
        mask="[!FIRST-NAME!]",
    )
    last_name: str = Field(
        ...,
        title="Last Name",
        description="Last name of a person.",
        mask="[!LAST-NAME!]",
    )
    email: str = Field(
        ...,
        title="Email address",
        description="Email address.",
        mask="[!EMAIL-ADDRESS!]",
    )


def main():
    # Sample input text
    input_texts = [
        "John Doe's email is john.doe@example.com. "
        "His first name is John and his last name is Doe. "
        "His second email is dem@example.com."
    ]

    # Extract PII from input text
    extracted_pii = [extract_pii(text, PIIConfig) for text in input_texts]

    # Mask PII in input text
    masked_text = [
        mask_pii(text, pii, PIIConfig) for text, pii in zip(input_texts, extracted_pii)
    ]

    pprint(f"Extracted pii: {extracted_pii}")
    pprint(f"Masked text: {masked_text}")


if __name__ == "__main__":
    main()
