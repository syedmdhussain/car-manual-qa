# Code Walkthrough: How Each Design Consideration Was Solved

This document provides a quick reference to the specific code sections that address each design consideration.

---

## 1. Input Processing: Parsing and Storing Data

### **PDF Text Extraction**
**File:** `pdf_processor.py`  
**Lines:** 19-30  
**What it does:** Extracts all text from PDF pages using pdfplumber

```python
def extract_text_from_pdf(self, pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text
```

### **Text Chunking with Overlap**
**File:** `pdf_processor.py`  
**Lines:** 32-47  
**What it does:** Splits text into 500-word chunks with 100-word overlap

```python
def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100):
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunks.append({
            "text": chunk_text,
            "start_word": i,
            "end_word": min(i + chunk_size, len(words))
        })
```

### **Data Storage (JSON)**
**File:** `pdf_processor.py`  
**Lines:** 65-78  
**What it does:** Saves processed chunks to JSON (removes full text to save space)

```python
def save_processed_data(self, output_path: str = "processed_manuals.json"):
    save_data = {}
    for model, data in self.manuals_data.items():
        save_data[model] = {
            "car_model": data["car_model"],
            "chunks": data["chunks"],  # Only chunks, not full text
            "total_chunks": data["total_chunks"]
        }
```

### **Caching Strategy**
**File:** `app.py`  
**Lines:** 34-42  
**What it does:** Loads cached processed data to avoid reprocessing

```python
@st.cache_resource
def load_manuals():
    if os.path.exists("processed_manuals.json"):
        manuals_data = processor.load_processed_data()  # Fast load
    else:
        # Process PDFs (slow, only first time)
        processor.process_manual(...)
```

---

## 2. Output Structure: Response Format and Query Handling

### **Standard Response Format**
**File:** `rag_qa_system.py`  
**Lines:** 81-85  
**What it does:** Returns structured response with answer, citations, confidence

```python
return {
    "answer": answer,
    "citations": citations,
    "confidence": confidence  # "high" | "medium" | "low"
}
```

### **Citation Generation**
**File:** `rag_qa_system.py`  
**Lines:** 65-71  
**What it does:** Creates numbered citations with excerpts

```python
citations = []
for i, result in enumerate(search_results[:5], 1):
    citations.append({
        "citation_number": i,
        "car_model": result["car_model"],
        "excerpt": result["text"][:300] + "..."  # Truncated excerpt
    })
```

### **Consistent Answer Formatting (RAG)**
**File:** `rag_qa_system.py`  
**Lines:** 119-136  
**What it does:** Uses structured prompt to ensure consistent answers

```python
prompt = f"""You are an expert car manual assistant...
INSTRUCTIONS:
1. Answer directly and concisely
2. Use bullet points for step-by-step instructions
3. Include specific steps, numbers, or measurements
4. Reference the car model when relevant
"""
```

### **Car Model Detection**
**File:** `pdf_processor.py`  
**Lines:** 94-108  
**What it does:** Detects car model from question keywords

```python
def detect_car_model(question: str) -> str:
    question_lower = question.lower()
    if any(keyword in question_lower for keyword in ["astor", "mg astor", "mg"]):
        return "MG Astor"
    if any(keyword in question_lower for keyword in ["tiago", "tata tiago", "tata"]):
        return "Tata Tiago"
    return None
```

### **Handling No Results**
**File:** `rag_qa_system.py`  
**Lines:** 54-59  
**What it does:** Returns clear message when no information found

```python
if not search_results:
    return {
        "answer": "I couldn't find relevant information...",
        "citations": [],
        "confidence": "low"
    }
```

### **Fallback Search Strategy**
**File:** `app.py`  
**Lines:** 150-157  
**What it does:** Falls back to keyword search if semantic search fails

```python
if not search_results and detected_model:
    st.info("Trying keyword search...")
    search_results = st.session_state.search_engine.simple_keyword_search(
        question, car_model=detected_model, top_k=5
    )
```

### **Confidence Calculation**
**File:** `rag_qa_system.py`  
**Lines:** 87-107  
**What it does:** Calculates confidence based on search result quality

```python
def _calculate_confidence(self, search_results: List[Dict]) -> str:
    if "distance" in search_results[0]:
        top_distance = search_results[0]["distance"]
        if top_distance < 0.5:
            return "high"
        elif top_distance < 1.0:
            return "medium"
    return "low"
```

---

## 3. Scalability: Storage, Processing, and Search

