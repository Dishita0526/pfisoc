import React, { useState } from "react";

function UploadForm() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    // Basic file validation for PDF
    if (e.target.files.length > 0 && e.target.files[0].type === 'application/pdf') {
        setFile(e.target.files[0]);
        setError(null);
    } else {
        setFile(null);
        setError("Please select a valid PDF file.");
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!file) {
      setError("Please select a file to upload.");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    // aborting the fetch request if a timeout occurs
    const controller = new AbortController();
    const signal = controller.signal;

    // Timeout mechanism
    const timeoutId = setTimeout(() => {
        controller.abort();
        setError("Request timed out. The AI analysis took too long to respond.");
        setLoading(false);
    }, 900000); 

    try {
      // 1. POST request to /upload_regulation
      const response = await fetch("http://127.0.0.1:5000/upload_regulation", {
        method: "POST",
        body: formData,
        signal: signal, // Pass the signal to the fetch request
      });

      clearTimeout(timeoutId); // Clear the timeout if the first request returns

      if (!response.ok) {
        // Attempt to parse JSON error message from backend
        const errorData = await response.json();
        throw new Error(errorData.error || `Upload failed with status ${response.status}`);
      }

      const uploadData = await response.json(); // Data from the first POST
 
      if (!uploadData.upload_id) {
          throw new Error("Analysis started successfully, but no unique ID was returned to fetch results.");
      }

      // 2. GET request to fetch results using the returned upload_id
      const uploadId = uploadData.upload_id;
      
      const fetchResponse = await fetch(`http://127.0.0.1:5000/get_latest_tasks/${uploadId}`);
      
      if (!fetchResponse.ok) {
          const errorData = await fetchResponse.json();
          throw new Error(errorData.message || `Failed to fetch tasks: HTTP status ${fetchResponse.status}`);
      }

      const taskData = await fetchResponse.json();
      setResult(taskData);

    } catch (err) {
      if (err.name === 'AbortError') {
          // Error already set by timeout
      } else {
          setError(err.message);
      }
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  };

  // helper function to format JSON output
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
          disabled={loading || !file || error} 
          className="px-4 py-2 bg-indigo-600 text-white font-semibold rounded-lg shadow-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Upload & Analyze"}
        </button>
      </form>
      {loading && (
        <p className="text-xl text-indigo-600 font-medium">
          Extracting text and preparing for AI analysis... (This may take
          several minutes for long documents)
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

      {result && result.analyzed_tasks && (
        <div className="result mt-6">
          <p className="text-lg font-semibold mb-4 text-green-700">
            <span className="font-extrabold text-2xl mr-2">✅</span> Analysis
            Complete! **{result.analyzed_tasks.length}** Actionable Tasks
            Identified.
          </p>

          <h3 className="text-xl font-bold mt-6 mb-3">Compliance Task List</h3>

          <div className="mb-4">
            <label className="mr-2 font-semibold">Filter by Department:</label>
            {/* Implement a filter state here */}
          </div>

          <div className="overflow-x-auto">
            <table className="table-auto w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-200">
                  <th className="border p-2 text-left">Task Summary</th>
                  <th className="border p-2 text-left">Department</th>
                  <th className="border p-2 text-center">Risk</th>
                  <th className="border p-2 text-left">Remediation Steps</th>
                  <th className="border p-2 text-left">
                    XAI Rationale (Source)
                  </th>
                </tr>
              </thead>
              <tbody>
                {result.analyzed_tasks.map((task, index) => (
                  <tr
                    key={task.obligation_id || index}
                    className={index % 2 === 0 ? "bg-white" : "bg-gray-50"}
                  >
                    <td className="border p-2 font-medium">{task.summary}</td>
                    <td className="border p-2 text-sm">{task.department}</td>
                    <td
                      className={`border p-2 text-center font-bold 
                                ${
                                  task.risk_score === "High"
                                    ? "text-red-600"
                                    : task.risk_score === "Medium"
                                    ? "text-yellow-600"
                                    : "text-green-600"
                                }`}
                    >
                      {task.risk_score}
                    </td>
                    <td className="border p-2 text-sm">
                      {task.remediation_steps}
                    </td>
                    <td className="border p-2 text-xs italic text-gray-600">
                      {task.xai_rationale}{" "}
                      <span className="font-bold ml-1 text-indigo-500">
                        (P.{task.source_page})
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default UploadForm;