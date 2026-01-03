"""
Search Engine Module
Implements semantic search using sentence transformers and FAISS.
Performance optimized with persistent indexes, lazy loading, and caching.
"""

import os
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import faiss


class ManualSearchEngine:
    """Search engine for car manual content using semantic search."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "faiss_index.bin"):
        """
        Initialize the search engine with lazy model loading.
        
        Args:
            model_name: Sentence transformer model name
            index_path: Path to save/load FAISS index
        """
        self.model_name = model_name
        self.model = None  # Load lazily on first use
        self.manuals_data = {}
        self.index = None
        self.chunk_metadata = []
        self.index_path = index_path
        self.metadata_path = "faiss_metadata.json"
        
        # Query embedding cache (LRU-style, max 100 queries)
        self._query_cache = {}
        self._cache_size = 100
    
    def _ensure_model_loaded(self):
        """Load sentence transformer model if not already loaded."""
        if self.model is None:
            print(f"Loading sentence transformer model: {self.model_name}...")
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model = SentenceTransformer(self.model_name, device=device)
            # Ensure model is on correct device
            self.model.to(device)
    
    def _get_cached_embedding(self, query: str) -> np.ndarray:
        """
        Get cached query embedding or generate new one.
        
        Args:
            query: Search query string
            
        Returns:
            Query embedding vector
        """
        query_lower = query.lower().strip()
        
        # Check cache
        if query_lower in self._query_cache:
            return self._query_cache[query_lower]
        
        # Generate new embedding
        self._ensure_model_loaded()
        embedding = self.model.encode([query])[0]
        
        # Simple LRU: remove oldest if cache full
        if len(self._query_cache) >= self._cache_size:
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]
        
        self._query_cache[query_lower] = embedding
        return embedding
        
    def build_index(self, manuals_data: Dict, force_rebuild: bool = False):
        """
        Build FAISS index from manual chunks.
        
        Args:
            manuals_data: Dictionary of manual data
            force_rebuild: Force rebuild even if cached index exists
        """
        # Try to load existing index first
        if not force_rebuild and self.load_index():
            print("Using cached FAISS index")
            self.manuals_data = manuals_data
            return
        
        print("Building new FAISS index...")
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
        self._ensure_model_loaded()
        print(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = self.model.encode(all_chunks, show_progress_bar=True)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        
        print(f"Index built with {self.index.ntotal} vectors")
        
        # Save index for future use
        self.save_index()
    
    def save_index(self):
        """Save FAISS index and metadata to disk."""
        if self.index is None or len(self.chunk_metadata) == 0:
            return
        
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.chunk_metadata, f, indent=2)
            print(f"Index saved to {self.index_path}")
        except Exception as e:
            print(f"Warning: Could not save index: {e}")
    
    def load_index(self) -> bool:
        """
        Load FAISS index and metadata from disk.
        
        Returns:
            True if index loaded successfully, False otherwise
        """
        if not os.path.exists(self.index_path) or not os.path.exists(self.metadata_path):
            return False
        
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.chunk_metadata = json.load(f)
            print(f"Index loaded from {self.index_path} ({self.index.ntotal} vectors)")
            return True
        except Exception as e:
            print(f"Warning: Could not load index: {e}")
            return False
    
    def search(self, query: str, car_model: str = None, top_k: int = 5) -> List[Dict]:
        """
        Search for relevant chunks using cached embeddings when possible.
        
        Args:
            query: Search query string
            car_model: Optional car model to filter results
            top_k: Number of results to return
            
        Returns:
            List of search results with text, car_model, distance, and chunk_index
        """
        if self.index is None or len(self.chunk_metadata) == 0:
            return []
        
        # Get query embedding (from cache if available)
        query_embedding = self._get_cached_embedding(query)
        
        # Ensure 2D array for FAISS (shape: [1, dimension])
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Search in index
        k = min(top_k * 2, self.index.ntotal)  # Get more results to filter by model
        distances, indices = self.index.search(
            query_embedding.astype('float32'), 
            k
        )
        
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
