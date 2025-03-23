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
    summary="Mask PII in text",
    description="Analyzes the input text and masks detected PII according to custom configuration",
)
async def mask_pii_endpoint(request: MaskRequest):
    """
    Endpoint to mask PII in provided text with custom configuration.

    Args:
        request: MaskRequest object containing the input text and PII config

    Returns:
        MaskResponse containing original text, masked text, and detected PII

    Raises:
        HTTPException: If processing fails or config is invalid
    """
    try:
        # Validate PII config
        if not request.pii_config:
            raise ValueError("PII configuration cannot be empty")

        # Create dynamic PII config class
        DynamicPIIConfig: Type[BaseModel] = create_dynamic_pii_config(
            request.pii_config
        )

        # Extract PII using the dynamic config
        extracted_pii = extract_pii(request.text, DynamicPIIConfig)

        # Mask the text
        masked_text = mask_pii(request.text, extracted_pii, DynamicPIIConfig)

        # Log the operation
        logger.info(
            f"Processed text with {len(request.pii_config)} PII types. "
            f"Detected {len(extracted_pii)} PII items"
        )

        return MaskResponse(
            original_text=request.text,
            masked_text=masked_text,
            detected_pii=extracted_pii,
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
