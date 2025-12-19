"""
PDF Processor Module
Extracts text from car manuals and stores them in a structured format.
"""

import pdfplumber
import os
from typing import Dict, List, Tuple
import json


class PDFProcessor:
    """Processes PDF manuals and extracts text content."""
    
    def __init__(self, manuals_dir: str = "manuals"):
        self.manuals_dir = manuals_dir
        self.manuals_data = {}
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from a PDF file."""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
        return text
    
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
    
    def process_manual(self, pdf_path: str, car_model: str) -> Dict:
        """Process a manual PDF and return structured data."""
        print(f"Processing {car_model} manual...")
        full_text = self.extract_text_from_pdf(pdf_path)
        chunks = self.chunk_text(full_text)
        
        manual_data = {
            "car_model": car_model,
            "full_text": full_text,
            "chunks": chunks,
            "total_chunks": len(chunks)
        }
        
        self.manuals_data[car_model] = manual_data
        return manual_data
    
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
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        print(f"Saved processed data to {output_path}")
    
    def load_processed_data(self, input_path: str = "processed_manuals.json") -> Dict:
        """Load processed manual data from JSON file."""
        if os.path.exists(input_path):
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.manuals_data = data
            return data
        return {}
    
    def get_available_models(self) -> List[str]:
        """Get list of available car models."""
        return list(self.manuals_data.keys())


def detect_car_model(question: str) -> str:
    """Detect which car model the question is about."""
    question_lower = question.lower()
    
    # Check for MG Astor
    astor_keywords = ["astor", "mg astor", "mg"]
    if any(keyword in question_lower for keyword in astor_keywords):
        return "MG Astor"
    
    # Check for Tata Tiago
    tiago_keywords = ["tiago", "tata tiago", "tata"]
    if any(keyword in question_lower for keyword in tiago_keywords):
        return "Tata Tiago"
    
    return None
