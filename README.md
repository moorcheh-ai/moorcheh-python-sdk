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

Install the SDK using pip (once published to PyPI):

```bash
pip install moorcheh-sdk
```
(Note: Package not yet published to PyPI)
Alternatively, install directly from the GitHub repository:pip install git+[https://github.com/mjfekri/moorcheh-python-sdk.git](https://github.com/mjfekri/moorcheh-python-sdk.git)

## Usage
It's recommended to use a virtual environment. If you clone the repository, you can use Poetry for easy setup and dependency management:

```bash
git clone [https://github.com/mjfekri/moorcheh-python-sdk.git](https://github.com/mjfekri/moorcheh-python-sdk.git) 
cd moorcheh-python-sdk
poetry install
```

## Authentication
The SDK requires a Moorcheh API key for authentication. Obtain an API Key: Sign up and generate an API key through the Moorcheh.ai [https://moorcheh.ai] platform dashboard. 
Provide the Key: The recommended way is to set the MOORCHEH_API_KEY environment variable:
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
A comprehensive quick start script is available in the examples/ directory. This script demonstrates the core workflow: creating namespaces, uploading data, searching, and deleting items. To run the quick start example:
Clone the repository (if you haven't already):
```bash
git clone [https://github.com/mjfekri/moorcheh-python-sdk.git](https://github.com/mjfekri/moorcheh-python-sdk.git) 
cd moorcheh-python-sdk
```
Install dependencies using Poetry: 
```bash
poetry install
```
Set your API Key as an environment variable (see Authentication section above) in your current terminal session. 
Run the script using poetry run:
```bash
poetry run python examples/quick_start.py
```
The script will print output to the console showing the results of each API call. 

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