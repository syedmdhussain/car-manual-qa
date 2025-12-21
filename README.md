# Car Manual Q&A System

A Streamlit web application that allows users to ask questions about car manuals (MG Astor and Tata Tiago) and get answers with citations.

## Features

- 📚 Support for multiple car manuals (MG Astor, Tata Tiago)
- 🔍 Semantic search using sentence transformers
- 🤖 **RAG with LLMs** (OpenAI GPT or Ollama) for better answers
- 💬 Natural language question answering
- 📖 Citation display for answers
- 🚀 Easy-to-use web interface

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

## Design Considerations

### Input Processing
- Text extraction from PDFs using `pdfplumber`
- Text chunking with overlap for better context
- Model detection from question keywords

### Output Structure
- Clear answer display
- Numbered citations with excerpts
- Expandable citation sections

### Scalability
- FAISS index for fast similarity search
- Cached processed data (JSON) to avoid reprocessing
- Chunked text storage for efficient retrieval

## Troubleshooting

### Manuals not loading
- Ensure PDF files are in the parent directory
- Check file names match: `Astor Manual.pdf` and `APP-TIAGO-FINAL-OMSB.pdf`

### Slow first load
- First run processes PDFs and builds the search index (may take 2-3 minutes)
- Subsequent runs use cached data and are faster

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
