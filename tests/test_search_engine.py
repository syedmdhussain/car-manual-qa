"""
Unit tests for search engine module.
Tests semantic search functionality.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_engine import ManualSearchEngine


class TestManualSearchEngine(unittest.TestCase):
    """Test cases for ManualSearchEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.search_engine = ManualSearchEngine()
    
    def test_search_engine_initialization(self):
        """Test search engine initializes correctly."""
        self.assertIsNotNone(self.search_engine)
        self.assertIsNone(self.search_engine.model)  # Lazy loading
        self.assertIsNone(self.search_engine.index)
        self.assertIsInstance(self.search_engine.manuals_data, dict)
        self.assertEqual(len(self.search_engine._query_cache), 0)
    
    def test_lazy_model_loading(self):
        """Test model loads lazily when needed."""
        # Model should be None initially
        self.assertIsNone(self.search_engine.model)
        
        # Ensure model loads when needed
        self.search_engine._ensure_model_loaded()
        self.assertIsNotNone(self.search_engine.model)
    
    def test_build_index_with_sample_data(self):
        """Test building search index with sample data."""
        sample_data = {
            "Test Manual": {
                "car_model": "Test Car",
                "chunks": [
                    {"text": "This is test chunk 1", "start_word": 0, "end_word": 5},
                    {"text": "This is test chunk 2", "start_word": 5, "end_word": 10}
                ]
            }
        }
        
        # Force rebuild to avoid loading cached index
        self.search_engine.build_index(sample_data, force_rebuild=True)
        
        # Check index was built
        self.assertIsNotNone(self.search_engine.index)
        self.assertIsNotNone(self.search_engine.model)
        self.assertEqual(len(self.search_engine.chunk_metadata), 2)
    
    def test_query_cache(self):
        """Test query embedding caching."""
        # Build index first
        sample_data = {
            "Test Manual": {
                "car_model": "Test Car",
                "chunks": [
                    {"text": "Engine oil specification", "start_word": 0, "end_word": 3}
                ]
            }
        }
        self.search_engine.build_index(sample_data)
        
        # First query - should cache
        embedding1 = self.search_engine._get_cached_embedding("test query")
        
        # Check cache
        self.assertIn("test query", self.search_engine._query_cache)
        
        # Second query - should use cache
        embedding2 = self.search_engine._get_cached_embedding("test query")
        
        # Should be same embedding
        self.assertTrue((embedding1 == embedding2).all())
    
    def test_simple_keyword_search(self):
        """Test keyword-based search fallback."""
        sample_data = {
            "Test Manual": {
                "car_model": "Test Car",
                "chunks": [
                    {"text": "Engine oil SAE 5W-30", "start_word": 0, "end_word": 4},
                    {"text": "Tire pressure 32 PSI", "start_word": 4, "end_word": 8}
                ]
            }
        }
        self.search_engine.manuals_data = sample_data
        self.search_engine.chunk_metadata = [
            {"text": "Engine oil SAE 5W-30", "car_model": "Test Car"},
            {"text": "Tire pressure 32 PSI", "car_model": "Test Car"}
        ]
        
        results = self.search_engine.simple_keyword_search("engine oil", top_k=5)
        
        self.assertIsInstance(results, list)
        if len(results) > 0:
            self.assertIn("engine", results[0]["text"].lower())


if __name__ == '__main__':
    unittest.main()

