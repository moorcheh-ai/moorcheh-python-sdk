# examples/02_list_namespaces.py

import os
import sys
import json
from moorcheh_sdk import (
    MoorchehClient,
    MoorchehError,
    AuthenticationError,
    APIError,
)

def main():
    """
    Example script to list Moorcheh namespaces using the SDK.
    """
    print("--- Moorcheh SDK: List Namespaces Example ---")

    # 1. Initialize the Client
    # Reads the API key from the MOORCHEH_API_KEY environment variable
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

    # 2. Call the list_namespaces method
    print("\nAttempting to list namespaces...")
    try:
        # Use the client's context manager for automatic cleanup
        with client:
            response = client.list_namespaces() # Call the SDK method

            print("\n--- API Response ---")
            print(json.dumps(response, indent=2))
            print("--------------------\n")

            # Optional: Print a summary
            if response and 'namespaces' in response:
                 num_namespaces = len(response['namespaces'])
                 print(f"Successfully retrieved {num_namespaces} namespace(s). ✅")
                 # Optionally iterate and print names
                 # for ns in response['namespaces']:
                 #     print(f" - {ns.get('namespace_name')} (Type: {ns.get('type')}, Items: {ns.get('itemCount')})")
            else:
                 print("Received response, but 'namespaces' key was missing or empty.")


    # 3. Handle Specific Errors
    except AuthenticationError as e: # Should be caught by init, but good practice
        print(f"\nError: Authentication failed.")
        print(f"API Message: {e}")
    except APIError as e:
        print(f"\nError: An API error occurred.")
        print(f"API Message: {e}")
    except MoorchehError as e: # Catch base SDK or network errors
        print(f"\nError: An SDK or network error occurred.")
        print(f"Details: {e}")
    except Exception as e: # Catch any other unexpected errors
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
