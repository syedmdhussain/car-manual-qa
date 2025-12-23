# How RAG (Retrieval-Augmented Generation) is Used

This document explains how RAG is implemented and used in the Car Manual Q&A system.

---

## What is RAG?

**RAG = Retrieval-Augmented Generation**

RAG is a technique that combines:
1. **Retrieval**: Finding relevant information from a knowledge base (car manuals)
2. **Augmentation**: Adding that information to the LLM's context
3. **Generation**: Using an LLM to generate a natural, accurate answer based on the retrieved context

**Why RAG?**
- LLMs can "hallucinate" (make up information)
- LLMs have limited knowledge cutoff dates
- RAG ensures answers are grounded in actual manual content
- Provides citations for transparency

---

## RAG Flow in This System

```
User Question
    ↓
┌─────────────────────────────────────┐
│   STEP 1: RETRIEVAL                │
│   (search_engine.py)                │
└─────────────────────────────────────┘
    ↓
1. Convert question to embedding
2. Search FAISS index for similar chunks
3. Retrieve top 5 most relevant chunks
    ↓
┌─────────────────────────────────────┐
│   STEP 2: AUGMENTATION             │
│   (rag_qa_system.py)                │
└─────────────────────────────────────┘
    ↓
1. Format retrieved chunks as context
2. Create prompt with context + question
    ↓
┌─────────────────────────────────────┐
│   STEP 3: GENERATION               │
│   (rag_qa_system.py)                │
└─────────────────────────────────────┘
    ↓
1. Send prompt to LLM (OpenAI/Ollama)
2. LLM generates answer from context
3. Return answer with citations
```

---

## Step-by-Step Implementation

### **Step 1: Retrieval (Finding Relevant Information)**

**File:** `search_engine.py`  
**Method:** `search()`

**What happens:**
1. User question is converted to an embedding vector
2. FAISS index searches for similar chunks (semantic similarity)
3. Top 5 most relevant chunks are returned

**Code:**
```python
# Generate query embedding
query_embedding = self.model.encode([query])

# Search in FAISS index
distances, indices = self.index.search(query_embedding.astype('float32'), k)

# Return top results
results = [
    {
        "text": chunk_text,
        "car_model": "MG Astor",
        "distance": 0.45,  # Lower = more similar
        "chunk_index": 42
    },
    # ... more results
]
```

**Example:**
- Question: "How to turn on indicator in MG Astor?"
- Retrieval finds chunks about:
  - Indicator controls
  - Turn signal operation
  - Dashboard controls

---

### **Step 2: Augmentation (Preparing Context for LLM)**

**File:** `rag_qa_system.py`  
**Method:** `_generate_with_openai()` or `_generate_with_ollama()`

**What happens:**
1. Retrieved chunks are formatted as context
2. Context is combined with the question in a structured prompt
3. Prompt instructs LLM to answer ONLY from the provided context

**Code:**
```python
# Prepare context from top results
context_chunks = []
for i, result in enumerate(search_results[:5], 1):
    context_chunks.append(
        f"[Source {i} from {result['car_model']} Manual]:\n{result['text']}\n"
    )

context = "\n".join(context_chunks)

# Create prompt
prompt = f"""You are an expert car manual assistant. Answer the user's question 
based ONLY on the provided manual excerpts from the {car_model} owner's manual.

MANUAL EXCERPTS:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer directly and concisely based ONLY on the provided manual excerpts
2. If the information is not in the excerpts, clearly state: "I couldn't find..."
3. Include specific steps, numbers, or measurements when mentioned
4. Use bullet points for step-by-step instructions
5. Reference the car model when relevant

ANSWER:"""
```

**Example Context Format:**
```
[Source 1 from MG Astor Manual]:
To activate the turn indicator, locate the indicator stalk on the left side 
of the steering column. Push the stalk up to indicate right turn, or down 
to indicate left turn. The indicator will automatically cancel after the turn.

[Source 2 from MG Astor Manual]:
The indicator controls are located on the steering column. The stalk can be 
moved in two directions: upward for right turn signals and downward for left 
turn signals.

USER QUESTION: How to turn on indicator in MG Astor?
```

---

### **Step 3: Generation (LLM Creates Answer)**

**File:** `rag_qa_system.py`  
**Methods:** `_generate_with_openai()` or `_generate_with_ollama()`

