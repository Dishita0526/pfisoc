import os
import json
import time
import requests
import uuid
from typing import List, Dict, Any

# API configuration 
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key="

# System instruction
SYSTEM_PROMPT = """You are a highly specialized and meticulous Regulatory Compliance Analyst. Your task is to analyze a given section of a legal document, identify all explicit and implicit compliance obligations, and translate them into structured, actionable tasks. You must strictly adhere to the provided JSON schema for output. If no clear obligation is found in the text, you must return an empty list: []."""

# JSON schema
OBLIGATION_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "summary": {"type": "string", "description": "A concise, actionable summary of the compliance requirement (e.g., 'Ensure all data is encrypted with 256-bit AES')."},
            "department": {"type": "string", "description": "The primary department responsible for execution (e.g., 'IT', 'Legal', 'Operations', 'Product')."},
            "risk_score": {"type": "string", "description": "The estimated risk level (High, Medium, Low) associated with non-compliance."},
            "remediation_steps": {"type": "string", "description": "A brief, suggested action plan to achieve compliance."},
            "xai_rationale": {"type": "string", "description": "A brief, direct sentence from the input text that justifies this obligation and its risk score (XAI - Explainable AI)."}
        },
        "required": ["summary", "department", "risk_score", "remediation_steps", "xai_rationale"]
    }
}

def analyze_compliance_chunks(structured_chunks: list[dict], app_id: str, api_key: str) -> list[dict]:
    """
    Iterates through structured text chunks, calls the Gemini API for analysis,
    and returns a consolidated list of structured compliance tasks.

    Args:
        structured_chunks: List of dictionaries from extract.py.
        app_id: The unique application ID for context.
        api_key: The required key for authenticating the Gemini API call (CRITICAL).

    Returns:
        A flat list of all successfully analyzed compliance tasks.
    """
    
    # Check API key status
    if not api_key:
        print("!!! CRITICAL ERROR: API Key is NOT present in arguments. All requests will fail with 403 Forbidden. !!!")

    all_analyzed_tasks = []
    total_chunks = len(structured_chunks)
    
    print(f"--- AI ANALYSIS START: {total_chunks} Chunks ---")

    for index, chunk in enumerate(structured_chunks):
        chunk_id = chunk['chunk_id']
        chunk_content = chunk['content']
        
        print(f"Processing Chunk {index + 1}/{total_chunks} (ID: {chunk_id[:8]}...)")

        user_prompt = f"Analyze the following section from a regulatory document and extract all obligations:\n\n---\n{chunk_content}\n---"
        
        payload = {
            "contents": [{ "parts": [{ "text": user_prompt }] }],
            "systemInstruction": { "parts": [{ "text": SYSTEM_PROMPT }] },
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": OBLIGATION_SCHEMA
            },
        }

        # --- API Call with Exponential Backoff and Error Handling ---
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # 1. API Request
                response = requests.post(
                    GEMINI_API_URL + api_key, # Use the passed argument here
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps(payload),
                    timeout=30
                )
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                # 2. Extract and Parse JSON (Crucial Step)
                response_data = response.json()
                
                json_string = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '[]')
                
                extracted_obligations = json.loads(json_string) 
                
                # 3. Process Valid Obligations
                if isinstance(extracted_obligations, list) and extracted_obligations:
                    print(f"  -> SUCCESS: Found {len(extracted_obligations)} obligations in chunk.")
                    for task_index, task in enumerate(extracted_obligations):
                        # Add audit trail context to each task
                        task['original_chunk_id'] = chunk_id
                        task['source_page'] = chunk.get('source_page_start', 'Unknown')
                        task['analysis_timestamp'] = time.time()
                        
                        task['obligation_id'] = str(uuid.uuid4())
                        
                        all_analyzed_tasks.append(task)

                break # Exit retry loop on success

            except requests.exceptions.Timeout:
                print(f"  -> WARNING: API Timeout on chunk {index + 1}. Retrying in {retry_delay}s...")
            except requests.exceptions.RequestException as e:
                print(f"  -> ERROR: API Request failed for chunk {index + 1}: {e}")
            except json.JSONDecodeError as e:
                # CRITICAL DEBUG LOG
                print(f"  -> CRITICAL JSON PARSE ERROR on chunk {index + 1}: {e}")
                print(f"  -> RAW OUTPUT from AI (DEBUG): {json_string[:500]}...")
            except Exception as e:
                print(f"  -> UNEXPECTED ERROR during processing chunk {index + 1}: {e}")
            
            # Exponential backoff
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print(f"  -> MAX RETRIES REACHED for chunk {index + 1}. Skipping.")
        
    print(f"--- AI ANALYSIS END: {len(all_analyzed_tasks)} total tasks identified ---")
    return all_analyzed_tasks
