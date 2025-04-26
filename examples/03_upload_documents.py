# examples/03_upload_documents.py

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
    Example script to upload documents to a text namespace using the SDK.
    """
    print("--- Moorcheh SDK: Upload Documents Example ---")

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

    # 2. Define Target Namespace and Documents to Upload
    target_namespace = "sdk-test-text-ns-01" # Use the text namespace created earlier

    documents_to_upload = [
        {
            "id": "sdk-doc-001", # Unique ID for this chunk
            "text": "The Moorcheh Python SDK simplifies API interactions.",
            "source": "sdk_example_03",
            "version": 1.0
        },
        {
            "id": "sdk-doc-002",
            "text": "Uploading documents involves sending a list of dictionaries.",
            "source": "sdk_example_03",
            "topic": "ingestion"
        },
        {
            "id": "sdk-doc-003",
            "text": "Each document needs a unique ID and text content. Metadata is optional but useful.",
            "source": "sdk_example_03",
            "topic": "data_format"
        }
    ]

    print(f"\nAttempting to upload {len(documents_to_upload)} documents to namespace: '{target_namespace}'")

    # 3. Call the upload_documents method
    try:
        # Use the client's context manager
        with client:
            response = client.upload_documents(
                namespace_name=target_namespace,
                documents=documents_to_upload
            )
            print("\n--- API Response (Should be 202 Accepted) ---")
            print(json.dumps(response, indent=2))
            print("--------------------------------------------\n")
            if response.get('status') == 'queued':
                print(f"Successfully queued {len(response.get('submitted_ids', []))} documents for processing! ✅")
            else:
                print("Upload request sent, but status was not 'queued'. Check response details.")


    # 4. Handle Specific Errors
    except NamespaceNotFound as e:
         print(f"\nError: Namespace '{target_namespace}' not found.")
         print(f"API Message: {e}")
    except InvalidInputError as e:
        print(f"\nError: Invalid input provided for document upload.")
        print(f"API Message: {e}")
    except AuthenticationError as e:
        print(f"\nError: Authentication failed.")
        print(f"API Message: {e}")
    except APIError as e:
        print(f"\nError: An API error occurred during upload.")
        print(f"API Message: {e}")
    except MoorchehError as e: # Catch base SDK or network errors
        print(f"\nError: An SDK or network error occurred.")
        print(f"Details: {e}")
    except Exception as e: # Catch any other unexpected errors
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
