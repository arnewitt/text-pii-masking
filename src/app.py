from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
from typing import Type
from dotenv import load_dotenv
from models import MaskResponse, MaskRequest, create_dynamic_pii_config

import logging

# Load environment variables
load_dotenv()

from masking import extract_pii, mask_pii


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PII Masking API",
    description="API for masking Personal Identifiable Information in text with custom PII configurations",
    version="0.1.0",
)


@app.post(
    "/mask-pii",
    response_model=MaskResponse,
    summary="Mask PII in multiple texts",
    description="Analyzes multiple input texts and masks detected PII according to custom configuration",
)
async def mask_pii_endpoint(request: MaskRequest):
    """
    Endpoint to mask PII in provided texts with custom configuration.

    Args:
        request: MaskRequest object containing the list of input texts and PII config

    Returns:
        MaskResponse containing original texts, masked texts, and detected PII

    Raises:
        HTTPException: If processing fails or config is invalid
    """
    try:
        # Validate PII config
        if not request.pii_config:
            raise ValueError("PII configuration cannot be empty")

        # Validate input texts
        if not request.texts:
            raise ValueError("Input texts cannot be empty")

        if not all(isinstance(text, str) for text in request.texts):
            raise ValueError("All input texts must be strings")

        if not all(text.strip() for text in request.texts):
            raise ValueError("Input texts cannot be empty strings or whitespace only")

        # Create dynamic PII config class
        DynamicPIIConfig: Type[BaseModel] = create_dynamic_pii_config(
            request.pii_config
        )

        # Process each text
        masked_texts = []
        all_detected_pii = []

        for text in request.texts:
            # Extract PII using the dynamic config
            extracted_pii = extract_pii(text, DynamicPIIConfig)
            all_detected_pii.append(extracted_pii)

            # Mask the text
            masked_text = mask_pii(text, extracted_pii, DynamicPIIConfig)
            masked_texts.append(masked_text)

        # Log the operation
        logger.info(
            f"Processed {len(request.texts)} texts with {len(request.pii_config)} PII types. "
            f"Detected {sum(len(pii) for pii in all_detected_pii)} total PII items"
        )

        return MaskResponse(
            original_texts=request.texts,
            masked_texts=masked_texts,
            detected_pii=all_detected_pii,
        )

    except ValidationError as e:
        logger.error(f"Invalid PII configuration: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Invalid PII configuration: {str(e)}"
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health", summary="Health check endpoint")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import argparse
    import uvicorn

    # Create argument parser
    parser = argparse.ArgumentParser(description="Run Uvicorn server")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8081, help="Port to bind (default: 8081)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Run Uvicorn with parsed arguments
    uvicorn.run(app, host=args.host, port=args.port)
