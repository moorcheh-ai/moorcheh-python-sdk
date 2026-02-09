# examples/08_delete_file.py

import json
import logging
import sys

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


def main():
    """
    Example script to delete one or more files from a text namespace using the SDK.
    """
    logger.info("--- Moorcheh SDK: Delete File Example ---")

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
    file_names_to_delete = [
        "test_document.txt",  # Example file name from the upload example
    ]

    logger.info(f"Target namespace: {target_namespace}")
    logger.info(f"Files to delete: {file_names_to_delete}")

    # 3. Delete the file(s)
    #    Note: The method expects a LIST of file names, even if deleting only one.
    try:
        with client:
            logger.info(
                "Deleting files from namespace '%s'...",
                target_namespace,
            )
            response = client.documents.delete_files(
                namespace_name=target_namespace,
                file_names=file_names_to_delete,
            )

            logger.info("--- API Response (200 OK or 207 Multi-Status) ---")
            logger.info(json.dumps(response, indent=2))
            logger.info("------------------------------------------------")

            if response and response.get("status") == "success":
                logger.info("Deletion request processed. ✅")
                for result in response.get("results", []):
                    logger.info(
                        "File '%s' -> %s (%s)",
                        result.get("fileName"),
                        result.get("status"),
                        result.get("message"),
                    )
            elif response and response.get("status") == "partial":
                logger.warning(
                    "Deletion request partially completed. Check response details."
                )
            else:
                logger.warning(
                    "Deletion request sent, but status was not 'success' or 'partial'."
                    f" Status: {response.get('status')}. Check response details."
                )

    # 4. Handle Specific Errors
    except NamespaceNotFound as e:
        logger.error(f"Namespace '{target_namespace}' not found.")
        logger.error(f"API Message: {e}")
        logger.info(
            "Tip: Create the namespace first using the create namespace example."
        )
    except InvalidInputError as e:
        logger.error("Invalid input provided for file deletion.")
        logger.error(f"API Message: {e}")
        logger.info("Tip: Ensure file names are non-empty strings.")
    except AuthenticationError as e:
        logger.error("Authentication failed during file deletion.")
        logger.error(f"API Message: {e}")
    except APIError:
        logger.exception("An API error occurred during file deletion.")
    except MoorchehError:
        logger.exception("An SDK or network error occurred.")
    except Exception:
        logger.exception("An unexpected error occurred.")


if __name__ == "__main__":
    main()
