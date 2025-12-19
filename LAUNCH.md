# 🚀 Quick Launch Guide

## Step 1: Get API Key (Optional but Recommended)

### Get OpenAI API Key:

1. **Visit:** https://platform.openai.com/api-keys
2. **Sign up/Login** (free $5 credit for new users!)
3. **Click "Create new secret key"**
4. **Copy the key** (starts with `sk-...`)

### Add to .env file:

```bash
# Create .env file
cd /Users/syed/Downloads/car-manual-qa
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

**OR** edit `.env` file and add:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

## Step 2: Launch the Service

### Option A: Direct Launch (Recommended)

```bash
cd /Users/syed/Downloads/car-manual-qa
streamlit run app.py
```

### Option B: With Python Path

If streamlit command not found:

```bash
cd /Users/syed/Downloads/car-manual-qa
python3 -m streamlit run app.py
```

### Option C: Using Full Path

```bash
/Users/syed/Library/Python/3.9/bin/streamlit run /Users/syed/Downloads/car-manual-qa/app.py
```

## Step 3: Open in Browser

The terminal will show:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

**Click the URL or copy-paste it into your browser!**

## First Run Notes

⚠️ **First time will take 2-3 minutes:**
- Processing PDFs
- Building search index
- Loading ML models

✅ **Subsequent runs are much faster** (uses cached data)

## Troubleshooting

### "streamlit: command not found"
```bash
# Use python3 -m instead
python3 -m streamlit run app.py
```

### "Module not found"
```bash
# Reinstall dependencies
pip3 install -r requirements.txt
```

### Port already in use
```bash
# Use different port
streamlit run app.py --server.port 8502
```

### PDFs not found
```bash
# Check PDFs are in directory
ls -lh *.pdf
# Should show:
# - Astor Manual.pdf
# - APP-TIAGO-FINAL-OMSB.pdf
```

## Without API Key

The app works without API key!
- Uses simple text extraction
- Still functional
- Just less polished answers

## Test It!

Try these questions:
- "How to turn on indicator in MG Astor?"
- "Which engine oil to use in Tiago?"
- "How to adjust headlights in MG Astor?"
