/**
 * Bulk User Upload Component
 * OPETSE-20: CSV Bulk Upload Feature
 */
import React, { useState } from 'react';
import { InstructorOnly } from '../components/ProtectedContent';

const BulkUserUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/v1/users/bulk-upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
        setFile(null);
        // Reset file input
        document.getElementById('csv-file-input').value = '';
      } else {
        setError(data.detail || 'Upload failed');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    const csvContent = 'email,name,role\nstudent@example.com,John Doe,student\ninstructor@example.com,Jane Smith,instructor\n';
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'student_upload_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <InstructorOnly fallback={<div className="p-4 text-center text-red-500">Only instructors can bulk upload users.</div>}>
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-4">Bulk User Upload</h2>
        
        <div className="mb-6">
          <p className="text-gray-600 mb-2">
            Upload a CSV file to create multiple user accounts at once.
          </p>
          <button
            onClick={downloadTemplate}
            className="text-blue-600 hover:text-blue-800 underline text-sm"
          >
            Download CSV Template
          </button>
        </div>

        <div className="mb-4">
          <label className="block mb-2 font-semibold">Select CSV File</label>
          <input
            id="csv-file-input"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            disabled={uploading}
          />
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className={`w-full py-2 px-4 rounded font-semibold ${
            !file || uploading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {uploading ? 'Uploading...' : 'Upload Users'}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
            <p className="text-red-700 font-semibold">Error:</p>
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {result && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
            <p className="text-green-700 font-semibold mb-2">{result.message}</p>
            
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{result.summary.created}</p>
                <p className="text-sm text-gray-600">Created</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">{result.summary.skipped}</p>
                <p className="text-sm text-gray-600">Skipped</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{result.summary.failed}</p>
                <p className="text-sm text-gray-600">Failed</p>
              </div>
            </div>

            {result.skipped_users && result.skipped_users.length > 0 && (
              <div className="mt-3">
                <p className="font-semibold text-yellow-700 mb-1">Skipped Users:</p>
                <ul className="text-sm text-yellow-600">
                  {result.skipped_users.map((user, idx) => (
                    <li key={idx}>
                      {user.email}: {user.reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.failed_users && result.failed_users.length > 0 && (
              <div className="mt-3">
                <p className="font-semibold text-red-700 mb-1">Failed Users:</p>
                <ul className="text-sm text-red-600">
                  {result.failed_users.map((user, idx) => (
                    <li key={idx}>
                      {user.email}: {user.reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.validation_errors && result.validation_errors.length > 0 && (
              <div className="mt-3">
                <p className="font-semibold text-orange-700 mb-1">Validation Errors:</p>
                <ul className="text-sm text-orange-600">
                  {result.validation_errors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <div className="mt-6 p-4 bg-gray-50 rounded">
          <p className="font-semibold mb-2">CSV Format Requirements:</p>
          <ul className="text-sm text-gray-600 list-disc list-inside">
            <li>Required columns: <code className="bg-gray-200 px-1">email</code>, <code className="bg-gray-200 px-1">name</code></li>
            <li>Optional column: <code className="bg-gray-200 px-1">role</code> (student or instructor, defaults to student)</li>
            <li>First row must contain column headers</li>
            <li>Email addresses must be valid and unique</li>
          </ul>
        </div>
      </div>
    </InstructorOnly>
  );
};

export default BulkUserUpload;
