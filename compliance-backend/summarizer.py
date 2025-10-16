# summarizer.py
from transformers import pipeline
import torch
import textwrap
import threading

MODEL_NAME = "facebook/bart-large-cnn"

_model_lock = threading.Lock()
_summarizer_pipeline = None

def _load_pipeline():
    global _summarizer_pipeline
    with _model_lock:
        if _summarizer_pipeline is None:
            device = 0 if torch.cuda.is_available() else -1
            print(f"[summarizer] Loading model {MODEL_NAME} on {'GPU' if device==0 else 'CPU'} ...")
            _summarizer_pipeline = pipeline("summarization", model=MODEL_NAME, device=device)
            print("[summarizer] Model loaded.")
    return _summarizer_pipeline

def chunk_text(text, max_chunk_length=1000):
    paragraphs = textwrap.wrap(text, width=max_chunk_length)
    return paragraphs

def summarize_text(text):
    pipeline_inst = _load_pipeline()
    chunks = chunk_text(text)
    summaries = []
    for chunk in chunks:
        summary = pipeline_inst(chunk, max_length=150, min_length=30, do_sample=False)
        summaries.append(summary[0]["summary_text"])
    return summaries
