# examples/05_delete_document.py

import os
import sys
import json
from moorcheh_sdk import (
    MoorchehClient,
    MoorchehError,
    AuthenticationError,
    InvalidInputError,
    NamespaceNotFound,
    APIError,
)

def main():
    """
    Example script to delete a single document chunk from a text namespace using the SDK.
    """
    print("--- Moorcheh SDK: Delete Document Example ---")

    # 1. Initialize the Client
    try:
        client = MoorchehClient()
        print("Client initialized successfully.")
    except AuthenticationError as e:
        print(f"Authentication Error: {e}")
        print("Please ensure the MOORCHEH_API_KEY environment variable is set correctly.")
        sys.exit(1)
    except MoorchehError as e:
        print(f"Error initializing client: {e}")
        sys.exit(1)

    # 2. Define Target Namespace and Document ID to Delete
    # --- Use the namespace you uploaded documents to ---
    target_namespace = "sdk-test-text-ns-01"
    # --- Specify the ID of the document chunk you want to remove ---
    document_id_to_delete = "sdk-doc-001" # Example ID from previous upload
    # ----------------------------------------------------

    print(f"\nAttempting to delete document ID '{document_id_to_delete}' from namespace: '{target_namespace}'")

    # 3. Call the delete_documents method
    #    Note: The method expects a LIST of IDs, even if deleting only one.
    try:
        with client:
            response = client.delete_documents(
                namespace_name=target_namespace,
                ids=[document_id_to_delete] # Pass the ID inside a list
            )
            print("\n--- API Response (Should be 200 OK or 207 Multi-Status) ---")
            print(json.dumps(response, indent=2))
            print("-----------------------------------------------------------\n")

            if response and response.get('status') == 'success':
                 # Check if the specific ID is in the returned list (optional validation)
                 if document_id_to_delete in response.get('deleted_ids', []):
                     print(f"Successfully processed deletion request for document ID '{document_id_to_delete}'. ✅")
                 else:
                     # This case might happen if the ID didn't exist but the call succeeded
                     print(f"Deletion request processed, but ID '{document_id_to_delete}' might not have been present.")
            elif response and response.get('status') == 'partial':
                 print(f"Deletion request partially completed. Check response details.")
            else:
                 print("Deletion request sent, but status was not 'success' or 'partial'. Check response details.")


    # 4. Handle Specific Errors
    except NamespaceNotFound as e:
         print(f"\nError: Namespace '{target_namespace}' not found.")
         print(f"API Message: {e}")
    except InvalidInputError as e:
        print(f"\nError: Invalid input provided for document deletion.")
        print(f"API Message: {e}")
    except AuthenticationError as e:
        print(f"\nError: Authentication failed.")
        print(f"API Message: {e}")
    except APIError as e:
        print(f"\nError: An API error occurred during deletion.")
        print(f"API Message: {e}")
    except MoorchehError as e: # Catch base SDK or network errors
        print(f"\nError: An SDK or network error occurred.")
        print(f"Details: {e}")
    except Exception as e: # Catch any other unexpected errors
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
