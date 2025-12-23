# Design Considerations - Detailed Explanation

This document explains how the Car Manual Q&A system addresses the three key design considerations.

---

## 1. Input Processing: Parsing and Storing Data

### **Textual Information Processing (Primary Focus)**

#### **PDF Text Extraction** (`pdf_processor.py`)

**How it works:**
- Uses `pdfplumber` library to extract text from PDF manuals
- Processes each page sequentially and concatenates all text
- Handles errors gracefully if PDF parsing fails

**Code Location:** `pdf_processor.py`, lines 19-30
```python
def extract_text_from_pdf(self, pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text
```

#### **Text Chunking Strategy**

**Why chunking?**
- Large documents can't fit in LLM context windows
- Chunking enables efficient search and retrieval
- Overlapping chunks preserve context across boundaries

**Implementation Details:**
- **Chunk size:** 500 words (configurable)
- **Overlap:** 100 words between chunks
- **Metadata stored:** Start/end word positions for each chunk

**Code Location:** `pdf_processor.py`, lines 32-47
```python
def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict]:
    """Split text into chunks with metadata."""
    chunks = []
    words = text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        
        chunks.append({
            "text": chunk_text,
            "start_word": i,
            "end_word": min(i + chunk_size, len(words))
        })
    
    return chunks
```

**Key Design Decisions:**
1. **Word-based chunking** (not character-based) - preserves word boundaries
2. **Overlapping chunks** - ensures context isn't lost at boundaries
3. **Metadata tracking** - enables citation and source tracking

#### **Data Storage Structure**

**Storage Format:**
```json
{
  "MG Astor": {
    "car_model": "MG Astor",
    "chunks": [
      {
        "text": "chunk text here...",
        "start_word": 0,
        "end_word": 500
      }
    ],
    "total_chunks": 150
  }
}
```

**Storage Strategy:**
- **Primary storage:** JSON file (`processed_manuals.json`)
- **Full text removed** from saved data to reduce file size
- **Only chunks stored** - can reconstruct full text if needed
- **Caching:** Processed data is cached to avoid reprocessing

**Code Location:** `pdf_processor.py`, lines 65-78
```python
def save_processed_data(self, output_path: str = "processed_manuals.json"):
    """Save processed manual data to JSON file."""
    # Remove full_text to save space, keep only chunks
    save_data = {}
    for model, data in self.manuals_data.items():
        save_data[model] = {
            "car_model": data["car_model"],
            "chunks": data["chunks"],
            "total_chunks": data["total_chunks"]
        }
```

#### **Future: Tabular Data Extraction**

**Current Status:** Textual extraction only (as per requirement to focus on text first)

**Planned Approach for Tables:**
1. Use `pdfplumber`'s table extraction: `page.extract_tables()`
2. Convert tables to structured format (CSV/JSON)
3. Store table metadata separately
4. Index table content for search
5. Format table data in answers when relevant

**Example Implementation (Future):**
```python
def extract_tables_from_pdf(self, pdf_path: str) -> List[Dict]:
    """Extract tables from PDF."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_tables = page.extract_tables()
            for table in page_tables:
                tables.append({
                    "page": page_num,
                    "table_data": table,
                    "headers": table[0] if table else []
                })
    return tables
```

---

## 2. Output Structure: Response Format, Citations, and Query Handling

### **Response Structure**

**Standard Response Format:**
```python
{
    "answer": "The answer text here...",
    "citations": [
        {
            "citation_number": 1,
            "car_model": "MG Astor",
            "excerpt": "Source text excerpt..."
        }
    ],
    "confidence": "high" | "medium" | "low"
}
```

**Code Location:** `rag_qa_system.py`, lines 81-85 and `qa_system.py`, lines 39-43

### **Citation System**

**Citation Features:**
1. **Numbered citations** - Easy to reference
2. **Car model identification** - Shows which manual the source is from
3. **Excerpt display** - Shows relevant portion (truncated to 300 chars)
4. **Expandable UI** - Streamlit expanders for better UX

**Implementation:**
```python
citations = []
for i, result in enumerate(search_results[:5], 1):
    citations.append({
        "citation_number": i,
        "car_model": result["car_model"],
        "excerpt": result["text"][:300] + "..." if len(result["text"]) > 300 else result["text"]
    })
```

**Code Location:** `rag_qa_system.py`, lines 65-71

### **Output Consistency**

#### **Consistent Answer Format**

**RAG System (with LLM):**
- Uses structured prompts to ensure consistent formatting
- Instructions for bullet points, step-by-step format
- Clear model references

