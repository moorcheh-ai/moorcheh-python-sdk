# benchmarks/benchmark_response_time.py

import os
import sys
import json
import random
import time
import statistics # For calculating the average
import numpy as np # For generating vectors easily
import argparse # For command-line arguments

print("Starting benchmark script...")


# --- Try importing the SDK ---
# Assumes the script is run from the project root using 'poetry run'
# or that the moorcheh_sdk package is installed in the environment
try:
    from moorcheh_sdk import (
        MoorchehClient,
        MoorchehError,
        AuthenticationError,
        InvalidInputError,
        NamespaceNotFound,
        ConflictError,
        APIError,
    )
    print("Moorcheh SDK imported successfully.")
except ImportError as e:
    print(f"ERROR: Failed to import Moorcheh SDK: {e}")
    print("Ensure you are running this script from the project root using 'poetry run python benchmarks/benchmark_response_time.py'")
    print("Or that the SDK package is installed in your environment.")
    sys.exit(1)

# --- Configuration ---
# Default values
DEFAULT_NUM_VECTORS = 1000
DEFAULT_VECTOR_DIMENSION = 1024
DEFAULT_NUM_QUERIES = 12
DEFAULT_UPLOAD_BATCH_SIZE = 100
DEFAULT_TOP_K = 10
DEFAULT_NAMESPACE_PREFIX = "local-benchmark-ns-"

def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Moorcheh Search API Benchmark Script")
    parser.add_argument(
        "-n", "--num-vectors", type=int, default=DEFAULT_NUM_VECTORS,
        help=f"Number of random vectors to upload (default: {DEFAULT_NUM_VECTORS})"
    )
    parser.add_argument(
        "-d", "--dimension", type=int, default=DEFAULT_VECTOR_DIMENSION,
        help=f"Dimension of the random vectors (default: {DEFAULT_VECTOR_DIMENSION})"
    )
    parser.add_argument(
        "-q", "--num-queries", type=int, default=DEFAULT_NUM_QUERIES,
        help=f"Number of random search queries to run (default: {DEFAULT_NUM_QUERIES})"
    )
    parser.add_argument(
        "-b", "--batch-size", type=int, default=DEFAULT_UPLOAD_BATCH_SIZE,
        help=f"Number of vectors per upload batch (default: {DEFAULT_UPLOAD_BATCH_SIZE})"
    )
    parser.add_argument(
        "-k", "--top-k", type=int, default=DEFAULT_TOP_K,
        help=f"Number of results to request per search (default: {DEFAULT_TOP_K})"
    )
    parser.add_argument(
        "--namespace", type=str, default=f"{DEFAULT_NAMESPACE_PREFIX}{random.randint(1000, 9999)}",
        help=f"Name of the namespace to create/use (default: {DEFAULT_NAMESPACE_PREFIX}<random>)"
    )
    parser.add_argument(
        "--base-url", type=str, default=None,
        help="Optional base URL for the Moorcheh API (overrides SDK default and MOORCHEH_BASE_URL env var)"
    )
    parser.add_argument(
        "--keep-namespace", action="store_true",
        help="If set, the script will not prompt to delete the namespace after the benchmark."
    )
    return parser.parse_args()

# --- Helper Functions ---
def generate_random_vectors(num_vectors, dimension):
    """Generates a list of random vectors using NumPy."""
    print(f"Generating {num_vectors} random vectors of dimension {dimension}...")
    vectors = np.random.uniform(-1.0, 1.0, size=(num_vectors, dimension)).astype(np.float32)
    vectors_list = vectors.tolist()
    print("Vector generation complete.")
    return vectors_list

def create_upload_payload(vectors_list, start_index):
    """Creates the payload for the upload_vectors API call."""
    payload_vectors = []
    for i, vec in enumerate(vectors_list):
         payload_vectors.append({
             "id": f"bench-vec-{start_index + i}", # Unique ID
             "vector": vec,
             "metadata": {"source": "local_benchmark", "index": start_index + i}
         })
    return {"vectors": payload_vectors}

