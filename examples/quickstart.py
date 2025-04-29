# examples/quickstart.py

import os
import sys
import json
import random # For generating example vectors
import time   # For adding a short delay
import logging # Import logging module
from moorcheh_sdk import (
    MoorchehClient,
    MoorchehError,
    AuthenticationError,
    InvalidInputError,
    NamespaceNotFound,
    ConflictError,
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

def run_quickstart():
    """
    Demonstrates the basic workflow of the Moorcheh Python SDK with logging:
    1. Initialize Client
    2. Create Text & Vector Namespaces
    3. List Namespaces
    4. Upload Documents (Text)
    5. Upload Vectors (Vector)
    6. Search Text Namespace
    7. Search Vector Namespace
    8. Delete specific items
    9. Optionally delete namespaces (commented out by default)
    """
    logger.info("--- Moorcheh SDK Quick Start ---")

    try:
        # 1. Initialize Client
        # Reads MOORCHEH_API_KEY from environment variables
        # Reads MOORCHEH_BASE_URL from environment or uses default
        # Client initialization will log its base URL (at INFO level)
        client = MoorchehClient()
        logger.info(f"Client initialized. Targeting base URL: {client.base_url}")

        # Use client as a context manager for automatic cleanup
        with client:
            # --- Define Namespaces and Parameters ---
            text_ns_name = "sdk-quickstart-text"
            vector_ns_name = "sdk-quickstart-vector"
            vector_dim = 10 # Keep dimension small for example

            # --- 1. Create Namespaces ---
            try:
                logger.info(f"[Step 1a] Creating text namespace: '{text_ns_name}'")
                creation_response_text = client.create_namespace(
                    namespace_name=text_ns_name,
                    type="text"
                )
                logger.info(f"Text Namespace creation response: {json.dumps(creation_response_text, indent=2)}")
            except ConflictError:
                logger.warning(f"Text Namespace '{text_ns_name}' already exists.")
            except Exception as e:
                logger.error(f"Failed to create text namespace: {e}", exc_info=True)
                # Decide if we should exit or continue if creation fails
                # sys.exit(1)

            try:
                logger.info(f"[Step 1b] Creating vector namespace: '{vector_ns_name}' (Dim: {vector_dim})")
                creation_response_vector = client.create_namespace(
                    namespace_name=vector_ns_name,
                    type="vector",
                    vector_dimension=vector_dim
                )
                logger.info(f"Vector Namespace creation response: {json.dumps(creation_response_vector, indent=2)}")
            except ConflictError:
                logger.warning(f"Vector Namespace '{vector_ns_name}' already exists.")
            except Exception as e:
                logger.error(f"Failed to create vector namespace: {e}", exc_info=True)
                # sys.exit(1)


            # --- 2. List Namespaces ---
            logger.info("[Step 2] Listing namespaces...")
            try:
                namespaces_response = client.list_namespaces()
                logger.info("Current Namespaces:")
                logger.info(json.dumps(namespaces_response.get('namespaces', []), indent=2))
            except Exception as e:
                 logger.error(f"Failed to list namespaces: {e}", exc_info=True)


            # --- 3. Upload Documents (to text namespace) ---
            logger.info(f"[Step 3] Uploading documents to '{text_ns_name}'...")
            docs_to_upload = [
                {"id": "qs-doc-1", "text": "Moorcheh uses information theory principles for search.", "source": "quickstart", "topic": "core_concept"},
                {"id": "qs-doc-2", "text": "The Python SDK simplifies API interactions.", "source": "quickstart", "topic": "sdk"},
                {"id": "qs-doc-3", "text": "Text data is embedded automatically by the service.", "source": "quickstart", "topic": "ingestion"},
            ]
            try:
                upload_doc_res = client.upload_documents(namespace_name=text_ns_name, documents=docs_to_upload)
                logger.info(f"Upload documents response (queued): {json.dumps(upload_doc_res, indent=2)}")
            except (NamespaceNotFound, InvalidInputError) as e:
                 logger.error(f"Could not upload documents to '{text_ns_name}': {e}")
            except Exception as e:
                 logger.error(f"An unexpected error occurred during document upload: {e}", exc_info=True)


            # --- 4. Upload Vectors (to vector namespace) ---
            logger.info(f"[Step 4] Uploading vectors to '{vector_ns_name}'...")
            vectors_to_upload = []
            num_vectors = 5
            for i in range(num_vectors):
                vec_id = f"qs-vec-{i+1}"
                random_vector = [random.uniform(-1.0, 1.0) for _ in range(vector_dim)] # Generate random vector
                vectors_to_upload.append({
                    "id": vec_id,
                    "vector": random_vector,
                    "metadata": {"source": "quickstart_random", "index": i, "type": "random"}
                })
            try:
                upload_vec_res = client.upload_vectors(namespace_name=vector_ns_name, vectors=vectors_to_upload)
                logger.info(f"Upload vectors response (processed): {json.dumps(upload_vec_res, indent=2)}")
            except (NamespaceNotFound, InvalidInputError) as e:
                 logger.error(f"Could not upload vectors to '{vector_ns_name}': {e}")
            except Exception as e:
                 logger.error(f"An unexpected error occurred during vector upload: {e}", exc_info=True)


            # --- Allow time for async text processing ---
            # This is important before searching the text namespace
            processing_wait_time = 1 # seconds
            logger.info(f"Waiting {processing_wait_time} seconds for text processing...")
            time.sleep(processing_wait_time)


            # --- 5. Search Text Namespace ---
            logger.info(f"[Step 5] Searching text namespace '{text_ns_name}' for 'API interaction'")
            try:
                text_search_res = client.search(
                    namespaces=[text_ns_name],
                    query="API interaction", # Text query
                    top_k=2
                )
                logger.info("Text search results:")
                logger.info(json.dumps(text_search_res, indent=2))
            except (NamespaceNotFound, InvalidInputError) as e:
                 logger.error(f"Could not search text namespace '{text_ns_name}': {e}")
            except Exception as e:
                 logger.error(f"An unexpected error occurred during text search: {e}", exc_info=True)


            # --- 6. Search Vector Namespace ---
            logger.info(f"[Step 6] Searching vector namespace '{vector_ns_name}' with a random vector")
            try:
                # Generate a new random query vector
                query_vector = [random.uniform(-1.0, 1.0) for _ in range(vector_dim)]
                vector_search_res = client.search(
                    namespaces=[vector_ns_name],
                    query=query_vector, # Vector query
                    top_k=2
                )
                logger.info("Vector search results:")
                logger.info(json.dumps(vector_search_res, indent=2))
            except (NamespaceNotFound, InvalidInputError) as e:
                 logger.error(f"Could not search vector namespace '{vector_ns_name}': {e}")
            except Exception as e:
                 logger.error(f"An unexpected error occurred during vector search: {e}", exc_info=True)


            # --- 7. Delete Items ---
            doc_id_to_delete = "qs-doc-2"
            logger.info(f"[Step 7a] Deleting document '{doc_id_to_delete}' from '{text_ns_name}'...")
            try:
                del_doc_res = client.delete_documents(namespace_name=text_ns_name, ids=[doc_id_to_delete])
                logger.info(f"Delete document response: {json.dumps(del_doc_res, indent=2)}")
            except (NamespaceNotFound, InvalidInputError) as e:
                 logger.error(f"Could not delete document '{doc_id_to_delete}': {e}")
            except Exception as e:
                 logger.error(f"An unexpected error occurred during document deletion: {e}", exc_info=True)

            vec_id_to_delete = "qs-vec-3"
            logger.info(f"[Step 7b] Deleting vector '{vec_id_to_delete}' from '{vector_ns_name}'...")
            try:
                del_vec_res = client.delete_vectors(namespace_name=vector_ns_name, ids=[vec_id_to_delete])
                logger.info(f"Delete vector response: {json.dumps(del_vec_res, indent=2)}")
            except (NamespaceNotFound, InvalidInputError) as e:
                 logger.error(f"Could not delete vector '{vec_id_to_delete}': {e}")
            except Exception as e:
                 logger.error(f"An unexpected error occurred during vector deletion: {e}", exc_info=True)


            # --- 8. Cleanup: Delete Namespaces (Optional - uncomment to run) ---
            # logger.info(f"[Step 8 - Cleanup] Deleting namespace: {text_ns_name}")
            # try:
            #     client.delete_namespace(text_ns_name)
            # except NamespaceNotFound:
            #     logger.warning(f"Namespace '{text_ns_name}' likely already deleted or never created.")
            # except Exception as e:
            #      logger.error(f"Error deleting '{text_ns_name}': {e}", exc_info=True)

            # logger.info(f"[Step 8 - Cleanup] Deleting namespace: {vector_ns_name}")
            # try:
            #     client.delete_namespace(vector_ns_name)
            # except NamespaceNotFound:
            #     logger.warning(f"Namespace '{vector_ns_name}' likely already deleted or never created.")
            # except Exception as e:
            #      logger.error(f"Error deleting '{vector_ns_name}': {e}", exc_info=True)

            # logger.info("Cleanup complete (if uncommented).")


    # --- Global Error Handling ---
    except (AuthenticationError, InvalidInputError, NamespaceNotFound, ConflictError, APIError, MoorchehError) as e:
        # Log specific SDK/API errors with their type and details
        logger.error(f"An SDK or API error occurred during the quick start:")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Details: {e}")
    except Exception as e:
        # Use logger.exception for unexpected Python errors to get the full traceback
        logger.exception("An unexpected Python error occurred during the quick start:")

if __name__ == "__main__":
    run_quickstart()
