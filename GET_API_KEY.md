# How to Get API Keys

## Option 1: OpenAI API Key (Recommended)

### Step-by-Step:

1. **Go to OpenAI Platform:**
   - Visit: https://platform.openai.com
   - Click "Sign Up" or "Log In"

2. **Create Account:**
   - Sign up with email or Google/Microsoft account
   - Verify your email

3. **Get API Key:**
   - Go to: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Give it a name (e.g., "Car Manual Q&A")
   - **Copy the key immediately** (you can't see it again!)

4. **Add Credits (if needed):**
   - Go to: https://platform.openai.com/account/billing
   - Add payment method (they have free tier too)
   - For this project, $5-10 is more than enough

5. **Free Tier:**
   - New accounts get $5 free credit
   - That's ~5000 questions with GPT-3.5-turbo!

### Cost:
- **GPT-3.5-turbo**: ~$0.001 per question
- **Free tier**: $5 credit = ~5000 questions
- **For this test**: Practically free!

## Option 2: Use Without API Key (Ollama)

If you don't want to use OpenAI:

1. **Install Ollama:**
   ```bash
   # macOS
   brew install ollama
   # or download from https://ollama.ai
   ```

2. **Download a model:**
   ```bash
   ollama pull llama2
   ```

3. **Start Ollama:**
   ```bash
   ollama serve
   ```

4. **Set environment variable:**
   ```bash
   export USE_OLLAMA=true
   ```

## Option 3: No API Key (Simple Mode)

The app works without any API key!
- Uses simple text extraction
- Still functional, just less polished answers
