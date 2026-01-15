/**
 * API service for communicating with the backend.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Ingest text document
 */
export const ingestText = async (text, source = null, title = null, metadata = null) => {
  const response = await api.post('/ingest', {
    text,
    source,
    title,
    metadata,
  });
  return response.data;
};

/**
 * Ingest file (PDF, TXT, DOCX)
 */
export const ingestFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/ingest/file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Query the knowledge base
 */
export const queryKnowledgeBase = async (query) => {
  const response = await api.post('/query', { query });
  return response.data;
};

/**
 * Clear all documents
 */
export const clearKnowledgeBase = async () => {
  const response = await api.delete('/clear');
  return response.data;
};

/**
 * Get statistics
 */
export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

/**
 * Health check
 */
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
