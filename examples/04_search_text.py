# examples/04_search_text.py

import json
import logging  # Import logging module
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
# Set up basic configuration for logging
logging.basicConfig(
    level=logging.INFO,  # Set the minimum level to capture (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Get a logger for this specific script
logger = logging.getLogger(__name__)
# -------------------------


def main():
    """
    Example script to perform a text search in a namespace using the SDK, with logging.
    """
    logger.info("--- Moorcheh SDK: Text Search Example ---")

    # 1. Initialize the Client
    try:
        # Client initialization will log its base URL (at INFO level)
        client = MoorchehClient()
        logger.info("Client initialized successfully.")
    except AuthenticationError as e:
        logger.error(f"Authentication Error: {e}")
        logger.error(
            "Please ensure the MOORCHEH_API_KEY environment variable is set correctly."
        )
        sys.exit(1)
    except MoorchehError as e:
        logger.error(
            f"Error initializing client: {e}", exc_info=True
        )  # Log full traceback
        sys.exit(1)

    # 2. Define Search Parameters
    # --- Use the namespace you uploaded text documents to ---
    target_namespace = "sdk-test-text-ns-01"
    search_query = "API interaction"  # The text query
    top_k_results = 2  # How many top results to fetch
    score_threshold = 0.001  # Optional minimum score (0-1)
    # ----------------------------------------------------

    logger.info(f"Attempting to search namespace(s): '{target_namespace}'")
    logger.info(f"  Query: '{search_query}'")
    logger.info(f"  Top K: {top_k_results}")
    if score_threshold is not None:
        logger.info(f"  Threshold: {score_threshold}")

    # 3. Call the search method
    try:
        # Use the client's context manager
        with client:
            # SDK method call will produce its own logs
            response = client.search(
                namespaces=[target_namespace],  # Pass namespace(s) as a list
                query=search_query,  # Pass the text query string
                top_k=top_k_results,
                threshold=score_threshold,
                # kiosk_mode=False # Default is false
            )
            logger.info("--- API Response (Search Results) ---")
            # Use json.dumps for pretty printing the response dict in the log
            logger.info(json.dumps(response, indent=2))
            logger.info("-------------------------------------")

            if response and "results" in response:
                result_count = len(response["results"])
                logger.info(
                    f"Search completed successfully. Found {result_count} result(s). ✅"
                )
            else:
                logger.warning(
                    "Search completed, but response format might be unexpected or missing 'results'."
                )

    # 4. Handle Specific Errors using logger.error or logger.exception
    except NamespaceNotFound as e:
        # Log specific error for namespace not found
        logger.error(f"Namespace '{target_namespace}' not found or not accessible.")
        logger.error(f"API Message: {e}")
    except InvalidInputError as e:
        logger.error("Invalid input provided for search.")
        logger.error(f"API Message: {e}")
    except AuthenticationError as e:
        logger.error("Authentication failed during search.")
        logger.error(f"API Message: {e}")
    except APIError:
        # Log the full traceback for unexpected API errors
        logger.exception("An API error occurred during search.")
    except MoorchehError:  # Catch base SDK or network errors
        # Log the full traceback for SDK/network errors
        logger.exception("An SDK or network error occurred.")
    except Exception:  # Catch any other unexpected errors
        # Log the full traceback for any other errors
        logger.exception("An unexpected error occurred.")


if __name__ == "__main__":
    main()
