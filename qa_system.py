"""
Q&A System Module
Generates answers from retrieved manual chunks.
"""

from typing import List, Dict
import re


class QASystem:
    """Simple Q&A system that generates answers from retrieved chunks."""
    
    def __init__(self):
        pass
    
    def generate_answer(self, question: str, search_results: List[Dict]) -> Dict:
        """Generate an answer from search results."""
        if not search_results:
            return {
                "answer": "I couldn't find relevant information in the manual to answer your question.",
                "citations": []
            }
        
        # Combine top results
        combined_context = "\n\n".join([result["text"] for result in search_results[:3]])
        
        # Simple extraction: try to find direct answers
        answer = self._extract_answer(question, combined_context, search_results)
        
        # Format citations
        citations = []
        for i, result in enumerate(search_results[:3], 1):
            citations.append({
                "citation_number": i,
                "car_model": result["car_model"],
                "excerpt": result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"]
            })
        
        return {
            "answer": answer,
            "citations": citations,
            "confidence": "medium"  # Simple extraction has medium confidence
        }
    
    def _extract_answer(self, question: str, context: str, search_results: List[Dict]) -> str:
        """Extract or generate answer from context."""
        question_lower = question.lower()
        
        # Try to find direct sentences that might answer the question
        sentences = re.split(r'[.!?]\s+', context)
        relevant_sentences = []
        
        # Extract keywords from question
        question_keywords = set(re.findall(r'\b\w+\b', question_lower))
        question_keywords.discard('how')
        question_keywords.discard('to')
        question_keywords.discard('what')
        question_keywords.discard('which')
        question_keywords.discard('where')
        question_keywords.discard('when')
        question_keywords.discard('why')
        question_keywords.discard('is')
        question_keywords.discard('are')
        question_keywords.discard('the')
        question_keywords.discard('a')
        question_keywords.discard('an')
        
        # Score sentences by keyword matches
        for sentence in sentences:
            sentence_lower = sentence.lower()
            score = sum(1 for keyword in question_keywords if keyword in sentence_lower)
            if score > 0:
                relevant_sentences.append((score, sentence.strip()))
        
        # Sort by relevance
        relevant_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # Build answer from top sentences
        if relevant_sentences:
            answer_sentences = [sent[1] for sent in relevant_sentences[:3]]
            answer = " ".join(answer_sentences)
            
            # Clean up the answer
            answer = re.sub(r'\s+', ' ', answer).strip()
            
            # If answer is too short, use more context
            if len(answer) < 50:
                answer = search_results[0]["text"][:500]
            
            return answer
        else:
            # Fallback: return the most relevant chunk
            return search_results[0]["text"][:500]
    
    def format_answer_with_citations(self, answer_data: Dict) -> str:
        """Format answer with inline citations."""
        answer = answer_data["answer"]
        citations = answer_data["citations"]
        
        formatted = f"{answer}\n\n"
        formatted += "**Sources:**\n"
        for citation in citations:
            formatted += f"[{citation['citation_number']}] {citation['car_model']}: {citation['excerpt']}\n\n"
        
        return formatted
