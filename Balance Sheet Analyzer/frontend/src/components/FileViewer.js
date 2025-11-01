import React, { useState, useEffect } from 'react';
import axios from 'axios';

const FileViewer = () => {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileData, setFileData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/user/files');
      setFiles(response.data);
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  const fetchFileData = async (filename) => {
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:5000/api/user/file/${filename}`);
      setFileData(response.data);
      setSelectedFile(filename);
    } catch (error) {
      console.error('Error fetching file data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="file-viewer">
      <h2>Company Data Files</h2>
      
      <div className="file-viewer-content">
        <div className="file-list">
          <h3>Available Files</h3>
          {files.map(file => (
            <button
              key={file}
              className={`file-item ${selectedFile === file ? 'active' : ''}`}
              onClick={() => fetchFileData(file)}
            >
              {file}
            </button>
          ))}
        </div>

        <div className="file-preview">
          {loading ? (
            <div>Loading file data...</div>
          ) : fileData ? (
            <div>
              <h3>{selectedFile}</h3>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      {fileData.columns.map(column => (
                        <th key={column}>{column}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {fileData.data.map((row, index) => (
                      <tr key={index}>
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div>Select a file to view its contents</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileViewer;