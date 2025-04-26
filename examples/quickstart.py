# examples/quick_start.py

import os
import sys
import json
import random # For generating example vectors
import time   # For adding a short delay
from moorcheh_sdk import (
    MoorchehClient,
    MoorchehError,
    AuthenticationError,
    InvalidInputError,
    NamespaceNotFound,
    ConflictError,
    APIError,
)

def run_quickstart():
    """
    Demonstrates the basic workflow of the Moorcheh Python SDK:
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
    print("--- Moorcheh SDK Quick Start ---")

    try:
        # 1. Initialize Client
        # Reads MOORCHEH_API_KEY from environment variables
        # Reads MOORCHEH_BASE_URL from environment or uses default
        client = MoorchehClient()
        print(f"Client initialized. Targeting base URL: {client.base_url}")

        # Use client as a context manager for automatic cleanup
        with client:
            # --- Define Namespaces and Parameters ---
            text_ns_name = "sdk-quickstart-text"
            vector_ns_name = "sdk-quickstart-vector"
            vector_dim = 10 # Keep dimension small for example

            # --- 1. Create Namespaces ---
            try:
                print(f"\n[Step 1a] Creating text namespace: '{text_ns_name}'")
                creation_response_text = client.create_namespace(
                    namespace_name=text_ns_name,
                    type="text"
                )
                print(f"Text Namespace creation response: {creation_response_text}")
            except ConflictError:
                print(f"Text Namespace '{text_ns_name}' already exists.")
            except Exception as e:
                print(f"Failed to create text namespace: {e}")
                # Decide if we should exit or continue if creation fails
                # sys.exit(1)

            try:
                print(f"\n[Step 1b] Creating vector namespace: '{vector_ns_name}' (Dim: {vector_dim})")
                creation_response_vector = client.create_namespace(
                    namespace_name=vector_ns_name,
                    type="vector",
                    vector_dimension=vector_dim
                )
                print(f"Vector Namespace creation response: {creation_response_vector}")
            except ConflictError:
                print(f"Vector Namespace '{vector_ns_name}' already exists.")
            except Exception as e:
                print(f"Failed to create vector namespace: {e}")
                # sys.exit(1)


            # --- 2. List Namespaces ---
            print("\n[Step 2] Listing namespaces...")
            namespaces_response = client.list_namespaces()
            print("Current Namespaces:")
            print(json.dumps(namespaces_response.get('namespaces', []), indent=2))


            # --- 3. Upload Documents (to text namespace) ---
            print(f"\n[Step 3] Uploading documents to '{text_ns_name}'...")
            docs_to_upload = [
                {"id": "qs-doc-1", "text": "Moorcheh uses information theory principles for search.", "source": "quickstart", "topic": "core_concept"},
                {"id": "qs-doc-2", "text": "The Python SDK simplifies API interactions.", "source": "quickstart", "topic": "sdk"},
                {"id": "qs-doc-3", "text": "Text data is embedded automatically by the service.", "source": "quickstart", "topic": "ingestion"},
            ]
            try:
                upload_doc_res = client.upload_documents(namespace_name=text_ns_name, documents=docs_to_upload)
                print("Upload documents response (queued):", upload_doc_res)
            except (NamespaceNotFound, InvalidInputError) as e:
                 print(f"Could not upload documents to '{text_ns_name}': {e}")


            # --- 4. Upload Vectors (to vector namespace) ---
            print(f"\n[Step 4] Uploading vectors to '{vector_ns_name}'...")
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
                print("Upload vectors response (processed):", upload_vec_res)
            except (NamespaceNotFound, InvalidInputError) as e:
                 print(f"Could not upload vectors to '{vector_ns_name}': {e}")


            # --- Allow time for async text processing ---
            # This is important before searching the text namespace
            processing_wait_time = 1 # seconds
            print(f"\nWaiting {processing_wait_time} seconds for text processing...")
            time.sleep(processing_wait_time)


            # --- 5. Search Text Namespace ---
            print(f"\n[Step 5] Searching text namespace '{text_ns_name}' for 'API interaction'")
            try:
                text_search_res = client.search(
                    namespaces=[text_ns_name],
                    query="API interaction", # Text query
                    top_k=2
                )
                print("Text search results:")
                print(json.dumps(text_search_res, indent=2))
            except (NamespaceNotFound, InvalidInputError) as e:
                 print(f"Could not search text namespace '{text_ns_name}': {e}")


            # --- 6. Search Vector Namespace ---
            print(f"\n[Step 6] Searching vector namespace '{vector_ns_name}' with a random vector")
            try:
                # Generate a new random query vector
                query_vector = [random.uniform(-1.0, 1.0) for _ in range(vector_dim)]
                vector_search_res = client.search(
                    namespaces=[vector_ns_name],
                    query=query_vector, # Vector query
                    top_k=2
                )
                print("Vector search results:")
                print(json.dumps(vector_search_res, indent=2))
            except (NamespaceNotFound, InvalidInputError) as e:
                 print(f"Could not search vector namespace '{vector_ns_name}': {e}")


            # --- 7. Delete Items ---
            doc_id_to_delete = "qs-doc-2"
            print(f"\n[Step 7a] Deleting document '{doc_id_to_delete}' from '{text_ns_name}'...")
            try:
                del_doc_res = client.delete_documents(namespace_name=text_ns_name, ids=[doc_id_to_delete])
                print("Delete document response:", del_doc_res)
            except (NamespaceNotFound, InvalidInputError) as e:
                 print(f"Could not delete document '{doc_id_to_delete}': {e}")

            vec_id_to_delete = "qs-vec-3"
            print(f"\n[Step 7b] Deleting vector '{vec_id_to_delete}' from '{vector_ns_name}'...")
            try:
                del_vec_res = client.delete_vectors(namespace_name=vector_ns_name, ids=[vec_id_to_delete])
                print("Delete vector response:", del_vec_res)
            except (NamespaceNotFound, InvalidInputError) as e:
                 print(f"Could not delete vector '{vec_id_to_delete}': {e}")


            # --- 8. Cleanup: Delete Namespaces (Optional - uncomment to run) ---
            # print(f"\n[Step 8 - Cleanup] Deleting namespace: {text_ns_name}")
            # try:
            #     client.delete_namespace(text_ns_name)
            # except NamespaceNotFound:
            #     print(f"Namespace '{text_ns_name}' likely already deleted.")
            # except Exception as e:
            #      print(f"Error deleting '{text_ns_name}': {e}")

            # print(f"\n[Step 8 - Cleanup] Deleting namespace: {vector_ns_name}")
            # try:
            #     client.delete_namespace(vector_ns_name)
            # except NamespaceNotFound:
            #     print(f"Namespace '{vector_ns_name}' likely already deleted.")
            # except Exception as e:
            #      print(f"Error deleting '{vector_ns_name}': {e}")

            # print("\nCleanup complete.")


    # --- Global Error Handling ---
    except (AuthenticationError, InvalidInputError, NamespaceNotFound, ConflictError, APIError, MoorchehError) as e:
        print(f"\nAn SDK or API error occurred during the quick start:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Details: {e}")
    except Exception as e:
        print(f"\nAn unexpected Python error occurred: {e}")
        import traceback
        traceback.print_exc() # Print full stack trace for unexpected errors

if __name__ == "__main__":
    run_quickstart()
