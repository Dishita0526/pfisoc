import fitz # PyMuPDF
import json
import uuid

# --- GLOBAL CONFIGURATION (These are placeholder values for chunking) ---
# Aim for ~2000 tokens per chunk for optimal Gemini processing
MAX_CHARS_PER_CHUNK = 8000 
OVERLAP_CHARS = 1000 # To maintain context between chunks

def extract_and_chunk_pdf(pdf_path: str) -> list[dict]:
    """
    Extracts text from a PDF, attempts to structure it by paragraphs, 
    and chunks the text into manageable sizes for the AI.
    
    Args:
        pdf_path: The local file path to the uploaded PDF.

    Returns:
        A list of dictionaries, where each dictionary is a text chunk 
        ready for the AI parser.
    """
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return []

    full_text = ""
    for page_num in range(len(doc)):
        # Extract text block by block to preserve some structure (headings, paragraphs)
        page = doc.load_page(page_num)
        text_blocks = page.get_text("blocks")
        
        for block in text_blocks:
            # block[4] is the text content
            text_content = block[4].strip()
            if text_content:
                # Add a separator to help downstream parsing identify page breaks/block breaks
                full_text += f"\n\n[PAGE_{page_num+1}] {text_content}"
    
    doc.close()

    # Split the document into segments based on typical paragraph/section breaks
    segments = full_text.split('\n\n')
    
    chunks = []
    current_chunk_text = ""
    
    for segment in segments:
        if not segment.strip():
            continue

        # If adding the new segment exceeds the max length, finalize the current chunk
        if len(current_chunk_text) + len(segment) > MAX_CHARS_PER_CHUNK:
            if current_chunk_text:
                # Finalize the current chunk
                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "content": current_chunk_text.strip(),
                    # The page number will be an estimate based on the first occurrence in the chunk
                    "source_page_start": current_chunk_text.split("[PAGE_")[1].split("]")[0] if "[PAGE_" in current_chunk_text else "1"
                })
            
            # Start a new chunk, incorporating overlap for context
            # Find the starting point for overlap
            overlap_start = max(0, len(current_chunk_text) - OVERLAP_CHARS)
            overlap_content = current_chunk_text[overlap_start:]
            
            current_chunk_text = overlap_content + "\n\n" + segment
        else:
            # Otherwise, just append the segment
            if current_chunk_text:
                current_chunk_text += "\n\n" + segment
            else:
                current_chunk_text = segment

    # Add the final remaining chunk
    if current_chunk_text:
        chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "content": current_chunk_text.strip(),
            "source_page_start": current_chunk_text.split("[PAGE_")[1].split("]")[0] if "[PAGE_" in current_chunk_text else "1"
        })
        
    print(f"Document processed into {len(chunks)} chunks for AI analysis.")
    return chunks

# Example of how this module would be used:
if __name__ == '__main__':
    # NOTE: In the Flask app, this would receive the path to the uploaded temp file.
    # For testing, replace 'path/to/your/document.pdf' with a real file path.
    # chunks_for_ai = extract_and_chunk_pdf("path/to/your/document.pdf")
    # print(json.dumps(chunks_for_ai[0], indent=2))
    pass