**Code Location:** `rag_qa_system.py`, lines 119-136
```python
prompt = f"""You are an expert car manual assistant. Answer the user's question based ONLY on the provided manual excerpts from the {car_model} owner's manual.

INSTRUCTIONS:
1. Answer directly and concisely based ONLY on the provided manual excerpts
2. If the information is not in the excerpts, clearly state: "I couldn't find specific information about this in the {car_model} manual"
3. Include specific steps, numbers, or measurements when mentioned in the manual
4. Use bullet points for step-by-step instructions
5. Reference the car model ({car_model}) when relevant
6. Be helpful and clear, as if explaining to a car owner
```

**Simple Q&A System (fallback):**
- Extracts relevant sentences based on keyword matching
- Formats answers with proper spacing
- Ensures minimum answer length

**Code Location:** `qa_system.py`, lines 45-93

#### **Handling Incomplete Queries**

**Strategies Implemented:**

1. **Missing Car Model Detection:**
   - Automatically detects car model from question keywords
   - Falls back to searching all manuals if model not detected
   - Warns user when model is ambiguous

**Code Location:** `app.py`, lines 131-137
```python
detected_model = detect_car_model(question)

if detected_model:
    st.info(f"📌 Detected car model: **{detected_model}**")
else:
    st.warning("⚠️ Could not detect car model. Searching all manuals...")
```

2. **Empty/No Results Handling:**
   - Returns clear message when no information found
   - Provides confidence levels (high/medium/low)
   - Suggests rephrasing when appropriate

**Code Location:** `rag_qa_system.py`, lines 54-59
```python
if not search_results:
    return {
        "answer": "I couldn't find relevant information in the manual to answer your question.",
        "citations": [],
        "confidence": "low"
    }
```

3. **Fallback Search Strategy:**
   - Primary: Semantic search (semantic similarity)
   - Fallback: Keyword search (if semantic search fails)
   - Ensures some results are always attempted

**Code Location:** `app.py`, lines 150-157
```python
if not search_results and detected_model:
    # Fallback to keyword search
    st.info("Trying keyword search...")
    search_results = st.session_state.search_engine.simple_keyword_search(
        question,
        car_model=detected_model,
        top_k=5
    )
```

4. **Confidence Scoring:**
   - Based on search result quality (distance scores)
   - Multiple results = higher confidence
   - Visual indicators in UI (✅/ℹ️/⚠️)

**Code Location:** `rag_qa_system.py`, lines 87-107
```python
def _calculate_confidence(self, search_results: List[Dict]) -> str:
    """Calculate confidence level based on search result quality."""
    if not search_results:
        return "low"
    
    # Check distance scores (lower is better for semantic search)
    if "distance" in search_results[0]:
        top_distance = search_results[0]["distance"]
        if top_distance < 0.5:
            return "high"
        elif top_distance < 1.0:
            return "medium"
        else:
            return "low"
```

---

## 3. Scalability: Storage, Processing, and Search Optimizations

### **Storage Considerations**

#### **Efficient Data Storage**

1. **Chunked Storage:**
   - Only stores chunks, not full text (saves ~70% space)
   - Full text can be reconstructed from chunks if needed
   - Reduces memory footprint

2. **Caching Strategy:**
   - Processed data saved to `processed_manuals.json`
   - Avoids reprocessing PDFs on every run
   - Fast startup after first run

**Code Location:** `app.py`, lines 39-42
```python
if os.path.exists("processed_manuals.json"):
    print("Loading pre-processed manuals...")
    manuals_data = processor.load_processed_data()
```

3. **Embedding Storage:**
   - Embeddings generated once and stored in FAISS index
   - FAISS uses efficient vector storage (compressed)
   - In-memory index for fast retrieval

**Code Location:** `search_engine.py`, lines 50-55
```python
# Build FAISS index
dimension = embeddings.shape[1]
self.index = faiss.IndexFlatL2(dimension)
self.index.add(embeddings.astype('float32'))
```

#### **Scalability for Large Datasets**

**Current Approach:**
- Single FAISS index for all manuals
- Metadata array tracks which chunk belongs to which manual
- Filtering by car model happens post-search

**Future Optimizations:**
1. **Sharded Indexes:** Separate index per car model
2. **Persistent Storage:** Save FAISS index to disk
3. **Incremental Updates:** Add new manuals without rebuilding entire index
4. **Compression:** Use quantized FAISS indexes for large datasets

### **Input Processing Strategy**

#### **Efficient Processing Pipeline**

1. **Lazy Loading:**
   - Manuals only processed when needed
   - Cached results reused across sessions
   - Streamlit caching prevents redundant processing

**Code Location:** `app.py`, lines 34-61
```python
@st.cache_resource
def load_manuals():
    """Load and process car manuals."""
    # Uses Streamlit caching to avoid reprocessing
```

2. **Batch Processing:**
   - All chunks processed in single batch
   - Embeddings generated in parallel
   - Progress bar for user feedback

**Code Location:** `search_engine.py`, lines 47-48
```python
embeddings = self.model.encode(all_chunks, show_progress_bar=True)
```

