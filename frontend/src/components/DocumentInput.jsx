/**
 * DocumentInput Component
 * Allows users to paste text or upload files for ingestion.
 */

import React, { useState } from 'react';
import { ingestText, ingestFile } from '../api';
import './DocumentInput.css';

const DocumentInput = ({ onIngestionComplete }) => {
  const [text, setText] = useState('');
  const [source, setSource] = useState('');
  const [title, setTitle] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('text'); // 'text' or 'file'

  const handleTextIngest = async () => {
    if (!text.trim()) {
      setError('Please enter some text to ingest');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await ingestText(text, source || null, title || null);
      setSuccess(`Successfully ingested! ${result.chunks_added} chunks added in ${result.total_time_seconds}s`);
      setText('');
      setSource('');
      setTitle('');
      
      if (onIngestionComplete) {
        onIngestionComplete(result);
      }
    } catch (err) {
      setError(`Ingestion failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFileIngest = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await ingestFile(file);
      setSuccess(`Successfully ingested ${file.name}! ${result.chunks_added} chunks added in ${result.total_time_seconds}s`);
      setFile(null);
      document.getElementById('file-input').value = '';
      
      if (onIngestionComplete) {
        onIngestionComplete(result);
      }
    } catch (err) {
      setError(`File ingestion failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="document-input">
      <h2>Add Documents to Knowledge Base</h2>
      
      <div className="tabs">
        <button 
          className={activeTab === 'text' ? 'active' : ''} 
          onClick={() => setActiveTab('text')}
        >
          Paste Text
        </button>
        <button 
          className={activeTab === 'file' ? 'active' : ''} 
          onClick={() => setActiveTab('file')}
        >
          Upload File
        </button>
      </div>

      {activeTab === 'text' ? (
        <div className="text-input-section">
          <input
            type="text"
            placeholder="Title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input-field"
          />
          <input
            type="text"
            placeholder="Source (optional)"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="input-field"
          />
          <textarea
            placeholder="Paste your text here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={10}
            className="text-area"
          />
          <button 
            onClick={handleTextIngest} 
            disabled={loading || !text.trim()}
            className="ingest-btn"
          >
            {loading ? 'Ingesting...' : 'Ingest Text'}
          </button>
        </div>
      ) : (
        <div className="file-input-section">
          <input
            id="file-input"
            type="file"
            accept=".pdf,.txt,.docx"
            onChange={(e) => setFile(e.target.files[0])}
            className="file-input"
          />
          {file && <p className="file-name">Selected: {file.name}</p>}
          <button 
            onClick={handleFileIngest} 
            disabled={loading || !file}
            className="ingest-btn"
          >
            {loading ? 'Uploading...' : 'Upload & Ingest'}
          </button>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
    </div>
  );
};

export default DocumentInput;
