# examples/10_list_files.py

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
    Example: list raw file objects in document storage for a namespace (GET
    list-files). This is storage listing (e.g. after upload_file), not indexed
    documents by ID — use documents.get or fetch_text_data for pipeline data.
    """
    logger.info("--- Moorcheh SDK: List Files Example ---")

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

    target_namespace = "test-documents"  # Change this to your namespace name

    logger.info(f"Target namespace: {target_namespace}")

    try:
        with client:
            logger.info(f"Listing files in namespace '{target_namespace}'...")
            response = client.documents.list_files(namespace_name=target_namespace)

            logger.info("--- API Response (200 OK) ---")
            logger.info(json.dumps(response, indent=2))
            logger.info("-------------------------------")

            if response.get("success"):
                count = response.get("file_count", 0)
                files = response.get("files") or []
                logger.info(f"✅ Listed {count} file object(s).")
                for f in files:
                    logger.info(
                        "  %s | %s bytes | %s",
                        f.get("file_name"),
                        f.get("size"),
                        f.get("last_modified"),
                    )
            else:
                logger.warning(
                    f"Unexpected response: success={response.get('success')!r}"
                )

    except NamespaceNotFound:
        logger.error(f"Namespace '{target_namespace}' was not found.")
        logger.info(
            "Create a namespace first (see examples/01_create_namespace.py) "
            "and upload a file (examples/07_upload_file.py)."
        )
    except InvalidInputError as e:
        logger.error(f"Invalid input: {e}")
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
    except APIError:
        logger.exception("An API error occurred.")
    except MoorchehError:
        logger.exception("An SDK or network error occurred.")
    except Exception:
        logger.exception("An unexpected error occurred.")


if __name__ == "__main__":
    main()
