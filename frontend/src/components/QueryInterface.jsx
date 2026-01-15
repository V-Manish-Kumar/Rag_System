/**
 * QueryInterface Component
 * Allows users to ask questions and displays answers with citations.
 * Uses Puter.js for free, unlimited AI responses.
 */

import React, { useState } from 'react';
import axios from 'axios';
import './QueryInterface.css';

const API_URL = 'http://localhost:8000';

const QueryInterface = () => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleQuery = async () => {
    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      console.log('Starting query...');
      
      // Step 1: Retrieve context chunks from backend
      console.log('Fetching chunks from backend...');
      const retrieveResponse = await axios.post(`${API_URL}/retrieve`, {
        query: query.trim()
      });
      
      console.log('Backend response:', retrieveResponse.data);
      const { chunks, num_chunks } = retrieveResponse.data;
      
      if (!chunks || chunks.length === 0) {
        console.log('No chunks found');
        setResult({
          answer: "I couldn't find any relevant information in the knowledge base to answer your question.",
          sources: [],
          confidence: "low"
        });
        setLoading(false);
        return;
      }

      // Step 2: Build context for LLM
      console.log('Building context from chunks...');
      let contextText = "";
      const sources = [];
      
      chunks.forEach((chunk, idx) => {
        const citationId = idx + 1;
        contextText += `\n\n[${citationId}] ${chunk.text}`;
        sources.push({
          citation_id: citationId,
          text: chunk.text,
          source: chunk.metadata?.source || "Unknown",
          score: chunk.score || 0
        });
      });

      // Step 3: Create prompt
      const prompt = `You are a helpful assistant. Answer the question based ONLY on the provided context. Include citation numbers [1], [2], etc. in your answer.

CONTEXT:${contextText}

QUESTION: ${query}

ANSWER:`;

      // Step 4: Call Puter.js for LLM response (free, unlimited)
      console.log('Checking for Puter.js...');
      if (typeof window.puter === 'undefined') {
        console.error('Puter.js not found!');
        throw new Error('Puter.js not loaded. Please refresh the page.');
      }

      console.log('Calling Puter.ai.chat...');
      let llmResponse;
      try {
        llmResponse = await window.puter.ai.chat(prompt, {
          model: 'gemini-3-flash-preview'
        });
        console.log('LLM Response received:', typeof llmResponse, llmResponse);
      } catch (puterError) {
        console.error('Puter error:', puterError);
        throw new Error(`AI service error: ${puterError.message}`);
      }

      // Step 5: Estimate tokens and cost (Gemini pricing)
      const promptText = prompt;
      const responseText = String(llmResponse || '');
      
      // Rough estimation: ~4 characters per token
      const promptTokens = Math.ceil(promptText.length / 4);
      const completionTokens = Math.ceil(responseText.length / 4);
      const totalTokens = promptTokens + completionTokens;
      
      // Gemini pricing (per 1M tokens)
      // Input: $0.075, Output: $0.30 per 1M tokens
      const inputCost = (promptTokens / 1000000) * 0.075;
      const outputCost = (completionTokens / 1000000) * 0.30;
      const estimatedCost = inputCost + outputCost;

      // Step 6: Calculate confidence
      const avgScore = sources.reduce((sum, s) => sum + s.score, 0) / sources.length;
      let confidence = "low";
      if (avgScore >= 0.8) confidence = "high";
      else if (avgScore >= 0.6) confidence = "medium";

      const finalResult = {
        answer: String(llmResponse || 'No response generated'),
        sources: sources,
        confidence: confidence,
        num_sources: sources.length,
        token_stats: {
          prompt_tokens: promptTokens,
          completion_tokens: completionTokens,
          total_tokens: totalTokens
        },
        estimated_cost_usd: estimatedCost,
        retrieval_stats: {
          initial_retrieved: num_chunks || chunks.length,
          after_reranking: sources.length
        }
      };
      
      console.log('Setting result:', finalResult);
      setResult(finalResult);

    } catch (err) {
      console.error('Query error:', err);
      setError(`Query failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      console.log('Query complete, setting loading to false');
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

  return (
    <div className="query-interface">
      <h2>Ask Questions</h2>
      
      <div className="query-input-section">
        <textarea
          placeholder="Ask a question about your documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          rows={3}
          className="query-input"
        />
        <button 
          onClick={handleQuery} 
          disabled={loading || !query.trim()}
          className="query-btn"
        >
          {loading ? 'Searching...' : 'Ask'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {result && (
        <div className="result-section">
          {/* Answer */}
          <div className="answer-panel">
            <h3>Answer</h3>
            <div 
              className="answer-text" 
              dangerouslySetInnerHTML={{
                __html: result.answer
                  .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                  .replace(/\n/g, '<br />')
              }}
            />
            
            <div className="metadata">
              <span className={`confidence confidence-${result.confidence}`}>
                Confidence: {result.confidence.toUpperCase()}
              </span>
              <span className="timing-simple">
                {result.num_sources} chunks | {result.token_stats?.total_tokens || 0} tokens
              </span>
              <span className="cost-badge">
                ${(result.estimated_cost_usd || 0).toFixed(6)}
              </span>
            </div>
          </div>

          {/* Sources */}
          {result.sources && result.sources.length > 0 && (
            <div className="sources-panel">
              <h3>Sources</h3>
              {result.sources.map((source) => (
                <div key={source.citation_id} className="source-item">
                  <div className="source-header">
                    <span className="citation-badge">[{source.citation_id}]</span>
                    <span className="source-name">{source.source}</span>
                    <span className="source-score">
                      Score: {(source.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="source-text">{source.text}</div>
                </div>
              ))}
            </div>
          )}

          {/* Statistics */}
          {result.token_stats && (
            <div className="stats-panel">
              <h3>Statistics</h3>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-label">Tokens Used:</span>
                  <span className="stat-value">{result.token_stats.total_tokens}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Estimated Cost:</span>
                  <span className="stat-value">${result.estimated_cost_usd.toFixed(6)}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Retrieved:</span>
                  <span className="stat-value">{result.retrieval_stats?.initial_retrieved || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Used (Reranked):</span>
                  <span className="stat-value">{result.retrieval_stats?.after_reranking || 0}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default QueryInterface;
