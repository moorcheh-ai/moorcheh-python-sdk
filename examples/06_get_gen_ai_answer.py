# examples/06_get_gen_ai_answer.py

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
# Set up basic configuration for logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Get a logger for this specific script
logger = logging.getLogger(__name__)
# -------------------------


def main():
    """
    Example script to get a generative AI answer from a namespace using the SDK.
    """
    logger.info("--- Moorcheh SDK: Generative AI Answer Example ---")

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

    # 2. Define Parameters
    # --- Use the text namespace you have already uploaded documents to ---
    target_namespace = "sdk-test-text-ns-01"
    query = "What is the Moorcheh Python SDK used for?"
    top_k_context = 3  # Number of documents to use as context
    # ----------------------------------------------------

    logger.info(
        f"Attempting to get a generative answer from namespace: '{target_namespace}'"
    )
    logger.info(f"  Query: '{query}'")
    logger.info(f"  Context (top_k): {top_k_context}")

    # 3. Call the get_generative_answer method
    try:
        # Use the client's context manager
        with client:
            # SDK method call will produce its own logs
            response = client.get_generative_answer(
                namespace=target_namespace, query=query, top_k=top_k_context
            )
            logger.info("--- API Response (Generative Answer) ---")
            # Use json.dumps for pretty printing the response dict in the log
            logger.info(json.dumps(response, indent=2))
            logger.info("----------------------------------------")

            if response and "answer" in response:
                logger.info("Successfully received a generative answer! ✅")
                # Log the answer itself for easy viewing
                print("\n--- Generated Answer ---")
                print(response["answer"])
                print("------------------------\n")
            else:
                logger.warning(
                    "Request completed, but response format might be unexpected or"
                    " missing 'answer'."
                )

    # 4. Handle Specific Errors using logger.error or logger.exception
    except NamespaceNotFound as e:
        # This might be raised if the target namespace doesn't exist
        logger.error(f"Namespace '{target_namespace}' not found or not accessible.")
        logger.error(f"API Message: {e}")
    except InvalidInputError as e:
        logger.error("Invalid input provided for the generative answer request.")
        logger.error(f"API Message: {e}")
    except AuthenticationError as e:
        logger.error("Authentication failed while requesting the generative answer.")
        logger.error(f"API Message: {e}")
    except APIError:
        # Log the full traceback for unexpected API errors (e.g., 5xx from server)
        logger.exception("An API error occurred while getting the generative answer.")
    except MoorchehError:  # Catch base SDK or network errors
        logger.exception("An SDK or network error occurred.")
    except Exception:  # Catch any other unexpected errors
        logger.exception("An unexpected error occurred.")


if __name__ == "__main__":
    main()
