"""
Evaluation Module
Provides metrics to evaluate answer quality in the RAG system.
"""

import time
import numpy as np
from typing import Dict, List, Tuple
from functools import wraps


class AnswerEvaluator:
    """Evaluates answer quality using multiple metrics."""
    
    def __init__(self, embedding_model=None):
        """
        Initialize evaluator with optional embedding model.
        
        Args:
            embedding_model: SentenceTransformer model for semantic similarity
        """
        self.embedding_model = embedding_model
    
    def evaluate_answer(self, question: str, answer: str, context_chunks: List[str]) -> Dict:
        """
        Evaluate answer quality using multiple metrics.
        
        Args:
            question: The user's question
            answer: The generated answer
            context_chunks: List of retrieved context chunks
            
        Returns:
            Dictionary with evaluation metrics
        """
        metrics = {}
        
        # 1. Answer Relevance Score
        metrics['answer_relevance'] = self.calculate_answer_relevance(question, answer)
        
        # 2. Faithfulness Score
        metrics['faithfulness'] = self.calculate_faithfulness(answer, context_chunks)
        
        # 3. Context Relevance (average)
        if context_chunks:
            context_relevances = [
                self.calculate_answer_relevance(question, chunk) 
                for chunk in context_chunks[:3]
            ]
            metrics['context_relevance'] = np.mean(context_relevances)
        else:
            metrics['context_relevance'] = 0.0
        
        # 4. Overall quality score (weighted average)
        metrics['overall_score'] = self._calculate_overall_score(metrics)
        
        return metrics
    
    def calculate_answer_relevance(self, question: str, answer: str) -> float:
        """
        Calculate semantic similarity between question and answer.
        Higher score means answer is more relevant to the question.
        
        Args:
            question: The user's question
            answer: The generated answer
            
        Returns:
            Relevance score between 0 and 1
        """
        if not question or not answer:
            return 0.0
        
        if self.embedding_model is None:
            # Fallback: simple keyword overlap
            return self._keyword_overlap_score(question, answer)
        
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode([question, answer])
            
            # Calculate cosine similarity
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            # Normalize to 0-1 range (cosine similarity is -1 to 1)
            score = (similarity + 1) / 2
            
            return float(score)
        except Exception as e:
            print(f"Error calculating answer relevance: {e}")
            return 0.5  # Neutral score on error
    
    def calculate_faithfulness(self, answer: str, context_chunks: List[str]) -> float:
        """
        Check if answer is faithful to the context (no hallucinations).
        Uses semantic similarity to ensure answer content is grounded in context.
        
        Args:
            answer: The generated answer
            context_chunks: List of context chunks the answer should be based on
            
        Returns:
            Faithfulness score between 0 and 1
        """
        if not answer or not context_chunks:
            return 0.0
        
        # Combine context
        combined_context = " ".join(context_chunks)
        
        if self.embedding_model is None:
            # Fallback: check if answer words appear in context
            return self._content_overlap_score(answer, combined_context)
        
        try:
            # Split answer into sentences
            answer_sentences = self._split_sentences(answer)
            
            if not answer_sentences:
                return 0.0
            
            # Check each sentence against context
            faithfulness_scores = []
            
            for sentence in answer_sentences:
                # Encode sentence and context
                embeddings = self.embedding_model.encode([sentence, combined_context])
                
                # Calculate similarity
                similarity = np.dot(embeddings[0], embeddings[1]) / (
                    np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
                )
                
                # Normalize to 0-1
                score = (similarity + 1) / 2
                faithfulness_scores.append(score)
            
            # Return average faithfulness across all sentences
            return float(np.mean(faithfulness_scores))
        
        except Exception as e:
            print(f"Error calculating faithfulness: {e}")
            return 0.5  # Neutral score on error
    
    def _calculate_overall_score(self, metrics: Dict) -> float:
        """
        Calculate weighted overall quality score.
        
        Weights:
        - Answer Relevance: 40% (most important - does it answer the question?)
        - Faithfulness: 40% (equally important - no hallucinations)
        - Context Relevance: 20% (supporting factor)
        """
        weights = {
            'answer_relevance': 0.4,
            'faithfulness': 0.4,
            'context_relevance': 0.2
        }
        
        score = (
            metrics.get('answer_relevance', 0) * weights['answer_relevance'] +
            metrics.get('faithfulness', 0) * weights['faithfulness'] +
            metrics.get('context_relevance', 0) * weights['context_relevance']
        )
        
        return float(score)
    
    def _keyword_overlap_score(self, text1: str, text2: str) -> float:
        """Fallback: simple keyword overlap score."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Remove common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'}
        words1 = words1 - stopwords
        words2 = words2 - stopwords
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1.intersection(words2))
        return overlap / max(len(words1), len(words2))
    
    def _content_overlap_score(self, answer: str, context: str) -> float:
        """Check what percentage of answer content appears in context."""
        answer_words = set(answer.lower().split())
        context_words = set(context.lower().split())
        
        # Remove stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
        answer_words = answer_words - stopwords
        
        if not answer_words:
            return 0.0
        
        # How many answer words appear in context?
        overlap = len(answer_words.intersection(context_words))
        return overlap / len(answer_words)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Simple sentence splitter."""
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def get_quality_rating(self, score: float) -> Tuple[str, str]:
        """
        Convert numeric score to quality rating.
        
        Returns:
            Tuple of (rating, emoji)
        """
        if score >= 0.8:
            return "Excellent", "🟢"
        elif score >= 0.6:
            return "Good", "🟡"
        elif score >= 0.4:
            return "Fair", "🟠"
        else:
            return "Poor", "🔴"


def track_response_time(func):
    """
    Decorator to track response time of a function.
    Adds 'response_time' to the returned dictionary.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Add response time to result if it's a dictionary
        if isinstance(result, dict):
            result['response_time'] = response_time
        
        return result
    
    return wrapper

