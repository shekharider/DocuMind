import sys
import unittest
from unittest.mock import patch, MagicMock
import json
import io

# Mock urllib.request.urlopen before importing rag_engine to avoid network calls during initialization (if any)
mock_response_data = [[0.1] * 384]

class MockHTTPResponse:
    def __init__(self, data, status=200):
        self.data = json.dumps(data).encode("utf-8")
        self.status = status
    def read(self):
        return self.data
    def decode(self, encoding):
        return self.data.decode(encoding)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        pass

def mock_urlopen(req, timeout=None):
    # If multiple texts were passed in inputs, return list of embeddings
    try:
        req_data = json.loads(req.data.decode("utf-8"))
        inputs = req_data.get("inputs", [])
        if isinstance(inputs, list):
            return MockHTTPResponse([[0.1] * 384 for _ in inputs])
        else:
            return MockHTTPResponse([0.1] * 384)
    except Exception:
        return MockHTTPResponse([[0.1] * 384])

@patch("urllib.request.urlopen", side_effect=mock_urlopen)
class TestRAGPipeline(unittest.TestCase):

    def test_embeddings_generation(self, mock_url):
        from backend.app.services.rag_engine import langchain_embeddings
        
        # Test embed_query (single string)
        query_vec = langchain_embeddings.embed_query("test query")
        self.assertEqual(len(query_vec), 384)
        self.assertTrue(all(x == 0.1 for x in query_vec))
        
        # Test embed_documents (list of strings)
        doc_vecs = langchain_embeddings.embed_documents(["doc1", "doc2"])
        self.assertEqual(len(doc_vecs), 2)
        self.assertEqual(len(doc_vecs[0]), 384)
        self.assertEqual(len(doc_vecs[1]), 384)

    def test_store_and_search_chunks(self, mock_url):
        from backend.app.services.rag_engine import store_chunks_in_chroma, search_chunks_mmr, get_collection
        
        # Clear out any existing collection entries for our test IDs if possible, or just use unique IDs
        test_chunks = [
            {"id": 999991, "content": "Python is a programming language.", "chunk_index": 0},
            {"id": 999992, "content": "Machine learning is a subset of AI.", "chunk_index": 1}
        ]
        
        # Call store_chunks_in_chroma (which will call our mock_urlopen for embeddings)
        try:
            store_chunks_in_chroma(
                chunks=test_chunks,
                document_id=999,
                session_id=999,
                filename="test_file.pdf"
            )
            print("Successfully stored mock chunks in Chroma DB!")
        except Exception as e:
            self.fail(f"store_chunks_in_chroma raised an exception: {e}")

        # Search for chunks
        try:
            results = search_chunks_mmr(
                query="What is python?",
                session_id=999,
                k=2
            )
            self.assertTrue(len(results) > 0)
            self.assertEqual(results[0]["filename"], "test_file.pdf")
            self.assertEqual(results[0]["document_id"], 999)
            print("Successfully retrieved mock chunks via MMR search from Chroma DB!")
        except Exception as e:
            self.fail(f"search_chunks_mmr raised an exception: {e}")

if __name__ == "__main__":
    unittest.main()
