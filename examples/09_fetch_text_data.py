# examples/09_fetch_text_data.py

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
    Example: list stored text and summary chunks for a text namespace (GET
    fetch-text-data). Up to 100 items per response. For retrieving full
    documents by ID, use client.documents.get instead.
    """
    logger.info("--- Moorcheh SDK: Fetch Text Data Example ---")

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

    target_namespace = "sdk-test-text-ns-01"

    logger.info(f"Target namespace (must be type=text): {target_namespace}")

    try:
        with client:
            logger.info(f"Fetching text chunks from namespace '{target_namespace}'...")
            response = client.documents.fetch_text_data(
                namespace_name=target_namespace,
            )

            logger.info("--- API Response (200 OK) ---")
            logger.info(json.dumps(response, indent=2))
            logger.info("-------------------------------")

            if response.get("status") == "success":
                items = response.get("items") or []
                stats = response.get("statistics") or {}
                logger.info(
                    f"✅ Fetched {len(items)} item(s). "
                    f"statistics.total_items={stats.get('total_items')}"
                )
            else:
                logger.warning(
                    f"Unexpected status in response: {response.get('status')!r}"
                )

    except NamespaceNotFound:
        logger.error(f"Namespace '{target_namespace}' was not found.")
        logger.info(
            "Create a text namespace first (see examples/01_create_namespace.py) "
            "and upload data (examples/03_upload_documents.py)."
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
