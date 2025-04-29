# examples/01_create_namespace.py

import os
import sys
import json
import logging # Import logging module
from moorcheh_sdk import (
    MoorchehClient,
    MoorchehError,
    AuthenticationError,
    InvalidInputError,
    ConflictError,
    APIError,
)

# --- Configure Logging ---
# Set up basic configuration for logging
# This will capture logs from this script and the moorcheh_sdk
logging.basicConfig(
    level=logging.INFO, # Set the minimum level to capture (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Get a logger for this specific script
logger = logging.getLogger(__name__)
# -------------------------

def main():
    """
    Example script to create a Moorcheh namespace using the SDK, with logging.
    """
    logger.info("--- Moorcheh SDK: Create Namespace Example ---")

    # 1. Initialize the Client
    # The client reads the API key from the MOORCHEH_API_KEY environment variable
    try:
        # You can optionally pass base_url="YOUR_STAGING_URL" if needed
        # The client initialization will also log its base URL (at INFO level)
        client = MoorchehClient()
        logger.info("Client initialized successfully.")
    except AuthenticationError as e:
        logger.error(f"Authentication Error: {e}")
        logger.error("Please ensure the MOORCHEH_API_KEY environment variable is set correctly.")
        sys.exit(1) # Exit if client cannot be initialized
    except MoorchehError as e:
        logger.error(f"Error initializing client: {e}", exc_info=True) # Log full traceback
        sys.exit(1)

    # 2. Define Namespace Parameters
    # --- Choose a unique name and type for your test ---
    namespace_to_create = "sdk-test-text-ns-01"
    namespace_type = "text" # "text" or "vector"
    vector_dimension = None # Set to integer (e.g., 10) if type is "vector", otherwise None
    # ----------------------------------------------------

    logger.info("Attempting to create namespace:")
    logger.info(f"  Name: {namespace_to_create}")
    logger.info(f"  Type: {namespace_type}")
    if vector_dimension:
        logger.info(f"  Dimension: {vector_dimension}")

    # 3. Call the create_namespace method
    try:
        # Use the client's context manager for automatic cleanup
        with client:
            # SDK method call will produce its own logs (e.g., request details at DEBUG)
            response = client.create_namespace(
                namespace_name=namespace_to_create,
                type=namespace_type,
                vector_dimension=vector_dimension
            )
            logger.info("--- API Response ---")
            # Use json.dumps for pretty printing the response dict in the log
            logger.info(json.dumps(response, indent=2))
            logger.info("--------------------")
            # Use f-string for cleaner log message construction
            logger.info(f"Successfully created namespace '{response.get('namespace_name')}'! ✅")

    # 4. Handle Specific Errors using logger.error or logger.exception
    except ConflictError as e:
        logger.error(f"Namespace '{namespace_to_create}' already exists.")
        logger.error(f"API Message: {e}")
    except InvalidInputError as e:
        logger.error("Invalid input provided for namespace creation.")
        logger.error(f"API Message: {e}")
    except AuthenticationError as e: # Should be caught by init, but good practice
        logger.error("Authentication failed during namespace creation.")
        logger.error(f"API Message: {e}")
    except APIError as e:
        # Log the full traceback for unexpected API errors
        logger.exception("An API error occurred during namespace creation.")
    except MoorchehError as e: # Catch base SDK or network errors
        # Log the full traceback for SDK/network errors
        logger.exception("An SDK or network error occurred.")
    except Exception as e: # Catch any other unexpected errors
        # Log the full traceback for any other errors
        logger.exception("An unexpected error occurred.")

if __name__ == "__main__":
    main()
