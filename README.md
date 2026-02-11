<p align="center">
    <a href="https://www.moorcheh.ai/">
    <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/moorcheh-ai/moorcheh-python-sdk/main/assets/moorcheh-logo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/moorcheh-ai/moorcheh-python-sdk/main/assets/moorcheh-logo-light.svg">
    <img alt="Fallback image description" src="https://raw.githubusercontent.com/moorcheh-ai/moorcheh-python-sdk/main/assets/moorcheh-logo-dark.svg">
    </picture>
    </a>
</p>

<div align="center">
  <h1>The Information-Theoretic Search Engine for RAG & Agentic Memory</h1>
</div>

<p align="center">
  <a href="https://moorcheh.ai/">Learn more</a>
  ·
  <a href="https://www.youtube.com/@moorchehai/videos">Tutorials</a>
  ·
  <a href="https://lnkd.in/gE_Pz_kb">Join Discord</a>
</p>

<p align="center">
    <a href="https://lnkd.in/gE_Pz_kb">
        <img src="https://img.shields.io/badge/Discord-%235865F2.svg?&logo=discord&logoColor=white" alt="Moorcheh Discord">
    </a>
    <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
    <a href="https://pypi.org/project/moorcheh-sdk/"><img alt="Python Version" src="https://img.shields.io/pypi/v/moorcheh-sdk.svg?color=%2334D058"></a>
    <a href="https://pepy.tech/project/moorcheh-sdk"><img alt="Downloads" src="https://static.pepy.tech/personalized-badge/moorcheh-sdk?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Downloads"></a>
    <a href="https://x.com/moorcheh_ai" target="_blank"><img src="https://img.shields.io/twitter/url/https/twitter.com/langchain.svg?style=social&label=Follow%20%40Moorcheh.ai" alt="Twitter / X"></a>
</p>

## Why Moorcheh?
- **32x Compression Ratio** over traditional Vector DBs
- **85% Reduced End-to-End Latency** over Pinecone vector search + Cohere reranker
- **0$ Storage Cost** true serverless architecture scaling to 0 when idle
- [Read the full paper](https://www.arxiv.org/abs/2601.11557)

[Moorcheh](https://moorcheh.ai/) is the universal memory layer for agentic AI, providing fast deterministic semantic search with zero‑ops scalability. Its MIB + ITS stack preserves relevance while reducing storage cost and decreasing latency, providing high‑accuracy semantic search without the overhead of managing clusters, making it ideal for production‑grade RAG, agentic memory, and semantic analytics.

## 🛠️ Key Capabilities

* **Bring any data:** Ingest raw text, files, or vectors with a unified API.
* **One-shot RAG:** Go from ingestion to grounded answers in a single flow.
* **Zero-ops scale:** Serverless architecture that scales up and down automatically.
* **Infrastructure as code:** Deploy into your cloud with native [IaC templates](https://moorcheh.ai/plans).
* **Agentic memory:** Stateful context for assistants and long-running agents.
* **Developer-ready:** Async support, type hints, and clear error handling.

## 🚀 Quickstart Guide

### Hosted Platform
Use our [hosted platform](https://console.moorcheh.ai) to get up and running fast with managed indexing, zero-ops scaling, and usage-based billing.

### Self-Hosted

1. Install the SDK using pip:
```bash
pip install moorcheh-sdk
```

2. Sign up and generate an API key through the [Moorcheh](https://moorcheh.ai) platform dashboard.

3. The recommended way is to set the MOORCHEH_API_KEY environment variable:

```bash
export MOORCHEH_API_KEY="YOUR_API_KEY_HERE"
```

## Basic Usage
```python
import os
from moorcheh_sdk import MoorchehClient

api_key = os.environ.get("MOORCHEH_API_KEY")

with MoorchehClient(api_key=api_key) as client:
    # Create a namespace
    namespace_name = "my-first-namespace"
    client.namespaces.create(namespace_name=namespace_name, type="text")

    # Upload a document
    docs = [{"id": "doc1", "text": "This is the first document about Moorcheh."}]
    upload_res = client.documents.upload(namespace_name=namespace_name, documents=docs)
    print(f"Upload status: {upload_res.get('status')}")

    # Add a small delay for processing before searching
    import time
    print("Waiting briefly for processing...")
    time.sleep(2)

    # Perform semantic search on the namespace
    search_res = client.similarity_search.query(namespaces=[namespace_name], query="Moorcheh", top_k=1)
    print("Search results:")
    print(search_res)

    # Get a Generative AI Answer
    gen_ai_res = client.answer.generate(namespace=namespace_name, query="What is Moorcheh?")
    print("Generative Answer:")
    print(gen_ai_res)
```

For more detailed examples covering vector operations, error handling, and logging configuration, please see the [examples directory](https://github.com/moorcheh-ai/moorcheh-python-sdk/tree/main/examples).

## API Client Methods
The `MoorchehClient` and `AsyncMoorchehClient` classes provide the same method signatures. Below is a list of the available methods.

| Methods                   | Description                                             |
| ------------------------- | ------------------------------------------------------- |
| `namespaces.create`       | Create a text or vector namespace.                      |
| `namespaces.list`         | List all available namespaces.                          |
| `namespaces.delete`       | Delete a namespace by name.                             |
| `documents.upload`        | Upload text documents (auto-embed) to a text namespace. |
| `documents.get`           | Retrieve documents by ID.                               |
| `documents.upload_file`   | Upload a file for server-side ingestion.                |
| `documents.delete`        | Delete documents by ID.                                 |
| `documents.delete_files`  | Delete uploaded files by filename.                      |
| `vectors.upload`          | Upload vectors to a vector namespace.                   |
| `vectors.delete`          | Delete vectors by ID.                                   |
| `similarity_search.query` | Run semantic search with text or vector queries.        |
| `answer.generate`         | Generate a grounded answer from a namespace.            |

For fully detailed method functionality, please see the [API Reference](https://docs.moorcheh.ai/api-reference/introduction).

## 🔗 Integrations
- **[LlamaIndex](https://developers.llamaindex.ai/python/framework/integrations/vector_stores/moorchehdemo)**: Use Moorcheh as a vector store inside LlamaIndex pipelines.
- **[LangChain](https://docs.langchain.com/oss/python/integrations/vectorstores/moorcheh)**: Plug Moorcheh into LangChain retrievers and RAG chains.
- **[n8n](https://n8n.io/integrations/moorcheh)**: Automate workflows that ingest, search, or answer with Moorcheh.
- **[MCP](https://github.com/moorcheh-ai/moorcheh-mcp)**: Connect Moorcheh to external tools via Model Context Protocol.


## Roadmap (Planned)

| Item              | Description                                                       |
| ----------------- | ----------------------------------------------------------------- |
| `get_eigenvectors`| Expose top eigenvectors for semantic structure analysis.          |
| `get_graph`       | Provide a graph view of relationships across data in a namespace. |
| `get_umap_image`  | Generate a 2D UMAP projection image for quick visual exploration. |

## Documentation & Support
Have questions or feedback? We're here to help:
- Docs: [https://docs.moorcheh.ai](https://docs.moorcheh.ai)
- Discord: [Join our Discord server](https://lnkd.in/gE_Pz_kb)
- Appointment: [Book a Discovery Call](https://www.edgeaiinnovations.com/appointments)
- Email: support@moorcheh.ai

## Contributing
Contributions are welcome! Please refer to the contributing guidelines ([CONTRIBUTING.md](CONTRIBUTING.md)) for details on setting up the development environment, running tests, and submitting pull requests.

## License
This project is licensed under the MIT License - See the LICENSE file for details.
