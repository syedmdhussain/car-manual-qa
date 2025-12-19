"""
RAG-based Q&A System Module
Uses Retrieval-Augmented Generation with LLMs for better answers.
"""

from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class RAGQASystem:
    """RAG-based Q&A system using LLMs."""
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize RAG Q&A system.
        
        Args:
            use_llm: Whether to use LLM (requires API key) or fallback to simple extraction
        """
        self.use_llm = use_llm
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Check if we can use LLM
        if use_llm:
            if self.openai_api_key:
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=self.openai_api_key)
                    self.llm_provider = "openai"
                    print("✅ Using OpenAI for RAG")
                except Exception as e:
                    print(f"⚠️ OpenAI initialization failed: {e}")
                    self.use_llm = False
            else:
                # Try Ollama as fallback
                try:
                    import requests
                    response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
                    if response.status_code == 200:
                        self.llm_provider = "ollama"
                        print("✅ Using Ollama for RAG")
                    else:
                        self.use_llm = False
                except:
                    self.use_llm = False
                    print("⚠️ No LLM available, using simple extraction")
    
    def generate_answer(self, question: str, search_results: List[Dict]) -> Dict:
        """Generate an answer using RAG."""
        if not search_results:
            return {
                "answer": "I couldn't find relevant information in the manual to answer your question.",
                "citations": [],
                "confidence": "low"
            }
        
        # Calculate confidence based on search result quality
        confidence = self._calculate_confidence(search_results)
        
        # Format citations
        citations = []
        for i, result in enumerate(search_results[:5], 1):
            citations.append({
                "citation_number": i,
                "car_model": result["car_model"],
                "excerpt": result["text"][:300] + "..." if len(result["text"]) > 300 else result["text"]
            })
        
        # Use LLM if available, otherwise fallback
        if self.use_llm and self.llm_provider == "openai":
            answer = self._generate_with_openai(question, search_results)
        elif self.use_llm and self.llm_provider == "ollama":
            answer = self._generate_with_ollama(question, search_results)
        else:
            answer = self._simple_extraction(question, search_results)
        
        return {
            "answer": answer,
            "citations": citations,
            "confidence": confidence
        }
    
    def _calculate_confidence(self, search_results: List[Dict]) -> str:
        """Calculate confidence level based on search result quality."""
        if not search_results:
            return "low"
        
        # Check distance scores (lower is better for semantic search)
        if "distance" in search_results[0]:
            top_distance = search_results[0]["distance"]
            # Normalize: lower distance = higher confidence
            if top_distance < 0.5:
                return "high"
            elif top_distance < 1.0:
                return "medium"
            else:
                return "low"
        
        # If we have multiple good results, confidence is higher
        if len(search_results) >= 3:
            return "medium"
        
        return "low"
    
    def _generate_with_openai(self, question: str, search_results: List[Dict]) -> str:
        """Generate answer using OpenAI API."""
        try:
            # Prepare context from top results
            context_chunks = []
            for i, result in enumerate(search_results[:5], 1):
                context_chunks.append(f"[Source {i} from {result['car_model']} Manual]:\n{result['text']}\n")
            
            context = "\n".join(context_chunks)
            
            # Create improved prompt
            car_model = search_results[0]["car_model"] if search_results else "the car"
            prompt = f"""You are an expert car manual assistant. Answer the user's question based ONLY on the provided manual excerpts from the {car_model} owner's manual.

MANUAL EXCERPTS:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer directly and concisely based ONLY on the provided manual excerpts
2. If the information is not in the excerpts, clearly state: "I couldn't find specific information about this in the {car_model} manual"
3. Include specific steps, numbers, or measurements when mentioned in the manual
4. Use bullet points for step-by-step instructions
5. Reference the car model ({car_model}) when relevant
6. Be helpful and clear, as if explaining to a car owner

ANSWER:"""
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Can be changed to gpt-4 for better results
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions about car manuals."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error with OpenAI: {e}")
            return self._simple_extraction(question, search_results)
    
    def _generate_with_ollama(self, question: str, search_results: List[Dict]) -> str:
        """Generate answer using Ollama (local LLM)."""
        try:
            import requests
            
            # Prepare context
            context_chunks = []
            for i, result in enumerate(search_results[:5], 1):
                context_chunks.append(f"[Source {i} from {result['car_model']} Manual]:\n{result['text']}\n")
            
            context = "\n".join(context_chunks)
            
            prompt = f"""Answer this question about car manuals based on the provided context:

Context:
{context}

Question: {question}

Answer based only on the context provided. Be concise and clear."""

            # Call Ollama
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": "llama2",  # Change to your preferred model
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                return self._simple_extraction(question, search_results)
                
        except Exception as e:
            print(f"Error with Ollama: {e}")
            return self._simple_extraction(question, search_results)
    
    def _simple_extraction(self, question: str, search_results: List[Dict]) -> str:
        """Fallback simple extraction method."""
        # Combine top results
        combined_context = "\n\n".join([result["text"] for result in search_results[:3]])
        
        # Simple answer: return the most relevant chunk with some formatting
        if search_results:
            answer = search_results[0]["text"]
            # Try to extract a relevant paragraph
            sentences = answer.split('. ')
            if len(sentences) > 1:
                # Return first few sentences
                answer = '. '.join(sentences[:3]) + '.'
            return answer[:500]
        
        return "I couldn't find relevant information to answer your question."