# --- Main Benchmark Logic ---
def run_benchmark(args):
    """Runs the benchmark: create ns, upload, search, measure, cleanup."""
    search_times = []
    namespace_created = False
    client = None # Initialize client variable

    # --- Get API Key from Environment Variable ---
    api_key = os.environ.get("MOORCHEH_API_KEY")
    if not api_key:
        print("ERROR: Environment variable MOORCHEH_API_KEY is not set.")
        print("Please set it before running the script (e.g., export MOORCHEH_API_KEY='your_key')")
        sys.exit(1)
    print("API Key loaded from environment variable.")

    # --- Initialize Moorcheh Client ---
    try:
        client = MoorchehClient(api_key=api_key, base_url=args.base_url)
        print(f"Moorcheh Client initialized. Target URL: {client.base_url}")
    except Exception as e:
        print(f"ERROR: Failed to initialize Moorcheh Client: {e}")
        sys.exit(1)

    # --- Start Benchmark ---
    try:
        with client: # Use context manager for client cleanup
            # 1. Create Namespace
            print(f"\n[1] Ensuring vector namespace exists: '{args.namespace}' (Dim: {args.dimension})")
            try:
                client.create_namespace(
                    namespace_name=args.namespace,
                    type="vector",
                    vector_dimension=args.dimension
                )
                print(f"Namespace '{args.namespace}' created successfully.")
                namespace_created = True
            except ConflictError:
                print(f"Namespace '{args.namespace}' already exists. Attempting to use it.")
                # Need to verify type/dimension if using existing? For benchmark, assume it's compatible.
                namespace_created = True # Mark as 'created' for cleanup logic
            except Exception as e:
                print(f"ERROR: Failed to create/confirm namespace: {e}")
                return # Stop if we can't create/use the namespace

            # 2. Generate and Upload Vectors in Batches
            print(f"\n[2] Generating {args.num_vectors} vectors...")
            all_vectors = generate_random_vectors(args.num_vectors, args.dimension)

            print(f"Uploading vectors in batches of {args.batch_size}...")
            upload_start_time = time.time()
            uploaded_count = 0
            for i in range(0, args.num_vectors, args.batch_size):
                batch_vectors = all_vectors[i : i + args.batch_size]
                payload = create_upload_payload(batch_vectors, start_index=i)
                batch_num = (i // args.batch_size) + 1
                print(f"  Uploading batch {batch_num}/{ (args.num_vectors + args.batch_size - 1) // args.batch_size } ({len(batch_vectors)} vectors)...")
                try:
                    upload_response = client.upload_vectors(
                        namespace_name=args.namespace,
                        vectors=payload['vectors']
                    )
                    if upload_response.get("status") == "success":
                         uploaded_count += len(upload_response.get("vector_ids_processed", []))
                    elif upload_response.get("status") == "partial":
                         processed_ids = upload_response.get("vector_ids_processed", [])
                         uploaded_count += len(processed_ids)
                         print(f"  WARNING: Upload batch {batch_num} partially completed.")
                         print(f"  Response: {json.dumps(upload_response)}")
                    else:
                         print(f"  WARNING: Upload batch {batch_num} returned unexpected status: {upload_response.get('status')}")
                         print(f"  Response: {json.dumps(upload_response)}")
                except Exception as e:
                     print(f"  ERROR uploading batch {batch_num}: {e}")
                     # Decide if you want to stop or continue on batch upload error
            upload_end_time = time.time()
            print(f"Vector upload process finished. Attempted to upload {uploaded_count}/{args.num_vectors} vectors in {upload_end_time - upload_start_time:.2f} seconds.")

            # Optional: Add a small delay
            # print("Waiting briefly after upload...")
            # time.sleep(5)

            # 3. Perform Search Queries and Measure Time
            print(f"\n[3] Performing {args.num_queries} search queries...")
            query_vectors = generate_random_vectors(args.num_queries, args.dimension)

            for i, q_vec in enumerate(query_vectors):
                print(f"  Running search query {i+1}/{args.num_queries}...")
                try:
                    search_response = client.search(
                        namespaces=[args.namespace],
                        query=q_vec,
                        top_k=args.top_k
                    )
                    exec_time = search_response.get('execution_time')
                    if isinstance(exec_time, (int, float)):
                        search_times.append(exec_time)
                        print(f"    Query {i+1} successful. API Execution Time: {exec_time:.4f}s")
                    else:
                        print(f"    Query {i+1} succeeded but 'execution_time' was missing/invalid.")
                        # print(f"    Response: {json.dumps(search_response)}") # Avoid printing large results
                except Exception as e:
                    print(f"    ERROR during search query {i+1}: {e}")
                time.sleep(0.5) # Small delay between queries

            # 4. Calculate and Print Average Time
            print("\n[4] Calculating results...")
            if search_times:
                average_time = statistics.mean(search_times)
                median_time = statistics.median(search_times)
                min_time = min(search_times)
                max_time = max(search_times)
                stdev_time = statistics.stdev(search_times) if len(search_times) > 1 else 0.0
                print("\n--- Benchmark Results ---")
                print(f"Namespace:                {args.namespace}")
                print(f"Vector Dimension:         {args.dimension}")
                print(f"Vectors Uploaded:         {uploaded_count}/{args.num_vectors}")
                print(f"Search Queries Performed: {len(search_times)}/{args.num_queries}")
                print(f"Search Top K:             {args.top_k}")
                print("-" * 25)
                print(f"Avg. API Execution Time:  {average_time:.4f} s")
                print(f"Median API Exec. Time:  {median_time:.4f} s")
                print(f"Min API Execution Time:   {min_time:.4f} s")
                print(f"Max API Execution Time:   {max_time:.4f} s")
                print(f"StdDev API Exec. Time:  {stdev_time:.4f} s")
                print("-------------------------\n")
            else:
                print("\n--- Benchmark Results ---")
                print("No successful search queries were measured.")
                print("-------------------------\n")

    except (AuthenticationError, InvalidInputError, NamespaceNotFound, ConflictError, APIError, MoorchehError) as e:
        print(f"\nAn SDK or API error occurred during the benchmark:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Details: {e}")
    except Exception as e:
        print(f"\nAn unexpected Python error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 5. Cleanup (Optional but Recommended)
        if namespace_created and not args.keep_namespace:
            # Use input() for interactive confirmation when run manually
            cleanup_input = input(f"Delete the benchmark namespace '{args.namespace}'? (y/N): ")
            cleanup = cleanup_input.lower() == 'y'
        elif args.keep_namespace:
            cleanup = False
            print("\n--keep-namespace flag set. Skipping namespace deletion.")
        else: # Namespace wasn't created or confirmed
             cleanup = False

        if cleanup:
            try:
                print(f"\n[5] Cleaning up: Deleting namespace '{args.namespace}'...")
                # Need a client instance. If the 'with' block exited due to error,
                # client might be closed. Re-initialize if needed.
                # Using a new instance is safer in case of errors.
                with MoorchehClient(api_key=api_key, base_url=args.base_url) as cleanup_client:
                     cleanup_client.delete_namespace(args.namespace)
                print("Namespace deleted successfully.")
            except Exception as e:
                print(f"ERROR during cleanup: Failed to delete namespace '{args.namespace}': {e}")
        else:
             if namespace_created and not args.keep_namespace:
                print(f"\nSkipping deletion of namespace '{args.namespace}'. Please delete it manually if needed.")

        print("\nBenchmark script finished.")


# --- Script Entry Point ---
if __name__ == "__main__":
    args = parse_arguments()
    run_benchmark(args)

