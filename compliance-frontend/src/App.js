import React, { useState } from 'react';
import UploadForm from './components/UploadForm';

function App() {
  const [result, setResult] = useState("");

  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://127.0.0.1:8000/upload/", {
      method: "POST",
      body: formData
    });
    const data = await response.json();
    setResult(data.text);
  };

  return (
    <div>
      <UploadForm onUpload={handleUpload} />
      <h3>Extracted Text:</h3>
      <pre>{result}</pre>
    </div>
  );
}

export default App;