3. **Model Detection:**
   - Fast keyword-based detection
   - No LLM needed for model detection
   - Reduces search space early

**Code Location:** `pdf_processor.py`, lines 94-108
```python
def detect_car_model(question: str) -> str:
    """Detect which car model the question is about."""
    question_lower = question.lower()
    
    astor_keywords = ["astor", "mg astor", "mg"]
    if any(keyword in question_lower for keyword in astor_keywords):
        return "MG Astor"
    
    tiago_keywords = ["tiago", "tata tiago", "tata"]
    if any(keyword in question_lower for keyword in tiago_keywords):
        return "Tata Tiago"
    
    return None
```

### **Search Optimizations**

#### **Semantic Search with FAISS**

**Why FAISS?**
- **Fast:** Optimized C++ backend
- **Scalable:** Handles millions of vectors efficiently
- **Memory efficient:** Compressed vector storage
- **L2 Distance:** Fast similarity computation

**Implementation:**
```python
# Generate query embedding once
query_embedding = self.model.encode([query])

# Fast vector search
k = min(top_k * 2, self.index.ntotal)
distances, indices = self.index.search(query_embedding.astype('float32'), k)
```

**Code Location:** `search_engine.py`, lines 62-67

#### **Multi-Level Search Strategy**

1. **Primary: Semantic Search**
   - Uses sentence transformers (all-MiniLM-L6-v2)
   - Understands meaning, not just keywords
   - Fast with FAISS index

2. **Fallback: Keyword Search**
   - Simple word matching when semantic fails
   - Ensures results are always attempted
   - Fast string operations

**Code Location:** `search_engine.py`, lines 91-114

#### **Search Result Filtering**

**Post-Search Filtering:**
- Retrieves 2x results, then filters by car model
- Ensures top_k results from correct model
- Efficient filtering on small result set

**Code Location:** `search_engine.py`, lines 66-88
```python
k = min(top_k * 2, self.index.ntotal)  # Get more results to filter
distances, indices = self.index.search(query_embedding.astype('float32'), k)

results = []
for dist, idx in zip(distances[0], indices[0]):
    metadata = self.chunk_metadata[idx]
    
    # Filter by car model if specified
    if car_model and metadata["car_model"] != car_model:
        continue
    
    # Add to results...
```

#### **Performance Optimizations**

1. **Model Choice:**
   - `all-MiniLM-L6-v2` - Fast, lightweight, good quality
   - 384-dimensional embeddings (smaller = faster)
   - Pre-trained on large corpus

2. **Batch Encoding:**
   - All chunks encoded in single batch
   - GPU acceleration if available
   - Progress feedback for user

3. **Index Type:**
   - `IndexFlatL2` - Exact search (best quality)
   - Can upgrade to `IndexIVFFlat` for larger datasets (approximate, faster)

**Future Optimizations:**
- **Approximate Search:** Use IVF or HNSW indexes for very large datasets
- **GPU Acceleration:** Use FAISS GPU indexes
- **Query Caching:** Cache common queries
- **Parallel Processing:** Multi-threaded search for multiple queries

---

## Summary of Design Decisions

### **Input Processing**
✅ **Textual extraction** using pdfplumber  
✅ **Chunking strategy** with overlap for context preservation  
✅ **Structured storage** in JSON with metadata  
⏳ **Tabular extraction** planned for future (text-first approach)

### **Output Structure**
✅ **Consistent response format** with answer, citations, confidence  
✅ **Numbered citations** with excerpts and car model  
✅ **Confidence scoring** based on search quality  
✅ **Incomplete query handling** with model detection and fallbacks

### **Scalability**
✅ **Efficient storage** with chunked data and caching  
✅ **FAISS indexing** for fast semantic search  
✅ **Batch processing** for embeddings  
✅ **Multi-level search** with semantic + keyword fallback  
⏳ **Future:** Sharded indexes, persistent storage, incremental updates

---

## Code Flow Diagram

```
User Question
    ↓
[Model Detection] → detect_car_model()
    ↓
[Semantic Search] → search_engine.search()
    ├─→ Generate query embedding
    ├─→ FAISS vector search
    └─→ Filter by car model
    ↓
[Fallback if needed] → simple_keyword_search()
    ↓
[Answer Generation] → qa_system.generate_answer()
    ├─→ RAG with LLM (if available)
    └─→ Simple extraction (fallback)
    ↓
[Format Response] → {answer, citations, confidence}
    ↓
Display to User
```

---

This architecture ensures the system is:
- **Fast:** Caching, efficient indexing, batch processing
- **Accurate:** Semantic search, confidence scoring, citations
- **Robust:** Fallbacks, error handling, incomplete query support
- **Scalable:** Efficient storage, optimized search, extensible design

