# examples/07_upload_file.py

import json
import logging
import sys
from pathlib import Path

from moorcheh_sdk import (
    APIError,
    AuthenticationError,
    InvalidInputError,
    MoorchehClient,
    MoorchehError,
    NamespaceNotFound,
)

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
# -------------------------


def create_test_file(
    file_path: Path, content: str = "This is a test document."
) -> None:
    """Create a test file if it doesn't exist."""
    if not file_path.exists():
        file_path.write_text(content)
        logger.info(f"Created test file: {file_path}")
    else:
        logger.info(f"Test file already exists: {file_path}")


def main():
    """
    Example script to upload a file to a text namespace using the SDK.
    """
    logger.info("--- Moorcheh SDK: Upload File Example ---")

    # 1. Initialize the Client
    try:
        client = MoorchehClient()
        logger.info("Client initialized successfully.")
    except AuthenticationError as e:
        logger.error(f"Authentication Error: {e}")
        logger.error(
            "Please ensure the MOORCHEH_API_KEY environment variable is set correctly."
        )
        sys.exit(1)
    except MoorchehError as e:
        logger.error(f"Error initializing client: {e}", exc_info=True)
        sys.exit(1)

    # 2. Configuration
    target_namespace = "test-documents"  # Change this to your namespace name
    test_file_path = Path("test_document.txt")  # Change this to your file path

    logger.info(f"Target namespace: {target_namespace}")
    logger.info(f"File to upload: {test_file_path}")

    # 3. Create a test file if it doesn't exist (for testing purposes)
    if not test_file_path.exists():
        logger.info("Creating a test file for demonstration...")
        create_test_file(test_file_path, "This is a test document for file upload.")

    # 4. Upload the file
    try:
        with client:
            logger.info(
                f"Uploading file '{test_file_path}' to namespace '{target_namespace}'..."
            )
            response = client.documents.upload_file(
                namespace_name=target_namespace,
                file_path=test_file_path,
            )

            logger.info("--- API Response (200 OK) ---")
            logger.info(json.dumps(response, indent=2))
            logger.info("--------------------------------------------")

            if response.get("success"):
                logger.info("✅ File uploaded successfully!")
                logger.info(f"   File: {response.get('fileName')}")
                logger.info(f"   Size: {response.get('fileSize')} bytes")
                logger.info(f"   Namespace: {response.get('namespace')}")
            else:
                logger.warning(
                    f"Upload request sent, but success was not True. Response: {response}"
                )

    # 5. Handle Specific Errors
    except NamespaceNotFound as e:
        logger.error(f"Namespace '{target_namespace}' not found.")
        logger.error(f"API Message: {e}")
        logger.info(
            "💡 Tip: Create the namespace first using the create namespace example."
        )
    except InvalidInputError as e:
        logger.error("Invalid input provided for file upload.")
        logger.error(f"API Message: {e}")
        logger.info("💡 Tip: Check that:")
        logger.info("   - The file exists")
        logger.info(
            "   - The file type is supported (.pdf, .docx, .xlsx, .json, .txt, .csv, .md)"
        )
        logger.info("   - The file size is less than 10MB")
    except AuthenticationError as e:
        logger.error("Authentication failed during file upload.")
        logger.error(f"API Message: {e}")
    except APIError:
        logger.exception("An API error occurred during file upload.")
    except MoorchehError:
        logger.exception("An SDK or network error occurred.")
    except Exception:
        logger.exception("An unexpected error occurred.")


if __name__ == "__main__":
    main()
