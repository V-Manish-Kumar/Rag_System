/**
 * Main App Component
 */

import React from 'react';
import Header from './components/Header';
import DocumentInput from './components/DocumentInput';
import QueryInterface from './components/QueryInterface';
import './App.css';

function App() {
  const handleIngestionComplete = (result) => {
    console.log('Ingestion completed:', result);
    // You can add additional logic here, like showing a notification
  };

  return (
    <div className="app">
      <Header />
      
      <main className="main-content">
        <div className="container">
          <DocumentInput onIngestionComplete={handleIngestionComplete} />
          <QueryInterface />
        </div>
      </main>
      
      <footer className="app-footer">
        <p className="footer-title">Built with:</p>
        <div className="tech-logos">
          <a href="https://fastapi.tiangolo.com/" target="_blank" rel="noopener noreferrer" title="FastAPI">
            <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-original.svg" alt="FastAPI" className="tech-logo" />
          </a>
          <a href="https://www.langchain.com/" target="_blank" rel="noopener noreferrer" title="LangChain">
            <img src="https://avatars.githubusercontent.com/u/126733545?s=200&v=4" alt="LangChain" className="tech-logo" />
          </a>
          <a href="https://qdrant.tech/" target="_blank" rel="noopener noreferrer" title="Qdrant">
            <img src="https://avatars.githubusercontent.com/u/73504361?s=200&v=4" alt="Qdrant" className="tech-logo" />
          </a>
          <a href="https://ai.google.dev/gemini-api" target="_blank" rel="noopener noreferrer" title="Google Gemini">
            <img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" alt="Google Gemini" className="tech-logo" />
          </a>
          <a href="https://jina.ai/" target="_blank" rel="noopener noreferrer" title="Jina AI">
            <img src="https://avatars.githubusercontent.com/u/60539444?s=200&v=4" alt="Jina AI" className="tech-logo" />
          </a>
        </div>
      </footer>
    </div>
  );
}

export default App;
