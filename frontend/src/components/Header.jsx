/**
 * Header Component
 * Displays app title, status, and controls.
 */

import React, { useState, useEffect } from 'react';
import { healthCheck, clearKnowledgeBase, getStats } from '../api';
import './Header.css';

const Header = () => {
  const [status, setStatus] = useState('checking');
  const [stats, setStats] = useState(null);

  useEffect(() => {
    checkHealth();
    loadStats();
    
    // Refresh stats every 30 seconds
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      await healthCheck();
      setStatus('healthy');
    } catch (err) {
      setStatus('error');
    }
  };

  const loadStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleClear = async () => {
    if (!window.confirm('Are you sure you want to clear all documents from the knowledge base?')) {
      return;
    }

    try {
      await clearKnowledgeBase();
      alert('Knowledge base cleared successfully!');
      loadStats();
    } catch (err) {
      alert(`Failed to clear: ${err.message}`);
    }
  };

  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-left">
          <h1>Mini RAG</h1>
          <p className="subtitle">Retrieval-Augmented Generation System</p>
        </div>
        
        <div className="header-right">
          <div className="status-indicator">
            <span className={`status-dot status-${status}`}></span>
            <span>Backend: {status}</span>
          </div>
          
          {stats && (
            <div className="stats-display">
              <span>{stats.total_vectors || 0} chunks</span>
            </div>
          )}
          
          <button onClick={loadStats} className="refresh-btn" title="Refresh stats">
            Refresh
          </button>
          
          <button onClick={handleClear} className="clear-btn" title="Clear all documents">
            Clear All
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
