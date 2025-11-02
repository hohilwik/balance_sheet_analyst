import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './FileViewer.css'; //TODO generate this css file 

const FileViewer = () => {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileData, setFileData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pagination, setPagination] = useState({
    currentPage: 1,
    pageSize: 50,
    totalRows: 0
  });

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      setError('');
      const response = await axios.get('http://localhost:5000/api/user/files');
      
      if (response.data && Array.isArray(response.data)) {
        setFiles(response.data);
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (error) {
      console.error('Error fetching files:', error);
      setError('Failed to load files. Please try again later.');
      setFiles([]);
    }
  };

  const fetchFileData = async (filename) => {
    if (!filename) {
      setError('No file selected');
      return;
    }

    setLoading(true);
    setError('');
    setSelectedFile(filename);
    setFileData(null);
    setPagination({
      currentPage: 1,
      pageSize: 50,
      totalRows: 0
    });

    try {
      const response = await axios.get(`http://localhost:5000/api/user/file/${filename}`);
      
      // Enhanced response validation
      if (!response.data) {
        throw new Error('No data received from server');
      }

      let columns = [];
      let data = [];

      // Handle different response structures
      if (response.data.columns && response.data.data) {
        // Standard structure: { columns: [], data: [] }
        columns = response.data.columns;
        data = response.data.data;
      } else if (Array.isArray(response.data) && response.data.length > 0) {
        // Array structure: assume first row is headers
        columns = response.data[0];
        data = response.data.slice(1);
      } else {
        throw new Error('Unexpected data format from server');
      }

      // Validate and process columns
      if (!Array.isArray(columns)) {
        console.warn('Columns is not an array, creating default columns');
        columns = data.length > 0 ? 
          Array.from({ length: data[0]?.length || 0 }, (_, i) => `Column ${i + 1}`) : 
          ['Column 1'];
      }

      // Validate and process data
      if (!Array.isArray(data)) {
        console.warn('Data is not an array, using empty array');
        data = [];
      }

      // Process data to handle missing values and ensure consistency
      const processedData = data.map((row, index) => {
        // Handle null/undefined rows
        if (row === null || row === undefined) {
          console.warn(`Row ${index} is null or undefined`);
          return Array(columns.length).fill('N/A');
        }

        // Convert row to array if it's not already
        let rowArray;
        if (Array.isArray(row)) {
          rowArray = [...row];
        } else if (typeof row === 'object') {
          // Convert object to array using column order
          rowArray = columns.map(col => row[col] ?? 'N/A');
        } else {
          console.warn(`Row ${index} is not an array or object:`, row);
          rowArray = [String(row)];
        }

        // Ensure row has same length as columns
        const processedRow = [...rowArray];
        if (processedRow.length < columns.length) {
          const missingColumns = columns.length - processedRow.length;
          for (let i = 0; i < missingColumns; i++) {
            processedRow.push('N/A');
          }
        } else if (processedRow.length > columns.length) {
          // Truncate extra columns if any
          processedRow.length = columns.length;
        }

        // Convert all values to strings and handle null/undefined
        return processedRow.map(cell => {
          if (cell === null || cell === undefined) {
            return 'N/A';
          }
          return String(cell);
        });
      });

      console.log('Processed data:', {
        columns,
        processedData: processedData.slice(0, 5) // Log first 5 rows for debugging
      });

      setFileData({
        columns,
        data: processedData
      });

      setPagination(prev => ({
        ...prev,
        totalRows: processedData.length
      }));

    } catch (error) {
      console.error('Error fetching file data:', error);
      
      let errorMessage = 'Failed to load file data. ';
      
      if (error.response) {
        // Server responded with error status
        if (error.response.status === 404) {
          errorMessage += 'File not found.';
        } else if (error.response.status === 403) {
          errorMessage += 'Access denied.';
        } else if (error.response.data && error.response.data.error) {
          errorMessage += error.response.data.error;
        } else {
          errorMessage += `Server error: ${error.response.status}`;
        }
      } else if (error.request) {
        // Request was made but no response received
        errorMessage += 'No response from server. Please check your connection.';
      } else {
        // Something else happened
        errorMessage += error.message || 'Unknown error occurred.';
      }
      
      setError(errorMessage);
      setFileData(null);
    } finally {
      setLoading(false);
    }
  };

  // Get current page data
  const getCurrentPageData = () => {
    if (!fileData || !fileData.data || !Array.isArray(fileData.data)) {
      return [];
    }
    
    const startIndex = (pagination.currentPage - 1) * pagination.pageSize;
    const endIndex = startIndex + pagination.pageSize;
    return fileData.data.slice(startIndex, endIndex);
  };

  // Handle pagination
  const handlePageChange = (newPage) => {
    setPagination(prev => ({
      ...prev,
      currentPage: newPage
    }));
  };

  // Calculate total pages
  const totalPages = Math.ceil(pagination.totalRows / pagination.pageSize);

  // Render table headers safely
  const renderTableHeaders = () => {
    if (!fileData || !fileData.columns || !Array.isArray(fileData.columns)) {
      return (
        <tr>
          <th colSpan="1">No columns available</th>
        </tr>
      );
    }

    return fileData.columns.map((column, index) => {
      const columnName = column || `Column ${index + 1}`;
      return (
        <th key={`header-${index}`} title={columnName}>
          {columnName}
        </th>
      );
    });
  };

  // Render table rows safely
  const renderTableRows = () => {
    const currentData = getCurrentPageData();
    
    if (!currentData || currentData.length === 0) {
      return (
        <tr>
          <td colSpan={fileData?.columns?.length || 1} className="no-data">
            No data available
          </td>
        </tr>
      );
    }

    return currentData.map((row, rowIndex) => {
      // Ensure row is an array
      const safeRow = Array.isArray(row) ? row : [];
      
      return (
        <tr key={`row-${rowIndex}`}>
          {safeRow.map((cell, cellIndex) => {
            const cellValue = cell !== null && cell !== undefined ? String(cell) : 'N/A';
            return (
              <td key={`cell-${rowIndex}-${cellIndex}`} title={cellValue}>
                {cellValue}
              </td>
            );
          })}
        </tr>
      );
    });
  };

  // Download CSV functionality
  const downloadCSV = () => {
    if (!fileData || !fileData.columns || !fileData.data) {
      setError('No data available to download');
      return;
    }

    try {
      const headers = fileData.columns.join(',');
      const csvContent = fileData.data.map(row => 
        row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
      ).join('\n');
      
      const fullCSV = [headers, csvContent].join('\n');
      const blob = new Blob([fullCSV], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = selectedFile || 'data.csv';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading CSV:', error);
      setError('Failed to download file');
    }
  };

  return (
    <div className="file-viewer">
      <div className="file-viewer-header">
        <h2>Company Data Files</h2>
        {selectedFile && fileData && (
          <button onClick={downloadCSV} className="download-btn">
            Download CSV
          </button>
        )}
      </div>
      
      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError('')} className="close-error">×</button>
        </div>
      )}

      <div className="file-viewer-content">
        <div className="file-list-section">
          <div className="file-list-header">
            <h3>Available Files</h3>
            <button 
              onClick={fetchFiles} 
              className="refresh-btn"
              title="Refresh file list"
            >
              ↻
            </button>
          </div>
          <div className="file-list">
            {files.length === 0 ? (
              <div className="no-files">No files available</div>
            ) : (
              files.map(file => (
                <button
                  key={file}
                  className={`file-item ${selectedFile === file ? 'active' : ''}`}
                  onClick={() => fetchFileData(file)}
                  disabled={loading}
                >
                  <span className="file-name">{file}</span>
                  {loading && selectedFile === file && (
                    <span className="loading-spinner"></span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        <div className="file-preview-section">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner large"></div>
              <p>Loading {selectedFile}...</p>
            </div>
          ) : fileData ? (
            <div className="file-preview">
              <div className="file-preview-header">
                <h3>{selectedFile}</h3>
                <div className="file-info">
                  <span>{pagination.totalRows} rows</span>
                  <span>{fileData.columns.length} columns</span>
                  <span>Page {pagination.currentPage} of {totalPages}</span>
                </div>
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      {renderTableHeaders()}
                    </tr>
                  </thead>
                  <tbody>
                    {renderTableRows()}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="pagination-controls">
                  <button
                    onClick={() => handlePageChange(1)}
                    disabled={pagination.currentPage === 1}
                  >
                    First
                  </button>
                  <button
                    onClick={() => handlePageChange(pagination.currentPage - 1)}
                    disabled={pagination.currentPage === 1}
                  >
                    Previous
                  </button>
                  
                  <span className="page-info">
                    Page {pagination.currentPage} of {totalPages}
                  </span>

                  <button
                    onClick={() => handlePageChange(pagination.currentPage + 1)}
                    disabled={pagination.currentPage === totalPages}
                  >
                    Next
                  </button>
                  <button
                    onClick={() => handlePageChange(totalPages)}
                    disabled={pagination.currentPage === totalPages}
                  >
                    Last
                  </button>

                  <select
                    value={pagination.pageSize}
                    onChange={(e) => setPagination({
                      currentPage: 1,
                      pageSize: parseInt(e.target.value),
                      totalRows: pagination.totalRows
                    })}
                    className="page-size-select"
                  >
                    <option value={20}>20 rows</option>
                    <option value={50}>50 rows</option>
                    <option value={100}>100 rows</option>
                    <option value={200}>200 rows</option>
                  </select>
                </div>
              )}
            </div>
          ) : (
            <div className="no-file-selected">
              <div className="placeholder-icon">📊</div>
              <h3>No File Selected</h3>
              <p>Select a file from the list to view its contents</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileViewer;