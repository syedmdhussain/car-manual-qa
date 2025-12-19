"""
Search Engine Module
Implements semantic search using sentence transformers and FAISS.
"""

import os
import json
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import faiss


class ManualSearchEngine:
    """Search engine for car manual content using semantic search."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the search engine with a sentence transformer model."""
        print(f"Loading sentence transformer model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.manuals_data = {}
        self.index = None
        self.chunk_metadata = []
        
    def build_index(self, manuals_data: Dict):
        """Build FAISS index from manual chunks."""
        self.manuals_data = manuals_data
        all_chunks = []
        self.chunk_metadata = []
        
        # Collect all chunks with metadata
        for model, data in manuals_data.items():
            for idx, chunk in enumerate(data["chunks"]):
                all_chunks.append(chunk["text"])
                self.chunk_metadata.append({
                    "car_model": model,
                    "chunk_index": idx,
                    "start_word": chunk.get("start_word", 0),
                    "end_word": chunk.get("end_word", 0)
                })
        
        if not all_chunks:
            print("No chunks found to index!")
            return
        
        # Generate embeddings
        print(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = self.model.encode(all_chunks, show_progress_bar=True)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        
        print(f"Index built with {self.index.ntotal} vectors")
    
    def search(self, query: str, car_model: str = None, top_k: int = 5) -> List[Dict]:
        """Search for relevant chunks."""
        if self.index is None or len(self.chunk_metadata) == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        
        # Search in index
        k = min(top_k * 2, self.index.ntotal)  # Get more results to filter by model
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            metadata = self.chunk_metadata[idx]
            
            # Filter by car model if specified
            if car_model and metadata["car_model"] != car_model:
                continue
            
            chunk_data = self.manuals_data[metadata["car_model"]]["chunks"][metadata["chunk_index"]]
            
            results.append({
                "text": chunk_data["text"],
                "car_model": metadata["car_model"],
                "distance": float(dist),
                "chunk_index": metadata["chunk_index"]
            })
            
            if len(results) >= top_k:
                break
        
        return results
    
    def simple_keyword_search(self, query: str, car_model: str = None, top_k: int = 5) -> List[Dict]:
        """Fallback simple keyword-based search."""
        query_words = set(query.lower().split())
        results = []
        
        for model, data in self.manuals_data.items():
            if car_model and model != car_model:
                continue
            
            for idx, chunk in enumerate(data["chunks"]):
                chunk_text_lower = chunk["text"].lower()
                score = sum(1 for word in query_words if word in chunk_text_lower)
                
                if score > 0:
                    results.append({
                        "text": chunk["text"],
                        "car_model": model,
                        "score": score,
                        "chunk_index": idx
                    })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
