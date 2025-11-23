# examples/02_list_namespaces.py

import json
import logging  # Import logging module
import sys

from moorcheh_sdk import (
    APIError,
    AuthenticationError,
    MoorchehClient,
    MoorchehError,
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
    Example script to list Moorcheh namespaces using the SDK, with logging.
    """
    logger.info("--- Moorcheh SDK: List Namespaces Example ---")

    # 1. Initialize the Client
    # Reads the API key from the MOORCHEH_API_KEY environment variable
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

    # 2. Call the list_namespaces method
    logger.info("Attempting to list namespaces...")
    try:
        # Use the client's context manager for automatic cleanup
        with client:
            # SDK method call will produce its own logs
            response = client.list_namespaces()  # Call the SDK method

            logger.info("--- API Response ---")
            # Use json.dumps for pretty printing the response dict in the log
            logger.info(json.dumps(response, indent=2))
            logger.info("--------------------")

            # Optional: Log a summary
            if response and "namespaces" in response:
                num_namespaces = len(response["namespaces"])
                logger.info(f"Successfully retrieved {num_namespaces} namespace(s). ✅")
                # Optionally iterate and log names at DEBUG level if needed
                # for ns in response['namespaces']:
                #     logger.debug(f" - {ns.get('namespace_name')} (Type: {ns.get('type')}, Items: {ns.get('itemCount')})")
            else:
                # Log a warning if the expected key is missing
                logger.warning(
                    "Received response, but 'namespaces' key was missing or empty."
                )

    # 3. Handle Specific Errors using logger.error or logger.exception
    except AuthenticationError as e:  # Should be caught by init, but good practice
        logger.error("Authentication failed during list namespaces.")
        logger.error(f"API Message: {e}")
    except APIError:
        # Log the full traceback for unexpected API errors
        logger.exception("An API error occurred during list namespaces.")
    except MoorchehError:  # Catch base SDK or network errors
        # Log the full traceback for SDK/network errors
        logger.exception("An SDK or network error occurred.")
    except Exception:  # Catch any other unexpected errors
        # Log the full traceback for any other errors
        logger.exception("An unexpected error occurred.")


if __name__ == "__main__":
    main()
