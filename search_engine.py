"""
Search Engine Module
Implements semantic search using sentence transformers and FAISS.
"""

import os
import json
import hashlib
from typing import List, Dict, Optional


class ManualSearchEngine:
    """Search engine for car manual content using semantic search."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = ".cache"):
        """Initialize the search engine.

        Notes:
        - The embedding model is lazily loaded to reduce startup time.
        - The FAISS index can be persisted to disk to avoid rebuilding.
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self._model = None
        self.manuals_data = {}
        self.index = None
        self.chunk_metadata = []

    def _ensure_model_loaded(self):
        """Lazy-load the sentence transformer model."""
        if self._model is not None:
            return
        # Import heavy deps only when needed (improves app startup time).
        try:
            from sentence_transformers import SentenceTransformer
        except ModuleNotFoundError as e:
            raise RuntimeError(
                "Semantic search requires 'sentence-transformers'. "
                "Install dependencies (e.g. `pip install -r requirements.txt`) and retry."
            ) from e

        print(f"Loading sentence transformer model: {self.model_name}...")
        self._model = SentenceTransformer(self.model_name)

    @staticmethod
    def _sha256_bytes(data: bytes) -> str:
        h = hashlib.sha256()
        h.update(data)
        return h.hexdigest()

    @staticmethod
    def _fingerprint_manuals(manuals_data: Dict) -> str:
        """Create a stable-ish fingerprint for manuals/chunks content.

        This is only used when a caller doesn't provide an explicit fingerprint.
        """
        h = hashlib.sha256()
        # Sort keys for determinism
        for model in sorted(manuals_data.keys()):
            h.update(model.encode("utf-8", errors="ignore"))
            h.update(b"\0")
            chunks = manuals_data.get(model, {}).get("chunks", []) or []
            h.update(str(len(chunks)).encode("utf-8"))
            h.update(b"\0")
            # Hash chunk texts incrementally to avoid giant allocations
            for ch in chunks:
                text = (ch.get("text") or "").encode("utf-8", errors="ignore")
                h.update(text)
                h.update(b"\0")
        return h.hexdigest()

    def _cache_paths(self, fingerprint: str, cache_dir: Optional[str] = None) -> tuple[str, str]:
        cache_dir = cache_dir or self.cache_dir
        safe_model = "".join(c for c in self.model_name if c.isalnum() or c in ("-", "_")).strip() or "model"
        prefix = f"manual_index_{safe_model}_{fingerprint}"
        index_path = os.path.join(cache_dir, f"{prefix}.faiss")
        meta_path = os.path.join(cache_dir, f"{prefix}.meta.json")
        return index_path, meta_path
        
    def build_index(
        self,
        manuals_data: Dict,
        *,
        fingerprint: Optional[str] = None,
        cache_dir: Optional[str] = None,
        force_rebuild: bool = False,
    ):
        """Build (or load) a FAISS index from manual chunks."""
        cache_dir = cache_dir or self.cache_dir
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

        fp = fingerprint or self._fingerprint_manuals(manuals_data)
        index_path, meta_path = self._cache_paths(fp, cache_dir=cache_dir)

        # Fast path: load cached index + metadata.
        if not force_rebuild and os.path.exists(index_path) and os.path.exists(meta_path):
            try:
                try:
                    import faiss
                except ModuleNotFoundError as e:
                    raise RuntimeError(
                        "Semantic search requires 'faiss-cpu'. "
                        "Install dependencies (e.g. `pip install -r requirements.txt`) and retry."
                    ) from e

                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                # Minimal compatibility check
                if meta.get("model_name") == self.model_name and meta.get("fingerprint") == fp:
                    self.index = faiss.read_index(index_path)
                    self.chunk_metadata = meta.get("chunk_metadata", [])
                    print(f"Loaded cached index ({self.index.ntotal} vectors) from {index_path}")
                    return
            except Exception as e:
                print(f"⚠️ Failed to load cached index, rebuilding: {e}")
        
        # Generate embeddings
        print(f"Generating embeddings for {len(all_chunks)} chunks...")
        self._ensure_model_loaded()
        embeddings = self._model.encode(
            all_chunks,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        try:
            import faiss
        except ModuleNotFoundError as e:
            raise RuntimeError(
                "Semantic search requires 'faiss-cpu'. "
                "Install dependencies (e.g. `pip install -r requirements.txt`) and retry."
            ) from e

        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype("float32", copy=False))
        
        print(f"Index built with {self.index.ntotal} vectors")

        # Persist to disk for faster subsequent startups.
        try:
            os.makedirs(cache_dir, exist_ok=True)
            faiss.write_index(self.index, index_path)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "model_name": self.model_name,
                        "fingerprint": fp,
                        "chunk_metadata": self.chunk_metadata,
                    },
                    f,
                    ensure_ascii=False,
                )
            print(f"Cached index saved to {index_path}")
        except Exception as e:
            print(f"⚠️ Failed to persist index cache: {e}")
    
    def search(self, query: str, car_model: str = None, top_k: int = 5) -> List[Dict]:
        """Search for relevant chunks."""
        if self.index is None or len(self.chunk_metadata) == 0:
            return []
        
        # Generate query embedding
        self._ensure_model_loaded()
        query_embedding = self._model.encode(
            [query],
            batch_size=1,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        
        # Search in index
        k = min(max(top_k * 6, top_k), self.index.ntotal)  # Over-fetch to allow model filtering
        distances, indices = self.index.search(query_embedding.astype("float32", copy=False), k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
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
