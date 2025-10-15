# summarizer.py
from transformers import pipeline
import torch
import textwrap

# Use a small summarization model for speed
MODEL_NAME = "facebook/bart-large-cnn"

# Load pipeline (CPU mode by default)
device = 0 if torch.cuda.is_available() else -1
print(f"Device set to use {'GPU' if device == 0 else 'CPU'}")

summarizer_pipeline = pipeline(
    "summarization",
    model=MODEL_NAME,
    device=device
)

def chunk_text(text, max_chunk_length=1000):
    """
    Split long text into smaller chunks for summarization.
    """
    paragraphs = textwrap.wrap(text, width=max_chunk_length)
    return paragraphs

def summarize_text(text):
    """
    Summarizes long text by splitting it into chunks.
    Returns a list of summarized clauses.
    """
    chunks = chunk_text(text)
    summaries = []

    for chunk in chunks:
        summary = summarizer_pipeline(chunk, max_length=150, min_length=30, do_sample=False)
        summaries.append(summary[0]["summary_text"])

    return summaries
