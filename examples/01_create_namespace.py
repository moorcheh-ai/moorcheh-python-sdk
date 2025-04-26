# examples/01_create_namespace.py

import os
import sys
import json
from moorcheh_sdk import (
    MoorchehClient,
    MoorchehError,
    AuthenticationError,
    InvalidInputError,
    ConflictError,
    APIError,
)

def main():
    """
    Example script to create a Moorcheh namespace using the SDK.
    """
    print("--- Moorcheh SDK: Create Namespace Example ---")

    # 1. Initialize the Client
    # The client reads the API key from the MOORCHEH_API_KEY environment variable
    try:
        # You can optionally pass base_url="YOUR_STAGING_URL" if needed
        client = MoorchehClient()
        print("Client initialized successfully.")
    except AuthenticationError as e:
        print(f"Authentication Error: {e}")
        print("Please ensure the MOORCHEH_API_KEY environment variable is set correctly.")
        sys.exit(1) # Exit if client cannot be initialized
    except MoorchehError as e:
        print(f"Error initializing client: {e}")
        sys.exit(1)

    # 2. Define Namespace Parameters
    # --- Choose a unique name and type for your test ---
    namespace_to_create = "sdk-test-text-ns-01"
    namespace_type = "text" # "text" or "vector"
    vector_dimension = None # Set to integer (e.g., 10) if type is "vector", otherwise None
    # ----------------------------------------------------

    print(f"\nAttempting to create namespace:")
    print(f"  Name: {namespace_to_create}")
    print(f"  Type: {namespace_type}")
    if vector_dimension:
        print(f"  Dimension: {vector_dimension}")

    # 3. Call the create_namespace method
    try:
        # Use the client's context manager for automatic cleanup
        with client:
            response = client.create_namespace(
                namespace_name=namespace_to_create,
                type=namespace_type,
                vector_dimension=vector_dimension
            )
            print("\n--- API Response ---")
            print(json.dumps(response, indent=2))
            print("--------------------\n")
            print(f"Successfully created namespace '{response.get('namespace_name')}'! ✅")

    # 4. Handle Specific Errors
    except ConflictError as e:
        print(f"\nError: Namespace '{namespace_to_create}' already exists.")
        print(f"API Message: {e}")
    except InvalidInputError as e:
        print(f"\nError: Invalid input provided for namespace creation.")
        print(f"API Message: {e}")
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
