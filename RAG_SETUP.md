# RAG Setup Guide

This guide explains how to enable RAG (Retrieval-Augmented Generation) with LLMs for better answers.

## What is RAG?

RAG combines:
1. **Retrieval**: Finding relevant chunks from the car manuals
2. **Augmented Generation**: Using an LLM to synthesize a coherent answer from those chunks

This provides much better answers than simple text extraction!

## Option 1: Using OpenAI (Recommended)

### Setup Steps:

1. **Get an OpenAI API Key:**
   - Go to https://platform.openai.com/api-keys
   - Sign up/login
   - Create a new API key
   - Copy the key

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

3. **Add your API key to `.env`:**
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

The app will automatically detect the API key and use GPT-3.5-turbo for RAG.

### Cost:
- GPT-3.5-turbo: ~$0.001-0.002 per question (very cheap)
- GPT-4: Better quality but more expensive (~$0.01-0.03 per question)

To use GPT-4, edit `rag_qa_system.py` and change `model="gpt-3.5-turbo"` to `model="gpt-4"`

## Option 2: Using Ollama (Free, Local)

Ollama allows you to run LLMs locally on your machine - completely free!

### Setup Steps:

1. **Install Ollama:**
   - Visit https://ollama.ai
   - Download and install Ollama
   - Or use: `curl -fsSL https://ollama.ai/install.sh | sh`

2. **Download a model:**
   ```bash
   ollama pull llama2
   # or
   ollama pull mistral
   # or
   ollama pull codellama
   ```

3. **Start Ollama server:**
   ```bash
   ollama serve
   ```

4. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

5. **Configure `.env`:**
   ```
   USE_OLLAMA=true
   OLLAMA_BASE_URL=http://localhost:11434
   ```

6. **Update model name (optional):**
   Edit `rag_qa_system.py` line ~120 and change `"model": "llama2"` to your preferred model.

7. **Run the app:**
   ```bash
   streamlit run app.py
   ```

### Recommended Ollama Models:
- `llama2` - Good balance of quality and speed
- `mistral` - Fast and efficient
- `codellama` - Good for technical content
- `llama2:13b` - Better quality (requires more RAM)

## Option 3: No LLM (Current Default)

If you don't set up any API keys, the system will use simple text extraction. This works but provides less coherent answers.

## Comparing the Options

| Feature | Simple Extraction | OpenAI RAG | Ollama RAG |
|---------|------------------|------------|------------|
| **Cost** | Free | ~$0.001/question | Free |
| **Quality** | Basic | Excellent | Good |
| **Speed** | Fast | Fast | Slower |
| **Internet** | Not needed | Required | Not needed |
| **Setup** | None | API key | Install Ollama |

## Testing RAG

After setup, you should see in the sidebar:
- ✅ Using OPENAI for RAG (if using OpenAI)
- ✅ Using OLLAMA for RAG (if using Ollama)
- ℹ️ Using simple extraction (if no LLM)

## Troubleshooting

### OpenAI Issues:
- **Error: Invalid API key**: Check your `.env` file
- **Error: Rate limit**: You've exceeded free tier limits
- **Error: No module 'openai'**: Run `pip install openai`

### Ollama Issues:
- **Connection refused**: Make sure `ollama serve` is running
- **Model not found**: Run `ollama pull <model-name>`
- **Slow responses**: Try a smaller model or better hardware

## Advanced Configuration

### Custom Prompt:
Edit `rag_qa_system.py` to customize the prompt template.

### Temperature Control:
Lower temperature (0.1-0.3) = more focused answers
Higher temperature (0.7-1.0) = more creative answers

### Context Size:
Adjust `search_results[:5]` to include more/fewer chunks in context.

## Benefits of RAG

✅ **Better answers**: LLM synthesizes information coherently  
✅ **Contextual understanding**: Understands question intent  
✅ **Proper formatting**: Well-structured, readable responses  
✅ **Handles ambiguity**: Can infer meaning from context  
✅ **Citations**: Still provides source references  

## Example Comparison

**Question**: "How do I turn on the indicator in MG Astor?"

**Simple Extraction:**
> "The indicator switch is located on the steering column. Turn the switch..."

**RAG Answer:**
> "To turn on the indicator in your MG Astor, locate the indicator switch on the steering column. Turn the switch in the direction you want to indicate. The indicator will automatically turn off after you complete the turn. Make sure to use indicators before changing lanes or turning."

The RAG answer is more complete and user-friendly!
