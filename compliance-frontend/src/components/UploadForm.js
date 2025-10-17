import React, { useState } from "react";

function UploadForm() {
  const [file, setFile] = useState(null);
  const [clauses, setClauses] = useState([]); // <-- default to empty array
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setErrorMsg("");
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      alert("Please select a PDF file first!");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setErrorMsg("");
    try {
      // Step 1: Upload PDF and extract text
      const uploadResponse = await fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData,
      });

      const uploadData = await uploadResponse.json();
      if (!uploadResponse.ok) {
        const msg = uploadData.error || "Upload failed";
        setErrorMsg(msg);
        return;
      }

      if (!uploadData.text) {
        setErrorMsg("Failed to extract text from PDF");
        return;
      }

      // Step 2: Send extracted text to summarizer immediately
      const summarizeResponse = await fetch("http://127.0.0.1:5000/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: uploadData.text }),
      });

      const summarizeData = await summarizeResponse.json();
      if (!summarizeResponse.ok) {
        const msg = summarizeData.error || "Summarization failed";
        setErrorMsg(msg);
        return;
      }

      if (summarizeData.summaries) {
        setClauses(summarizeData.summaries);
      } else {
        setErrorMsg("Unexpected summarizer response");
        console.error("Unexpected summarizer response:", summarizeData);
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      setErrorMsg(String(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-form">
      <h2>Upload PDF</h2>
      <form onSubmit={handleUpload}>
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
        />
        <button type="submit" disabled={loading}>Upload</button>
      </form>

      {loading && <p>Processing... Please wait ⏳</p>}
      {errorMsg && <p style={{ color: "red" }}>Error: {errorMsg}</p>}

      {clauses && clauses.length > 0 && (
        <div className="clauses">
          <h3>🧠 Extracted / Summarized Clauses</h3>
          <ul>
            {clauses.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default UploadForm;