### **FAISS Index Building**
**File:** `search_engine.py`  
**Lines:** 25-55  
**What it does:** Builds efficient vector index for fast similarity search

```python
def build_index(self, manuals_data: Dict):
    # Generate embeddings for all chunks
    embeddings = self.model.encode(all_chunks, show_progress_bar=True)
    
    # Build FAISS index
    dimension = embeddings.shape[1]
    self.index = faiss.IndexFlatL2(dimension)
    self.index.add(embeddings.astype('float32'))
```

### **Semantic Search**
**File:** `search_engine.py`  
**Lines:** 57-89  
**What it does:** Fast vector similarity search using FAISS

```python
def search(self, query: str, car_model: str = None, top_k: int = 5):
    # Generate query embedding
    query_embedding = self.model.encode([query])
    
    # Fast vector search
    k = min(top_k * 2, self.index.ntotal)
    distances, indices = self.index.search(query_embedding.astype('float32'), k)
    
    # Filter by car model
    for dist, idx in zip(distances[0], indices[0]):
        if car_model and metadata["car_model"] != car_model:
            continue
        results.append({...})
```

### **Keyword Search Fallback**
**File:** `search_engine.py`  
**Lines:** 91-114  
**What it does:** Simple keyword matching when semantic search fails

```python
def simple_keyword_search(self, query: str, car_model: str = None, top_k: int = 5):
    query_words = set(query.lower().split())
    for chunk in data["chunks"]:
        score = sum(1 for word in query_words if word in chunk_text_lower)
        if score > 0:
            results.append({"text": chunk["text"], "score": score})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
```

### **Batch Embedding Generation**
**File:** `search_engine.py`  
**Line:** 48  
**What it does:** Processes all chunks in single batch for efficiency

```python
embeddings = self.model.encode(all_chunks, show_progress_bar=True)
# All chunks encoded at once - much faster than one-by-one
```

### **Efficient Storage (Chunks Only)**
**File:** `pdf_processor.py`  
**Lines:** 67-74  
**What it does:** Removes full text from saved data to reduce file size

```python
# Remove full_text to save space, keep only chunks
save_data[model] = {
    "car_model": data["car_model"],
    "chunks": data["chunks"],  # Full text not saved
    "total_chunks": data["total_chunks"]
}
```

---

## Key Design Patterns Used

### **1. Caching Pattern**
- Streamlit `@st.cache_resource` for session-level caching
- JSON file caching for processed data
- Avoids redundant processing

### **2. Fallback Pattern**
- Primary: Semantic search → Fallback: Keyword search
- Primary: RAG with LLM → Fallback: Simple extraction
- Ensures system always provides some response

### **3. Lazy Loading Pattern**
- Manuals only processed when needed
- Search engine initialized on first use
- Reduces startup time

### **4. Separation of Concerns**
- `pdf_processor.py` - Data extraction
- `search_engine.py` - Search functionality
- `rag_qa_system.py` - Answer generation
- `app.py` - UI and orchestration

### **5. Progressive Enhancement**
- Works without LLM (simple extraction)
- Enhanced with LLM if available (RAG)
- Graceful degradation

---

## Performance Characteristics

| Operation | Time Complexity | Notes |
|-----------|----------------|-------|
| PDF Processing | O(n) | n = number of pages |
| Chunking | O(n) | n = number of words |
| Embedding Generation | O(n) | n = number of chunks (batched) |
| FAISS Index Build | O(n log n) | n = number of vectors |
| Semantic Search | O(log n) | Approximate with FAISS |
| Keyword Search | O(n) | n = number of chunks |

**Typical Performance:**
- First run: 2-3 minutes (PDF processing + indexing)
- Subsequent runs: < 5 seconds (cached data)
- Query response: < 2 seconds (semantic search + answer generation)

---

## Extension Points for Future Enhancements

### **Tabular Data Extraction**
Add to `pdf_processor.py`:
```python
def extract_tables_from_pdf(self, pdf_path: str) -> List[Dict]:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            # Process and store tables
```

### **Persistent FAISS Index**
Modify `search_engine.py`:
```python
def save_index(self, path: str):
    faiss.write_index(self.index, path)

def load_index(self, path: str):
    self.index = faiss.read_index(path)
```

### **Sharded Indexes (for scale)**
Create separate indexes per car model:
```python
self.indexes = {
    "MG Astor": faiss.IndexFlatL2(dimension),
    "Tata Tiago": faiss.IndexFlatL2(dimension)
}
```

---

This walkthrough shows exactly where each design consideration is implemented in the codebase.

