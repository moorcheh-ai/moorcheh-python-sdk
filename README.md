# Moorcheh Python SDK

[![PyPI version](https://badge.fury.io/py/moorcheh-sdk.svg)](https://badge.fury.io/py/moorcheh-sdk) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) Python SDK for interacting with the Moorcheh Semantic Search API v1. Moorcheh provides ultra-fast, highly accurate vector similarity search and analysis capabilities based on information-theoretic principles.

This SDK simplifies the process of creating namespaces, ingesting data (text or vectors), performing searches, and managing your resources via Python.

## Features

* **Namespace Management:** Create, list, and delete text or vector namespaces.
* **Data Ingestion:** Upload text documents (with automatic embedding) or pre-computed vectors.
* **Semantic Search:** Perform fast and accurate similarity searches using text or vector queries. Filter results using `top_k` and `threshold`.
* **Data Deletion:** Remove specific documents or vectors from your namespaces by ID.
* **Pythonic Interface:** Object-oriented client with clear methods and type hinting.
* **Error Handling:** Custom exceptions for specific API errors (Authentication, Not Found, Invalid Input, etc.).

## Installation

Install the SDK using pip:

```bash
pip install moorcheh-sdk
```

## Development

If you want to contribute or run the examples locally, clone the repository and install using Poetry:
```bash
git clone https://github.com/mjfekri/moorcheh-python-sdk.git
cd moorcheh-python-sdk
poetry install --with dev
```

## Authentication
The SDK requires a Moorcheh API key for authentication. Obtain an API Key: Sign up and generate an API key through the Moorcheh.ai [https://moorcheh.ai] platform dashboard. 

### Provide the Key: 
The recommended way is to set the MOORCHEH_API_KEY environment variable:

Linux/macOS/Git Bash:
```bash
export MOORCHEH_API_KEY="YOUR_API_KEY_HERE"
```
Windows PowerShell:
```powershell
$env:MOORCHEH_API_KEY = "YOUR_API_KEY_HERE"
```
Windows CMD:
```bash
set MOORCHEH_API_KEY=YOUR_API_KEY_HERE
```
The client will automatically read this environment variable upon initialization.

Alternatively, you can pass the key directly to the constructor (MoorchehClient(api_key="...")), but using environment variables is generally preferred for security. 

## Quick Start:
This example demonstrates the basic usage after installing the SDK.
```python
import os
import logging
from moorcheh_sdk import MoorchehClient, MoorchehError, ConflictError

# Configure basic logging to see SDK messages
logging.basicConfig(level=logging.INFO)

# Ensure MOORCHEH_API_KEY is set as an environment variable
api_key = os.environ.get("MOORCHEH_API_KEY")
if not api_key:
    print("Error: MOORCHEH_API_KEY environment variable not set.")
    exit()

try:
    # Use the client as a context manager for automatic connection closing
    with MoorchehClient(api_key=api_key) as client:
        # 1. Create a namespace
        namespace_name = "my-first-namespace"
        print(f"Attempting to create namespace: {namespace_name}")
        try:
            client.create_namespace(namespace_name=namespace_name, type="text")
            print(f"Namespace '{namespace_name}' created.")
        except ConflictError:
            print(f"Namespace '{namespace_name}' already exists.")
        except MoorchehError as e:
            print(f"Error creating namespace: {e}")
            exit()

        # 2. List namespaces
        print("\nListing namespaces...")
        ns_list = client.list_namespaces()
        print("Available namespaces:")
        for ns in ns_list.get('namespaces', []):
            print(f" - {ns.get('namespace_name')} (Type: {ns.get('type')})")

        # 3. Upload a document
        print(f"\nUploading document to '{namespace_name}'...")
        docs = [{"id": "doc1", "text": "This is the first document about Moorcheh."}]
        upload_res = client.upload_documents(namespace_name=namespace_name, documents=docs)
        print(f"Upload status: {upload_res.get('status')}")

        # Add a small delay for processing before searching
        import time
        print("Waiting briefly for processing...")
        time.sleep(2)

        # 4. Search the namespace
        print(f"\nSearching '{namespace_name}' for 'Moorcheh'...")
        search_res = client.search(namespaces=[namespace_name], query="Moorcheh", top_k=1)
        print("Search results:")
        print(search_res)

        # 5. Delete the document
        print(f"\nDeleting document 'doc1' from '{namespace_name}'...")
        delete_res = client.delete_documents(namespace_name=namespace_name, ids=["doc1"])
        print(f"Delete status: {delete_res.get('status')}")

        # 6. Delete the namespace (optional cleanup)
        # print(f"\nDeleting namespace '{namespace_name}'...")
        # client.delete_namespace(namespace_name)
        # print("Namespace deleted.")

except MoorchehError as e:
    print(f"\nAn SDK error occurred: {e}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
```
(Note: For more detailed examples covering vector operations, error handling, and logging configuration, please see the examples/ directory in the source repository.)

## Development Setup
If you want to contribute, run tests, or run the example scripts directly from the source code:

Clone the repository:
```bash
git clone https://github.com/mjfekri/moorcheh-python-sdk.git
cd moorcheh-python-sdk
```

Install dependencies using Poetry (this includes development tools like pytest):
```bash
poetry install --with dev
```

Set your MOORCHEH_API_KEY environment variable.
Run examples using poetry run:
```bash
poetry run python examples/quickstart.py
```

Run tests using poetry run:
```bash
poetry run pytest tests/
```

## API Client Methods
The `MoorchehClient` class provides the following methods corresponding to the API v1 endpoints:
### Namespace Management:
```python
create_namespace(namespace_name, type, vector_dimension=None)
```
```python
list_namespaces()
```
```python
delete_namespace(namespace_name)
```
### Data Ingestion:
```python
upload_documents(namespace_name, documents) - For text namespaces (async processing).
```
```python
upload_vectors(namespace_name, vectors) - For vector namespaces (sync processing).
```
### Semantic Search
```python
search(namespaces, query, top_k=10, threshold=None, kiosk_mode=False) - Handles text or vector queries.
```

### Data Deletion:
```python
delete_documents(namespace_name, ids)
```
```python
delete_vectors(namespace_name, ids)
```
### Analysis (Planned):
```python
get_eigenvectors(namespace_name, n_eigenvectors=1) - Not yet implemented
```
```python
get_graph(namespace_name) - Not yet implemented
```
```python
get_umap_image(namespace_name, n_dimensions=2) - Not yet implemented
```
(Refer to method docstrings or full documentation for detailed parameters and return types.)

## Documentation
Full API reference and further examples can be found at: [https://www.moorcheh.ai/docs](https://www.moorcheh.ai/docs)

## Contributing
Contributions are welcome! Please refer to the contributing guidelines (CONTRIBUTING.md - TBD) for details on setting up the development environment, running tests, and submitting pull requests.

## License
This project is licensed under the MIT License -