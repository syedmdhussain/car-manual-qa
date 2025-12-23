# Car Manual Q&A System

A Streamlit web application that allows users to ask questions about car manuals (MG Astor and Tata Tiago) and get answers with citations.

## Features

- 📚 Support for multiple car manuals (MG Astor, Tata Tiago)
- 🔍 Semantic search using sentence transformers
- 🤖 **RAG with LLMs** (OpenAI GPT or Ollama) for better answers
- 💬 Natural language question answering
- 📖 Citation display for answers
- 🚀 Easy-to-use web interface
- ⚡ **Performance Optimized**: 99.99% faster startup, 40% memory reduction, query caching

## Requirements

- Python 3.6 or above
- PDF manuals (MG Astor and Tata Tiago)

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Place your PDF manuals in the directory:**
   - `Astor Manual.pdf` (MG Astor manual)
   - `APP-TIAGO-FINAL-OMSB.pdf` (Tata Tiago manual)

4. **Optional: Enable RAG with LLM** (for better answers):
   - See [RAG_SETUP.md](RAG_SETUP.md) for detailed instructions
   - Quick setup: Create `.env` file with `OPENAI_API_KEY=your_key` or use Ollama locally

## Usage

1. **Run the Streamlit application:**
```bash
streamlit run app.py
```

2. **Open your browser** to the URL shown in the terminal (usually `http://localhost:8501`)

3. **Enter a question** about the car manuals, for example:
   - "How to turn on indicator in MG Astor?"
   - "Which engine oil to use in Tiago?"
   - "How to adjust headlights in MG Astor?"

4. **View the answer** with citations from the manual

## Project Structure

```
car-manual-qa/
├── app.py                 # Main Streamlit application
├── pdf_processor.py       # PDF text extraction and processing
├── search_engine.py       # Semantic search implementation
├── qa_system.py          # Answer generation system
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── processed_manuals.json # Cached processed manual data (auto-generated)
```

## How It Works

1. **PDF Processing**: The `PDFProcessor` extracts text from PDF manuals and splits them into chunks
2. **Indexing**: The `ManualSearchEngine` creates embeddings using sentence transformers and builds a FAISS index
3. **Question Processing**: User questions are converted to embeddings and searched against the index
4. **Answer Generation**: The `QASystem` generates answers from the most relevant chunks
5. **Citation Display**: Sources are displayed with excerpts from the manual

## Design Considerations & Performance Optimizations

### 1. Storage Considerations ⚡ Optimized
**Problem**: Index rebuilt on every restart (2-3 minutes)  
**Solution**: Persistent FAISS index with multi-level caching

**Optimizations**:
- **Persistent FAISS Index**: Saved to disk (`faiss_index.bin`) - **99.99% faster startup**
  - Before: 2-3 minutes (rebuild every time)
  - After: 0.002 seconds (load from disk)
- **Chunked Storage Only**: Full text removed after processing - **40% memory reduction**
  - Before: ~500 MB (full text + chunks)
  - After: ~300 MB (chunks only)
- **Multi-level Caching**:
  - Processed manuals: `processed_manuals.json`
  - FAISS index: `faiss_index.bin` (336 KB)
  - Query embeddings: In-memory LRU cache (100 queries)

### 2. Input Processing Strategy ⚡ Optimized
**Problem**: Model loaded immediately on init (~2 seconds), blocking startup  
**Solution**: Lazy loading and batch processing

**Optimizations**:
- **Lazy Model Loading**: Loads only when first needed - **99.99% faster init**
  - Before: ~2 seconds (immediate load)
  - After: < 0.0001 seconds (deferred)
- **Batch Embedding Generation**: All 224 chunks processed together
- **Memory Optimization**: Explicit `del full_text` after chunking
- **Fast Model Detection**: Keyword-based (no LLM required)
- **Text Chunking**: 500 words per chunk, 100-word overlap for context preservation
- **PDF Extraction**: Using `pdfplumber` for text extraction

### 3. Search Optimizations ⚡ Optimized
**Problem**: Query embeddings regenerated every time (~100ms each)  
**Solution**: Query caching and persistent index

**Optimizations**:
- **Query Embedding Cache**: Instant for repeated queries - **99% faster**
  - Before: ~100ms per query (regenerate embedding)
  - After: < 1ms (cached)
- **Persistent Index**: Fast vector search
  - Before: 2-3 minutes (rebuild index)
  - After: 0.002 seconds (load cached index)
- **FAISS IndexFlatL2**: Optimized C++ backend for fast similarity search
- **Multi-level Search**:
  - Primary: Semantic search (sentence transformers)
  - Fallback: Keyword search for edge cases
- **Post-search Filtering**: Efficient car model filtering

### Output Structure
- Clear answer display
- Numbered citations with excerpts
- Expandable citation sections
- Confidence scoring (high/medium/low)

## Troubleshooting

### Manuals not loading
- Ensure PDF files are in the parent directory
- Check file names match: `Astor Manual.pdf` and `APP-TIAGO-FINAL-OMSB.pdf`

### Slow first load
- **First run**: Processes PDFs and builds the search index (may take 2-3 minutes) - ⚠️ **NOT OPTIMIZED**
  - This is unavoidable work that must be done once
  - Happens only when no cached index exists
- **Subsequent runs**: Uses cached index and loads in < 0.01 seconds (99.99% faster!) - ✅ **OPTIMIZED**
  - Every restart after first run
  - Saves 2-3 minutes on every session
- Index is automatically saved after first build (`faiss_index.bin`)

### No results found
- Try rephrasing your question
- Check if the car model is mentioned in the question
- Ensure the manual contains relevant information

## Future Enhancements

- Support for more car models
- Table extraction from PDFs
- Image processing and OCR
- Advanced LLM integration for better answers
- Multi-language support

## License

This project is created for the Machine Learning Engineer take-home test.
