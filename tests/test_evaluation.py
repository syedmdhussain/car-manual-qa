"""
Unit tests for evaluation module.
Tests the answer quality evaluation metrics.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation import AnswerEvaluator, track_response_time


class TestAnswerEvaluator(unittest.TestCase):
    """Test cases for AnswerEvaluator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = AnswerEvaluator()
    
    def test_evaluator_initialization(self):
        """Test evaluator initializes correctly."""
        self.assertIsNotNone(self.evaluator)
        self.assertIsNone(self.evaluator.embedding_model)
    
    def test_answer_relevance_with_fallback(self):
        """Test answer relevance calculation without embedding model."""
        question = "How to check tire pressure?"
        answer = "Use a tire pressure gauge to check the tire pressure."
        
        score = self.evaluator.calculate_answer_relevance(question, answer)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertGreater(score, 0.2)  # Should have some overlap
    
    def test_answer_relevance_empty_inputs(self):
        """Test answer relevance with empty inputs."""
        self.assertEqual(self.evaluator.calculate_answer_relevance("", ""), 0.0)
        self.assertEqual(self.evaluator.calculate_answer_relevance("question", ""), 0.0)
        self.assertEqual(self.evaluator.calculate_answer_relevance("", "answer"), 0.0)
    
    def test_faithfulness_calculation(self):
        """Test faithfulness score calculation."""
        answer = "The recommended tire pressure is 32 PSI."
        context = ["Tire pressure should be maintained at 32 PSI for optimal performance."]
        
        score = self.evaluator.calculate_faithfulness(answer, context)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertGreater(score, 0.5)  # Should have good overlap
    
    def test_faithfulness_empty_context(self):
        """Test faithfulness with empty context."""
        score = self.evaluator.calculate_faithfulness("answer", [])
        self.assertEqual(score, 0.0)
    
    def test_evaluate_answer(self):
        """Test complete answer evaluation."""
        question = "What is the engine oil specification?"
        answer = "Use SAE 5W-30 engine oil."
        context = ["The recommended engine oil is SAE 5W-30 or SAE 10W-40."]
        
        metrics = self.evaluator.evaluate_answer(question, answer, context)
        
        # Check all metrics are present
        self.assertIn('answer_relevance', metrics)
        self.assertIn('faithfulness', metrics)
        self.assertIn('context_relevance', metrics)
        self.assertIn('overall_score', metrics)
        
        # Check all metrics are in valid range
        for key, value in metrics.items():
            self.assertIsInstance(value, float)
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
    
    def test_quality_rating(self):
        """Test quality rating conversion."""
        rating, emoji = self.evaluator.get_quality_rating(0.85)
        self.assertEqual(rating, "Excellent")
        self.assertEqual(emoji, "🟢")
        
        rating, emoji = self.evaluator.get_quality_rating(0.65)
        self.assertEqual(rating, "Good")
        self.assertEqual(emoji, "🟡")
        
        rating, emoji = self.evaluator.get_quality_rating(0.45)
        self.assertEqual(rating, "Fair")
        self.assertEqual(emoji, "🟠")
        
        rating, emoji = self.evaluator.get_quality_rating(0.25)
        self.assertEqual(rating, "Poor")
        self.assertEqual(emoji, "🔴")
    
    def test_keyword_overlap_score(self):
        """Test fallback keyword overlap scoring."""
        text1 = "engine oil specification SAE 5W-30"
        text2 = "recommended engine oil is SAE 5W-30"
        
        score = self.evaluator._keyword_overlap_score(text1, text2)
        
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_content_overlap_score(self):
        """Test content overlap scoring."""
        answer = "Use SAE 5W-30 engine oil"
        context = "The recommended oil is SAE 5W-30 synthetic engine oil"
        
        score = self.evaluator._content_overlap_score(answer, context)
        
        self.assertGreater(score, 0.5)  # Should have good overlap
        self.assertLessEqual(score, 1.0)


class TestResponseTimeDecorator(unittest.TestCase):
    """Test cases for response time tracking decorator."""
    
    def test_decorator_adds_response_time(self):
        """Test that decorator adds response_time to result."""
        import time
        
        @track_response_time
        def sample_function():
            time.sleep(0.001)  # Small delay to ensure measurable time
            return {"answer": "test"}
        
        result = sample_function()
        
        self.assertIn('response_time', result)
        self.assertIsInstance(result['response_time'], float)
        self.assertGreaterEqual(result['response_time'], 0.0)
    
    def test_decorator_with_non_dict_return(self):
        """Test decorator with non-dictionary return value."""
        
        @track_response_time
        def sample_function():
            return "string result"
        
        result = sample_function()
        
        # Should return original value if not dict
        self.assertEqual(result, "string result")


if __name__ == '__main__':
    unittest.main()