**What happens:**
1. Prompt (with context + question) is sent to LLM
2. LLM generates a natural, coherent answer
3. Answer is extracted and returned

**OpenAI Implementation:**
```python
response = self.client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant..."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,  # Low temperature for consistent, factual answers
    max_tokens=500
)

answer = response.choices[0].message.content.strip()
```

**Ollama Implementation (Local LLM):**
```python
response = requests.post(
    f"{self.ollama_base_url}/api/generate",
    json={
        "model": "llama2",
        "prompt": prompt,
        "stream": False
    }
)

answer = response.json().get("response", "").strip()
```

**Example Generated Answer:**
```
To turn on the indicator in your MG Astor:

1. Locate the indicator stalk on the left side of the steering column
2. Push the stalk upward to activate the right turn indicator
3. Push the stalk downward to activate the left turn indicator

The indicator will automatically cancel after you complete the turn.
```

---

## Complete RAG Flow in Code

**File:** `app.py` (lines 140-163)

```python
# 1. RETRIEVAL: Search for relevant chunks
search_results = st.session_state.search_engine.search(
    question,
    car_model=detected_model,
    top_k=5
)

# 2. GENERATION: Use RAG to generate answer
answer_data = st.session_state.qa_system.generate_answer(
    question,
    search_results
)
```

**Inside `generate_answer()` (rag_qa_system.py, lines 52-85):**

```python
def generate_answer(self, question: str, search_results: List[Dict]) -> Dict:
    # Prepare citations
    citations = []
    for i, result in enumerate(search_results[:5], 1):
        citations.append({
            "citation_number": i,
            "car_model": result["car_model"],
            "excerpt": result["text"][:300]
        })
    
    # AUGMENTATION + GENERATION: Use LLM if available
    if self.use_llm and self.llm_provider == "openai":
        answer = self._generate_with_openai(question, search_results)
    elif self.use_llm and self.llm_provider == "ollama":
        answer = self._generate_with_ollama(question, search_results)
    else:
        # Fallback: simple extraction (no LLM)
        answer = self._simple_extraction(question, search_results)
    
    return {
        "answer": answer,
        "citations": citations,
        "confidence": confidence
    }
```

---

## RAG vs Simple Q&A

### **With RAG (LLM-enabled):**
```
Question → Retrieval → LLM Generation → Natural Answer
```

**Advantages:**
- ✅ Natural, conversational answers
- ✅ Synthesizes information from multiple chunks
- ✅ Better formatting (bullet points, steps)
- ✅ Handles complex questions
- ✅ More context-aware

**Example Answer (RAG):**
```
To adjust the headlights in your MG Astor:

1. Park your vehicle on a level surface about 25 feet from a wall
2. Turn on the headlights
3. Locate the headlight adjustment screws near each headlight assembly
4. Use a Phillips screwdriver to turn the screws:
   - Turn clockwise to raise the beam
   - Turn counterclockwise to lower the beam
5. Adjust until the beam pattern is centered on the wall

Note: Refer to your owner's manual for specific adjustment specifications.
```

### **Without RAG (Simple Extraction):**
```
Question → Retrieval → Text Extraction → Raw Chunk
```

**Limitations:**
- ❌ Returns raw text chunks
- ❌ No synthesis of multiple sources
- ❌ Less natural language
- ❌ May include irrelevant information

**Example Answer (Simple):**
```
"To adjust the headlights, park the vehicle on a level surface. Locate the 
adjustment screws. Turn clockwise to raise, counterclockwise to lower. 
Refer to manual for specifications. The headlight assembly is located near 
the front grille. Maintenance should be performed regularly..."
```

---

## LLM Provider Options

### **1. OpenAI (Cloud-based)**
**Setup:** Set `OPENAI_API_KEY` in `.env` file

**Code:** `rag_qa_system.py`, lines 109-153

**Pros:**
- ✅ High quality answers
- ✅ Fast response
- ✅ Reliable

**Cons:**
- ❌ Requires API key
- ❌ Costs per request
- ❌ Requires internet

### **2. Ollama (Local)**
**Setup:** Install Ollama locally, set `USE_OLLAMA=true`

**Code:** `rag_qa_system.py`, lines 155-194

**Pros:**
- ✅ Free (runs locally)
- ✅ No API costs
- ✅ Privacy (data stays local)

