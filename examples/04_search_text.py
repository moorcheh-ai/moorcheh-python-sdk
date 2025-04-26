# examples/04_search_text.py

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
    Example script to perform a text search in a namespace using the SDK.
    """
    print("--- Moorcheh SDK: Text Search Example ---")

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

    # 2. Define Search Parameters
    # --- Use the namespace you uploaded text documents to ---
    target_namespace = "sdk-test-text-ns-01"
    search_query = "API interaction" # The text query
    top_k_results = 2 # How many top results to fetch
    score_threshold = 0.001 # Optional minimum score (0-1)
    # ----------------------------------------------------

    print(f"\nAttempting to search namespace(s): '{target_namespace}'")
    print(f"  Query: '{search_query}'")
    print(f"  Top K: {top_k_results}")
    if score_threshold is not None:
        print(f"  Threshold: {score_threshold}")

    # 3. Call the search method
    try:
        # Use the client's context manager
        with client:
            response = client.search(
                namespaces=[target_namespace], # Pass namespace(s) as a list
                query=search_query,           # Pass the text query string
                top_k=top_k_results,
                threshold=score_threshold,
                # kiosk_mode=False # Default is false
            )
            print("\n--- API Response (Search Results) ---")
            print(json.dumps(response, indent=2))
            print("-------------------------------------\n")

            if response and 'results' in response:
                 print(f"Search completed successfully. Found {len(response['results'])} result(s). ✅")
            else:
                 print("Search completed, but response format might be unexpected.")

    # 4. Handle Specific Errors
    except NamespaceNotFound as e:
         print(f"\nError: Namespace '{target_namespace}' not found or not accessible.")
         print(f"API Message: {e}")
    except InvalidInputError as e:
        print(f"\nError: Invalid input provided for search.")
        print(f"API Message: {e}")
    except AuthenticationError as e:
        print(f"\nError: Authentication failed.")
        print(f"API Message: {e}")
    except APIError as e:
        print(f"\nError: An API error occurred during search.")
        print(f"API Message: {e}")
    except MoorchehError as e: # Catch base SDK or network errors
        print(f"\nError: An SDK or network error occurred.")
        print(f"Details: {e}")
    except Exception as e: # Catch any other unexpected errors
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
