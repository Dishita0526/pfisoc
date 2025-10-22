import React, { useState } from "react";

// NOTE: This file assumes Tailwind CSS is available for styling (not included in this snippet)

function UploadForm() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!file) {
      alert("Please select a PDF file first!");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);

    // --- Timeout Logic Added ---
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 900000); // 5 minutes (in milliseconds)

    try {
      const response = await fetch("http://127.0.0.1:5000/upload_regulation", {
        method: "POST",
        body: formData,
        signal: controller.signal, // Attach abort signal
      });

      clearTimeout(timeoutId); // Stop timeout if success

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      if (err.name === "AbortError") {
        setError("⏰ The server took too long to respond. Please try again or use a smaller PDF.");
      } else {
        setError(`Analysis Failed: ${err.message}`);
      }
      console.error("Error during analysis pipeline:", err);
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  };

  // --- Helper function to format JSON output ---
  const formatJson = (data) => {
    try {
      return JSON.stringify(data, null, 2);
    } catch (e) {
      return "Error displaying results.";
    }
  };

  return (
    <div className="upload-form p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Upload Regulatory Document</h2>

      <form onSubmit={handleUpload} className="flex space-x-4 mb-8">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="file-input file-input-bordered w-full max-w-xs"
        />
        <button
          type="submit"
          disabled={loading || !file}
          className="px-4 py-2 bg-indigo-600 text-white font-semibold rounded-lg shadow-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Upload & Analyze"}
        </button>
      </form>

      {/* --- Status Display --- */}
      {loading && (
        <p className="text-xl text-indigo-600 font-medium">
          Extracting text and preparing for AI analysis... (This may take several minutes for long documents)
        </p>
      )}

      {error && (
        <div
          className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mt-4"
          role="alert"
        >
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}

      {/* --- Result Display (for Phase 2 debugging) --- */}
      {result && result.analyzed_tasks && (
        <div className="result mt-6">
          <p className="text-lg font-semibold mb-2 text-green-700">
            <span className="font-extrabold text-2xl mr-2">✅</span> Analysis Pipeline Initiated!
          </p>
          <p className="mb-4">
            AI analysis complete. **{result.analyzed_tasks.length}** compliance tasks identified.
          </p>

          <h3 className="text-xl font-bold mt-6 mb-3">Structured Tasks (JSON Output)</h3>
          <div className="bg-gray-800 p-4 rounded-lg shadow-xl overflow-x-auto">
            <pre className="text-green-400 text-xs whitespace-pre-wrap font-mono">
              {formatJson(result.analyzed_tasks)}
            </pre>
          </div>

          <p className="mt-8 italic text-sm text-gray-500">
            *This raw output is only for development. In the final version (Phase 3), the results (Tasks, Gaps, Audit
            Trail) will appear here shortly (via Firestore).
          </p>
        </div>
      )}
    </div>
  );
}

export default UploadForm;
