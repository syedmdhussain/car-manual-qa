"""
Streamlit Web Application for Car Manual Q&A
"""

import streamlit as st
import os
from pdf_processor import PDFProcessor, detect_car_model
from search_engine import ManualSearchEngine
from qa_system import QASystem
from rag_qa_system import RAGQASystem


# Page configuration
st.set_page_config(
    page_title="Car Manual Q&A",
    page_icon="🚗",
    layout="wide"
)

# Initialize session state
if 'search_engine' not in st.session_state:
    st.session_state.search_engine = None
if 'qa_system' not in st.session_state:
    # Try to use RAG system, fallback to simple Q&A
    use_rag = os.getenv("OPENAI_API_KEY") or os.getenv("USE_OLLAMA", "").lower() == "true"
    if use_rag:
        st.session_state.qa_system = RAGQASystem(use_llm=True)
    else:
        st.session_state.qa_system = QASystem()
if 'manuals_loaded' not in st.session_state:
    st.session_state.manuals_loaded = False


@st.cache_resource
def load_manuals():
    """Load and process car manuals."""
    processor = PDFProcessor()
    
    # Check if processed data exists
    if os.path.exists("processed_manuals.json"):
        print("Loading pre-processed manuals...")
        manuals_data = processor.load_processed_data()
    else:
        print("Processing manuals from PDFs...")
        # Process manuals - check current directory first, then parent
        astor_paths = ["Astor Manual.pdf", "../Astor Manual.pdf"]
        tiago_paths = ["APP-TIAGO-FINAL-OMSB.pdf", "../APP-TIAGO-FINAL-OMSB.pdf"]
        
        astor_path = next((p for p in astor_paths if os.path.exists(p)), None)
        tiago_path = next((p for p in tiago_paths if os.path.exists(p)), None)
        
        if astor_path:
            processor.process_manual(astor_path, "MG Astor")
        if tiago_path:
            processor.process_manual(tiago_path, "Tata Tiago")
        
        # Save processed data
        processor.save_processed_data()
        manuals_data = processor.manuals_data
    
    return manuals_data


def initialize_search_engine():
    """Initialize the search engine."""
    if st.session_state.search_engine is None:
        with st.spinner("Initializing search engine (this may take a minute)..."):
            manuals_data = load_manuals()
            search_engine = ManualSearchEngine()
            search_engine.build_index(manuals_data)
            st.session_state.search_engine = search_engine
            st.session_state.manuals_loaded = True


def main():
    """Main application function."""
    st.title("🚗 Car Manual Q&A System")
    st.markdown("Ask questions about MG Astor or Tata Tiago car manuals!")
    
    # Initialize search engine
    if not st.session_state.manuals_loaded:
        initialize_search_engine()
    
    # Sidebar with information
    with st.sidebar:
        st.header("📚 Available Manuals")
        if st.session_state.manuals_loaded:
            st.success("✅ Manuals loaded successfully!")
            st.write("**Available models:**")
            st.write("- MG Astor")
            st.write("- Tata Tiago")
        else:
            st.info("Loading manuals...")
        
        # Show LLM status
        st.header("🤖 AI Status")
        if isinstance(st.session_state.qa_system, RAGQASystem):
            if st.session_state.qa_system.use_llm:
                st.success(f"✅ Using {st.session_state.qa_system.llm_provider.upper()} for RAG")
            else:
                st.info("ℹ️ Using simple extraction (no LLM)")
        else:
            st.info("ℹ️ Using simple extraction")
        
        st.header("💡 Example Questions")
        st.write("""
        - How to turn on indicator in MG Astor?
        - Which engine oil to use in Tiago?
        - How to adjust headlights in MG Astor?
        - What is the tire pressure for Tata Tiago?
        """)
        
        st.header("⚙️ Configuration")
        st.caption("To use RAG with LLM:")
        st.caption("1. Set OPENAI_API_KEY in .env file")
        st.caption("2. Or use Ollama locally")
    
    # Main input area
    st.subheader("Ask a Question")
    
    # Text input
    question = st.text_input(
        "Enter your question:",
        placeholder="e.g., How to turn on indicator in MG Astor?",
        key="question_input"
    )
    
    # Submit button
    if st.button("🔍 Search", type="primary") or question:
        if question:
            # Detect car model from question
            detected_model = detect_car_model(question)
            
            if detected_model:
                st.info(f"📌 Detected car model: **{detected_model}**")
            else:
                st.warning("⚠️ Could not detect car model. Searching all manuals...")
            
            # Search
            if st.session_state.search_engine:
                with st.spinner("Searching manual..."):
                    try:
                        # Use semantic search
                        search_results = st.session_state.search_engine.search(
                            question,
                            car_model=detected_model,
                            top_k=5
                        )
                        
                        if not search_results and detected_model:
                            # Fallback to keyword search
                            st.info("Trying keyword search...")
                            search_results = st.session_state.search_engine.simple_keyword_search(
                                question,
                                car_model=detected_model,
                                top_k=5
                            )
                        
                        # Generate answer
                        answer_data = st.session_state.qa_system.generate_answer(
                            question,
                            search_results
                        )
                        
                        # Display answer
                        st.subheader("💬 Answer")
                        st.write(answer_data["answer"])
                        
                        # Display confidence if available
                        if "confidence" in answer_data:
                            confidence = answer_data["confidence"]
                            if confidence == "high":
                                st.success("✅ High confidence answer")
                            elif confidence == "medium":
                                st.info("ℹ️ Medium confidence answer")
                            else:
                                st.warning("⚠️ Low confidence - answer may be incomplete")
                        
                        # Display citations
                        if answer_data["citations"]:
                            st.subheader("📖 Sources")
                            for citation in answer_data["citations"]:
                                with st.expander(f"Source {citation['citation_number']} - {citation['car_model']}"):
                                    st.write(citation["excerpt"])
                        
                    except Exception as e:
                        st.error(f"Error processing question: {e}")
                        st.exception(e)
            else:
                st.error("Search engine not initialized. Please refresh the page.")
        else:
            st.warning("Please enter a question.")


if __name__ == "__main__":
    main()
