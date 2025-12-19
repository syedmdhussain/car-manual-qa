# Quick Start Guide

## Prerequisites
- Python 3.6 or above
- pip (Python package installer)

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

## Step 2: Verify PDF Files

Make sure the following PDF files are in the `car-manual-qa` directory:
- `Astor Manual.pdf` (MG Astor manual)
- `APP-TIAGO-FINAL-OMSB.pdf` (Tata Tiago manual)

If they're in a different location, the app will also check the parent directory.

## Step 3: Run the Application

```bash
streamlit run app.py
```

The application will:
1. First time: Process PDFs and build search index (takes 2-3 minutes)
2. Subsequent runs: Load cached data (much faster)

## Step 4: Use the Application

1. Open your browser to the URL shown (usually `http://localhost:8501`)
2. Enter a question like:
   - "How to turn on indicator in MG Astor?"
   - "Which engine oil to use in Tiago?"
3. Click "Search" or press Enter
4. View the answer with citations

## Troubleshooting

### Error: Module not found
- Run: `pip install -r requirements.txt`

### Error: PDFs not found
- Check that PDF files are in the correct location
- Verify file names match exactly

### Slow first load
- This is normal! The first run processes PDFs and builds the search index
- Subsequent runs are much faster

### No results found
- Try rephrasing your question
- Include the car model name (MG Astor or Tata Tiago)
- Check if the manual contains relevant information

## Notes

- The processed manual data is cached in `processed_manuals.json`
- Delete this file to reprocess PDFs
- The search index is built in memory each time (consider saving it for production)
