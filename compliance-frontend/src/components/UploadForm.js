import React, { useState } from 'react';

function UploadForm({ onUpload }) {
  const [file, setFile] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (file) {
      onUpload(file);
    } else {
      alert("Please select a file first!");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input 
        type="file" 
        accept=".png,.jpg,.jpeg,.pdf" 
        onChange={(e) => setFile(e.target.files[0])} 
      />
      <button type="submit">Upload</button>
    </form>
  );
}

export default UploadForm;
