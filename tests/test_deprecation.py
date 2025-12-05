import pytest

from moorcheh_sdk import MoorchehClient
from tests.constants import DUMMY_API_KEY


def test_deprecated_methods(mock_httpx_client, mocker, mock_response):
    """Test that deprecated methods issue a warning and call the new resource methods."""
    with MoorchehClient(api_key=DUMMY_API_KEY) as client:
        client._mock_httpx_instance = mock_httpx_client

        mock_httpx_client.request.side_effect = [
            mock_response(201, json_data={}),  # create_namespace
            mock_response(200, json_data={}),  # delete_namespace
            mock_response(200, json_data={"namespaces": []}),  # list_namespaces
            mock_response(202, json_data={}),  # upload_documents
            mock_response(200, json_data={}),  # get_documents
            mock_response(201, json_data={}),  # upload_vectors
            mock_response(200, json_data={}),  # search
            mock_response(200, json_data={}),  # get_generative_answer
            mock_response(200, json_data={}),  # delete_documents
            mock_response(200, json_data={}),  # delete_vectors
        ]

        # 1. create_namespace
        with pytest.warns(DeprecationWarning, match="create_namespace is deprecated"):
            client.create_namespace("ns", "text")

        # 2. delete_namespace
        with pytest.warns(DeprecationWarning, match="delete_namespace is deprecated"):
            client.delete_namespace("ns")

        # 3. list_namespaces
        with pytest.warns(DeprecationWarning, match="list_namespaces is deprecated"):
            client.list_namespaces()

        # 4. upload_documents
        with pytest.warns(DeprecationWarning, match="upload_documents is deprecated"):
            client.upload_documents("ns", [{"id": "1", "text": "t"}])

        # 5. get_documents
        with pytest.warns(DeprecationWarning, match="get_documents is deprecated"):
            client.get_documents("ns", ["1"])

        # 6. upload_vectors
        with pytest.warns(DeprecationWarning, match="upload_vectors is deprecated"):
            client.upload_vectors("ns", [{"id": "1", "vector": [0.1]}])

        # 7. search
        with pytest.warns(DeprecationWarning, match="search is deprecated"):
            client.search(["ns"], "query")

        # 8. get_generative_answer
        with pytest.warns(
            DeprecationWarning, match="get_generative_answer is deprecated"
        ):
            client.get_generative_answer("ns", "query")

        # 9. delete_documents
        with pytest.warns(DeprecationWarning, match="delete_documents is deprecated"):
            client.delete_documents("ns", ["1"])

        # 10. delete_vectors
        with pytest.warns(DeprecationWarning, match="delete_vectors is deprecated"):
            client.delete_vectors("ns", ["1"])
