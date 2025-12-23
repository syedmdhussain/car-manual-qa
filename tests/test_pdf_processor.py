"""
Unit tests for PDF processor module.
Tests PDF processing and text chunking functionality.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_processor import PDFProcessor, detect_car_model


class TestCarModelDetection(unittest.TestCase):
    """Test cases for car model detection."""
    
    def test_detect_mg_astor(self):
        """Test MG Astor detection."""
        self.assertEqual(detect_car_model("How to start MG Astor?"), "MG Astor")
        self.assertEqual(detect_car_model("What is the Astor engine oil?"), "MG Astor")
        self.assertEqual(detect_car_model("mg astor manual"), "MG Astor")
    
    def test_detect_tata_tiago(self):
        """Test Tata Tiago detection."""
        self.assertEqual(detect_car_model("How to start Tata Tiago?"), "Tata Tiago")
        self.assertEqual(detect_car_model("What is the Tiago engine oil?"), "Tata Tiago")
        self.assertEqual(detect_car_model("tiago manual"), "Tata Tiago")
    
    def test_detect_no_model(self):
        """Test when no model is detected."""
        self.assertIsNone(detect_car_model("How to change oil?"))
        self.assertIsNone(detect_car_model("random question"))
    
    def test_case_insensitive_detection(self):
        """Test case insensitive model detection."""
        self.assertEqual(detect_car_model("MG ASTOR"), "MG Astor")
        self.assertEqual(detect_car_model("tata tiago"), "Tata Tiago")


class TestPDFProcessor(unittest.TestCase):
    """Test cases for PDFProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = PDFProcessor()
    
    def test_processor_initialization(self):
        """Test processor initializes correctly."""
        self.assertIsNotNone(self.processor)
        self.assertIsInstance(self.processor.manuals_data, dict)
        self.assertEqual(len(self.processor.manuals_data), 0)
    
    def test_chunk_text(self):
        """Test text chunking functionality."""
        # Create sample text with more than 500 words
        words = ["word"] * 600
        text = " ".join(words)
        
        chunks = self.processor.chunk_text(text)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 1)  # Should create multiple chunks
        
        # Check each chunk is a dict with required keys
        for chunk in chunks:
            self.assertIsInstance(chunk, dict)
            self.assertIn('text', chunk)
            self.assertIn('start_word', chunk)
            self.assertIn('end_word', chunk)
    
    def test_chunk_text_short(self):
        """Test chunking with text shorter than chunk size."""
        text = "This is a short text."
        chunks = self.processor.chunk_text(text)
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['text'], text)
    
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        words = ["word"] * 700
        text = " ".join(words)
        
        chunks = self.processor.chunk_text(text)
        
        if len(chunks) > 1:
            # Check overlap exists
            chunk1_end = chunks[0]['end_word']
            chunk2_start = chunks[1]['start_word']
            
            # Second chunk should start before first chunk ends (overlap)
            self.assertLess(chunk2_start, chunk1_end)


if __name__ == '__main__':
    unittest.main()

