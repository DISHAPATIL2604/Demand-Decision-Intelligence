import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  AlertCircle,
  Loader2,
  RefreshCw,
  Database,
  FileSpreadsheet,
  HelpCircle,
  TrendingUp,
  Boxes,
  Activity,
  DollarSign,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getChatSuggestions, sendChatMessage } from '../../services/api';
import '../../styles/main.css';
import './AssistantPage.css';

const INTENT_CONFIG = {
  inventory: { label: 'Inventory Optimization', color: '#f59e0b', icon: Boxes },
  anomaly:   { label: 'Demand Anomaly',        color: '#f43f5e', icon: Activity },
  forecast:  { label: 'Sales Forecast',        color: '#3b82f6', icon: TrendingUp },
  business:  { label: 'Business Performance',  color: '#10b981', icon: DollarSign },
  demand:    { label: 'Demand Analytics',      color: '#8b5cf6', icon: Sparkles },
};

export default function AssistantPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const DEFAULT_SUGGESTIONS = [
    "Which products generate the most revenue?",
    "Which products should I restock?",
    "Why should I restock them?",
    "What is the expected demand next week?",
    "Are there any demand anomalies?",
    "Kaunsa product sabse zyada revenue generate karta hai?",
    "मला कोणते products restock करायचे आहेत?",
    "What data did you use?",
  ];

  const [suggestions, setSuggestions] = useState(DEFAULT_SUGGESTIONS);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchSuggestions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const fetchSuggestions = async () => {
    try {
      const data = await getChatSuggestions();
      if (data?.suggestions && data.suggestions.length > 0) {
        setSuggestions(data.suggestions);
      }
    } catch (err) {
      console.warn('Using default starter suggestions:', err.message);
    }
  };

  const handleSubmit = async (e, customText = null) => {
    if (e) e.preventDefault();
    const text = customText || input;
    if (!text.trim() || isLoading) return;

    const userMsg = { role: 'user', content: text };
    const historyForApi = messages.map(m => ({ role: m.role, content: m.content }));

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(text, historyForApi);
      const botMsg = {
        role:      'assistant',
        content:   response.reply,
        citations: response.citations || [],
        intent:    response.intent,
        evidence:  response.evidence || [],
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setError(err.message || 'Assistant encountered a communication error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setError(null);
    fetchSuggestions();
  };

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - var(--header-height))', padding: '1.25rem 2rem 1.5rem' }}>
      {/* Header */}
      <div className="assistant-header">
        <div className="assistant-header-left">
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 10px rgba(59, 130, 246, 0.3)',
            }}
          >
            <Sparkles size={20} style={{ color: '#fff' }} />
          </div>
          <div>
            <h2 className="assistant-title">AI Decision Intelligence Copilot</h2>
            <p className="assistant-subtitle">
              Ask natural questions in English, Hindi, or Marathi grounded in audited database records and ML forecasts.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="data-status-bar" title="Connected to PostgreSQL & Analytics Reports">
            <span className="data-status-dot" />
            <Database size={12} />
            <span>PostgreSQL Evidence Engine</span>
          </div>

          {messages.length > 0 && (
            <button className="assistant-reset-btn" onClick={handleReset} title="Clear conversation">
              <RefreshCw size={14} /> New Query
            </button>
          )}
        </div>
      </div>

      {/* Main Chat Body Card */}
      <div className="assistant-body">
        {/* Messages feed */}
        <div className="assistant-messages">
          {messages.length === 0 && (
            <div className="assistant-welcome">
              <div className="assistant-welcome-icon">
                <Bot size={36} />
              </div>
              <h3>How can I assist your supply chain decisions?</h3>
              <p>
                Query sales performance, stockout risks, safety buffer calculations, or anomaly diagnostics.
              </p>

              {/* Suggestions Grid */}
              <div className="assistant-suggestions-grid">
                {suggestions.map((sug, idx) => (
                  <button
                    key={idx}
                    className="assistant-suggestion-card"
                    onClick={() => handleSubmit(null, sug)}
                  >
                    <span className="assistant-suggestion-text">{sug}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => {
            const intentMeta = INTENT_CONFIG[msg.intent];
            const IntentIcon = intentMeta?.icon;

            return (
              <div key={idx} className={`assistant-msg-row ${msg.role}`}>
                {/* Avatar */}
                <div className={`assistant-avatar ${msg.role}`}>
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>

                {/* Bubble */}
                <div className={`assistant-bubble ${msg.role}`}>
                  {/* Intent tag */}
                  {msg.role === 'assistant' && msg.intent && (
                    <div
                      className="assistant-intent-badge"
                      style={{
                        borderColor: intentMeta?.color ? `${intentMeta.color}40` : 'var(--border)',
                        background: intentMeta?.color ? `${intentMeta.color}15` : 'transparent',
                      }}
                    >
                      {IntentIcon && <IntentIcon size={12} style={{ color: intentMeta.color }} />}
                      <span style={{ color: intentMeta?.color || 'var(--text-secondary)' }}>
                        {intentMeta?.label || msg.intent.toUpperCase()}
                      </span>
                    </div>
                  )}

                  {/* Message content */}
                  <div className="assistant-bubble-content">
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          table: ({ node, ...props }) => (
                            <div className="assistant-table-wrap">
                              <table className="data-table" {...props} />
                            </div>
                          ),
                          code: ({ node, inline, ...props }) =>
                            inline ? (
                              <code className="assistant-inline-code" {...props} />
                            ) : (
                              <pre className="assistant-code-block">
                                <code {...props} />
                              </pre>
                            ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      <p className="assistant-user-text">{msg.content}</p>
                    )}
                  </div>

                  {/* Evidence records */}
                  {msg.evidence && msg.evidence.length > 0 && (
                    <details className="assistant-evidence">
                      <summary>
                        <Database size={13} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                        View Grounded Evidence ({msg.evidence.length} records retrieved)
                      </summary>
                      <div className="assistant-evidence-body">
                        {msg.evidence.slice(0, 5).map((ev, i) => (
                          <div key={i} className="assistant-evidence-card">
                            {Object.entries(ev)
                              .filter(([k]) => k !== 'source' && ev[k] !== null && ev[k] !== undefined)
                              .map(([k, v]) => (
                                <span key={k} className="assistant-ev-field">
                                  <span className="assistant-ev-key">{k.replace(/_/g, ' ')}:</span>{' '}
                                  <span className="assistant-ev-val">{String(v)}</span>
                                </span>
                              ))}
                            {ev.source && (
                              <span className="assistant-ev-source">
                                <FileSpreadsheet size={11} style={{ display: 'inline', marginRight: 3 }} />
                                Source: {ev.source}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </details>
                  )}

                  {/* Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="assistant-citations">
                      <span className="assistant-citations-label">Sources:</span>
                      {msg.citations.map((c, i) => (
                        <span key={i} className="assistant-citation-chip">
                          {c.includes('.csv') ? <FileSpreadsheet size={11} /> : <Database size={11} />}
                          <span>{c}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Loading bubble */}
          {isLoading && (
            <div className="assistant-msg-row assistant">
              <div className="assistant-avatar assistant"><Bot size={16} /></div>
              <div className="assistant-bubble assistant assistant-thinking">
                <Loader2 size={16} className="spin" />
                <span>Analyzing your data...</span>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="assistant-error-bar">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="assistant-input-area">
          <form onSubmit={handleSubmit} className="assistant-input-form">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about demand, sales, inventory or forecasts — English, Hindi, Marathi or Hinglish..."
              className="assistant-input"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="assistant-send-btn"
              title="Send message"
            >
              <Send size={18} />
            </button>
          </form>
          <p className="assistant-disclaimer">
            Decision responses are strictly grounded in PostgreSQL demand data, forecasting models, and inventory reports.
          </p>
        </div>
      </div>
    </div>
  );
}
