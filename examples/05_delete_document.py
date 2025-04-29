# examples/05_delete_document.py

import os
import sys
import json
import logging # Import logging module
from moorcheh_sdk import (
    MoorchehClient,
    MoorchehError,
    AuthenticationError,
    InvalidInputError,
    NamespaceNotFound,
    APIError,
)

# --- Configure Logging ---
# Set up basic configuration for logging
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
    Example script to delete a single document chunk from a text namespace using the SDK, with logging.
    """
    logger.info("--- Moorcheh SDK: Delete Document Example ---")

    # 1. Initialize the Client
    try:
        # Client initialization will log its base URL (at INFO level)
        client = MoorchehClient()
        logger.info("Client initialized successfully.")
    except AuthenticationError as e:
        logger.error(f"Authentication Error: {e}")
        logger.error("Please ensure the MOORCHEH_API_KEY environment variable is set correctly.")
        sys.exit(1)
    except MoorchehError as e:
        logger.error(f"Error initializing client: {e}", exc_info=True) # Log full traceback
        sys.exit(1)

    # 2. Define Target Namespace and Document ID to Delete
    # --- Use the namespace you uploaded documents to ---
    target_namespace = "sdk-test-text-ns-01"
    # --- Specify the ID of the document chunk you want to remove ---
    document_id_to_delete = "sdk-doc-001" # Example ID from previous upload
    # ----------------------------------------------------

    logger.info(f"Attempting to delete document ID '{document_id_to_delete}' from namespace: '{target_namespace}'")

    # 3. Call the delete_documents method
    #    Note: The method expects a LIST of IDs, even if deleting only one.
    try:
        with client:
            # SDK method call will produce its own logs
            response = client.delete_documents(
                namespace_name=target_namespace,
                ids=[document_id_to_delete] # Pass the ID inside a list
            )
            logger.info("--- API Response (Should be 200 OK or 207 Multi-Status) ---")
            # Use json.dumps for pretty printing the response dict in the log
            logger.info(json.dumps(response, indent=2))
            logger.info("-----------------------------------------------------------")

            if response and response.get('status') == 'success':
                 # Check if the specific ID is in the returned list (optional validation)
                 if document_id_to_delete in response.get('deleted_ids', []):
                     logger.info(f"Successfully processed deletion request for document ID '{document_id_to_delete}'. ✅")
                 else:
                     # This case might happen if the ID didn't exist but the call succeeded
                     logger.warning(f"Deletion request processed, but ID '{document_id_to_delete}' might not have been present.")
            elif response and response.get('status') == 'partial':
                 logger.warning("Deletion request partially completed. Check response details.")
            else:
                 logger.warning(f"Deletion request sent, but status was not 'success' or 'partial'. Status: {response.get('status')}. Check response details.")


    # 4. Handle Specific Errors using logger.error or logger.exception
    except NamespaceNotFound as e:
         logger.error(f"Namespace '{target_namespace}' not found.")
         logger.error(f"API Message: {e}")
    except InvalidInputError as e:
        logger.error("Invalid input provided for document deletion.")
        logger.error(f"API Message: {e}")
    except AuthenticationError as e:
        logger.error("Authentication failed during document deletion.")
        logger.error(f"API Message: {e}")
    except APIError as e:
        # Log the full traceback for unexpected API errors
        logger.exception("An API error occurred during document deletion.")
    except MoorchehError as e: # Catch base SDK or network errors
        # Log the full traceback for SDK/network errors
        logger.exception("An SDK or network error occurred.")
    except Exception as e: # Catch any other unexpected errors
        # Log the full traceback for any other errors
        logger.exception("An unexpected error occurred.")

if __name__ == "__main__":
    main()