**Cons:**
- ❌ Requires local installation
- ❌ Slower than cloud
- ❌ May need GPU for good performance

### **3. Fallback (No LLM)**
**When:** No API key and Ollama not available

**Code:** `rag_qa_system.py`, lines 196-211

**Behavior:**
- Uses simple text extraction
- Returns raw chunks
- Still provides citations

---

## Key RAG Features in This System

### **1. Context-Aware Prompting**
The prompt explicitly tells the LLM to:
- Answer ONLY from provided context
- State clearly if information is missing
- Include specific details (numbers, steps)
- Format answers clearly

**Code:** `rag_qa_system.py`, lines 121-136

### **2. Multiple Source Synthesis**
RAG combines information from multiple chunks:
- Top 5 chunks are included in context
- LLM synthesizes information across chunks
- Provides comprehensive answers

**Code:** `rag_qa_system.py`, lines 113-117

### **3. Citation Tracking**
Every answer includes:
- Numbered citations
- Source car model
- Excerpt from manual

**Code:** `rag_qa_system.py`, lines 65-71

### **4. Confidence Scoring**
System calculates confidence based on:
- Search result quality (distance scores)
- Number of relevant results
- Quality of matches

**Code:** `rag_qa_system.py`, lines 87-107

### **5. Graceful Degradation**
If LLM fails:
- Falls back to simple extraction
- Still provides citations
- System remains functional

**Code:** `rag_qa_system.py`, lines 151-153, 192-194

---

## Example: Complete RAG Flow

**User Question:**
> "What is the recommended tire pressure for Tata Tiago?"

**Step 1: Retrieval**
```python
search_results = [
    {
        "text": "The recommended tire pressure for Tata Tiago is 30 PSI for 
                 front tires and 28 PSI for rear tires when the vehicle is 
                 cold. Check tire pressure monthly...",
        "car_model": "Tata Tiago",
        "distance": 0.32
    },
    {
        "text": "Tire pressure should be checked when tires are cold. 
                 Recommended values are printed on the driver's door jamb...",
        "car_model": "Tata Tiago",
        "distance": 0.45
    }
]
```

**Step 2: Augmentation (Prompt Created)**
```
You are an expert car manual assistant...

MANUAL EXCERPTS:
[Source 1 from Tata Tiago Manual]:
The recommended tire pressure for Tata Tiago is 30 PSI for front tires and 
28 PSI for rear tires when the vehicle is cold...

[Source 2 from Tata Tiago Manual]:
Tire pressure should be checked when tires are cold. Recommended values are 
printed on the driver's door jamb...

USER QUESTION: What is the recommended tire pressure for Tata Tiago?

ANSWER:
```

**Step 3: Generation (LLM Response)**
```
The recommended tire pressure for your Tata Tiago is:

- Front tires: 30 PSI
- Rear tires: 28 PSI

Important notes:
- These values are for cold tires (before driving)
- Check tire pressure monthly
- The recommended values are also printed on the driver's door jamb for reference
```

**Final Response:**
```python
{
    "answer": "The recommended tire pressure for your Tata Tiago is: Front: 30 PSI, Rear: 28 PSI...",
    "citations": [
        {
            "citation_number": 1,
            "car_model": "Tata Tiago",
            "excerpt": "The recommended tire pressure for Tata Tiago is 30 PSI..."
        }
    ],
    "confidence": "high"
}
```

---

## Why RAG Works Well Here

1. **Grounded Answers**: Answers come from actual manual content, not LLM's training data
2. **Up-to-date**: Can add new manuals without retraining LLM
3. **Transparent**: Citations show where information came from
4. **Accurate**: Reduces hallucinations by constraining LLM to provided context
5. **Flexible**: Works with different LLM providers (OpenAI, Ollama, or none)

---

## Configuration

**Enable RAG with OpenAI:**
```bash
# Create .env file
echo "OPENAI_API_KEY=your_key_here" > .env
```

**Enable RAG with Ollama:**
```bash
# Install Ollama locally, then:
echo "USE_OLLAMA=true" >> .env
```

**Disable RAG (use simple extraction):**
- Don't set API keys
- System automatically falls back to simple extraction
- Still provides search and citations

---

This RAG implementation ensures accurate, cited answers while leveraging the power of LLMs for natural language generation.

