import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  User,
  Send,
  Sparkles,
  RefreshCw,
  Trash2,
  Boxes,
  AlertTriangle,
  TrendingUp,
  LineChart,
  ShieldCheck,
  ChevronRight,
  Database,
  ArrowUpRight
} from 'lucide-react';
import api from '../../services/api';

const QUICK_PROMPTS = [
  "Which products are at risk of stockout next week?",
  "Show top moving products in Delhi",
  "Summarize recent demand anomalies",
  "What is the recommended reorder quantity for SKU 19512?"
];

export default function AssistantPage() {
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    // Initial welcome message
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `### 🤖 Welcome to DemandIQ AI Decision Assistant

I am grounded directly in your **PostgreSQL production database**, analyzing live transactions across **32,226 product master SKUs**, holdout demand forecasts, safety stocks, and detected anomalies.

**How can I assist your supply chain decisions today?**
- Inquire about stockout risks and reorder quantities across Delhi, Mumbai, Bengaluru, and HR-NCR hubs.
- Investigate anomalous demand spikes or stockout drops.
- Review multi-model forecast projections.`,
        citations: []
      }
    ]);
  }, []);

  const handleSendMessage = async (textToSend) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || loading) return;

    const userMsgId = 'user-' + Date.now();
    const newMessages = [
      ...messages,
      { id: userMsgId, role: 'user', content: query }
    ];
    setMessages(newMessages);
    setInputQuery('');
    setLoading(true);

    try {
      const payload = {
        message: query,
        session_id: sessionId
      };
      const res = await api.post('/chat/message', payload);

      if (res.data) {
        if (res.data.session_id) {
          setSessionId(res.data.session_id);
        }

        setMessages((prev) => [
          ...prev,
          {
            id: 'bot-' + Date.now(),
            role: 'assistant',
            content: res.data.message,
            citations: res.data.citations || [],
            intent: res.data.intent
          }
        ]);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: 'error-' + Date.now(),
          role: 'assistant',
          content: '⚠️ Failed to connect to the Decision Assistant backend. Please verify that the API server is operational and try again.',
          citations: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = async () => {
    if (sessionId) {
      try {
        await api.delete(`/chat/session/${sessionId}`);
      } catch (e) {
        // ignore
      }
    }
    setSessionId(null);
    setMessages([
      {
        id: 'reset',
        role: 'assistant',
        content: 'Session cleared. Ask me any question regarding your inventory, demand trends, or forecasting models.',
        citations: []
      }
    ]);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Helper to render markdown-like text
  const formatMarkdown = (text) => {
    if (!text) return null;
    const lines = text.split('\n');

    return lines.map((line, idx) => {
      // Header 3
      if (line.startsWith('### ')) {
        return (
          <h3 key={idx} style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.8rem', marginBottom: '0.4rem' }}>
            {line.replace('### ', '')}
          </h3>
        );
      }
      // Bullet
      if (line.startsWith('- ')) {
        const content = line.substring(2);
        return (
          <li key={idx} style={{ marginLeft: '1.2rem', marginBottom: '0.3rem', color: 'var(--text-secondary)' }}>
            {renderInlineFormatting(content)}
          </li>
        );
      }
      if (line.trim() === '') {
        return <div key={idx} style={{ height: '0.5rem' }} />;
      }
      return (
        <p key={idx} style={{ marginBottom: '0.4rem', color: 'var(--text-secondary)' }}>
          {renderInlineFormatting(line)}
        </p>
      );
    });
  };

  // Inline bold/italic renderer
  const renderInlineFormatting = (text) => {
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} style={{ color: '#fff', fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={i} style={{ color: 'var(--accent-cyan)' }}>{part.slice(1, -1)}</em>;
      }
      return part;
    });
  };

  return (
    <div style={{ maxWidth: '1300px', margin: '0 auto', height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      {/* Top Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Bot color="var(--accent-primary)" size={28} />
            AI Decision Assistant
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.2rem' }}>
            RAG-grounded natural language Q&A across live sales, forecasts, and inventory optimization policies.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.35rem 0.75rem', borderRadius: '999px', backgroundColor: 'rgba(16, 185, 129, 0.12)', border: '1px solid var(--accent-emerald)', color: 'var(--accent-emerald)', fontSize: '0.75rem', fontWeight: 600 }}>
            <Database size={13} />
            PostgreSQL Live Grounded
          </div>

          <button
            onClick={handleClearChat}
            className="btn"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              backgroundColor: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-strong)',
              color: 'var(--text-muted)',
              fontSize: '0.8rem',
              padding: '0.45rem 0.85rem',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
            title="Clear Chat Session"
          >
            <Trash2 size={14} />
            Clear Session
          </button>
        </div>
      </div>

      {/* Quick Action Prompt Chips */}
      <div style={{ display: 'flex', gap: '0.6rem', overflowX: 'auto', paddingBottom: '0.75rem', marginBottom: '0.5rem' }}>
        {QUICK_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(prompt)}
            disabled={loading}
            style={{
              padding: '0.4rem 0.85rem',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-strong)',
              borderRadius: '20px',
              color: 'var(--text-secondary)',
              fontSize: '0.8rem',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              transition: 'all 0.15s ease'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-primary)';
              e.currentTarget.style.color = '#fff';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-strong)';
              e.currentTarget.style.color = 'var(--text-secondary)';
            }}
          >
            <Sparkles size={12} color="var(--accent-amber)" />
            {prompt}
          </button>
        ))}
      </div>

      {/* Message Stream Area */}
      <div
        className="card"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)'
        }}
      >
        {messages.map((m) => {
          const isUser = m.role === 'user';

          return (
            <div
              key={m.id}
              style={{
                display: 'flex',
                gap: '0.85rem',
                alignItems: 'flex-start',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                maxWidth: isUser ? '75%' : '90%',
              }}
            >
              {!isUser && (
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    border: '1px solid var(--accent-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px'
                  }}
                >
                  <Bot size={18} color="var(--accent-primary)" />
                </div>
              )}

              <div style={{ flex: 1 }}>
                <div
                  style={{
                    padding: '1rem 1.25rem',
                    borderRadius: isUser ? '16px 16px 4px 16px' : '4px 16px 16px 16px',
                    backgroundColor: isUser ? 'var(--accent-primary)' : 'var(--bg-surface-elevated)',
                    color: isUser ? '#fff' : 'var(--text-primary)',
                    border: isUser ? 'none' : '1px solid var(--border-strong)',
                    fontSize: '0.9rem',
                    lineHeight: 1.6,
                    boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                  }}
                >
                  {isUser ? m.content : formatMarkdown(m.content)}
                </div>

                {/* Grounded Citation Cards */}
                {!isUser && m.citations && m.citations.length > 0 && (
                  <div style={{ marginTop: '0.85rem' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <Database size={12} color="var(--accent-cyan)" />
                      Cited Database Records ({m.citations.length})
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '0.6rem' }}>
                      {m.citations.map((c, cIdx) => (
                        <div
                          key={cIdx}
                          style={{
                            padding: '0.75rem',
                            backgroundColor: 'rgba(255, 255, 255, 0.03)',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: '8px',
                            fontSize: '0.8rem'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.25rem' }}>
                            <span style={{ fontWeight: 600, color: '#fff' }}>
                              {c.product_name ? `${c.product_name.slice(0, 24)}...` : `SKU #${c.product_id}`}
                            </span>
                            {c.city && (
                              <span style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)', backgroundColor: 'rgba(6, 182, 212, 0.1)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                                {c.city}
                              </span>
                            )}
                          </div>

                          {c.type === 'inventory' && (
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                              <div>Current Stock: <strong style={{ color: '#fff' }}>{Math.round(c.current_stock).toLocaleString()}</strong></div>
                              <div>Recommended PO: <strong style={{ color: 'var(--accent-rose)' }}>{Math.round(c.recommended_order_qty).toLocaleString()}</strong></div>
                              <div style={{ marginTop: '0.2rem' }}>
                                <span style={{
                                  padding: '0.1rem 0.4rem',
                                  borderRadius: '4px',
                                  fontSize: '0.68rem',
                                  fontWeight: 700,
                                  backgroundColor: c.risk_status === 'CRITICAL_STOCKOUT' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                                  color: c.risk_status === 'CRITICAL_STOCKOUT' ? 'var(--accent-rose)' : 'var(--accent-amber)'
                                }}>
                                  {c.risk_status}
                                </span>
                              </div>
                            </div>
                          )}

                          {c.type === 'anomaly' && (
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                              <div>Actual: <strong style={{ color: '#fff' }}>{Math.round(c.actual).toLocaleString()}</strong> vs Exp: {Math.round(c.expected).toLocaleString()}</div>
                              <div style={{ color: 'var(--accent-amber)', marginTop: '0.2rem' }}>{c.anomaly_type} ({c.severity})</div>
                              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Date: {c.date}</div>
                            </div>
                          )}

                          {c.type === 'forecast' && (
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                              <div>Forecast: <strong style={{ color: 'var(--accent-cyan)' }}>{Math.round(c.predicted).toLocaleString()} units</strong></div>
                              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>95% CI: {c.bounds}</div>
                              <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Model: {c.model}</div>
                            </div>
                          )}

                          {c.type === 'sales' && (
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                              <div>14-Day Demand: <strong style={{ color: '#fff' }}>{Math.round(c.total_quantity).toLocaleString()} units</strong></div>
                              <div>Gross Revenue: <strong style={{ color: 'var(--accent-emerald)' }}>₹{Math.round(c.revenue_inr).toLocaleString()}</strong></div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {isUser && (
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-strong)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px'
                  }}
                >
                  <User size={18} color="#fff" />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div style={{ display: 'flex', gap: '0.85rem', alignItems: 'center' }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: '50%',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                border: '1px solid var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              <Bot size={18} color="var(--accent-primary)" />
            </div>
            <div
              style={{
                padding: '0.75rem 1.25rem',
                borderRadius: '4px 16px 16px 16px',
                backgroundColor: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-strong)',
                color: 'var(--text-secondary)',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              <RefreshCw size={14} className="animate-spin" />
              Retrieving live facts & computing policy recommendations...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Message Input Box */}
      <div style={{ marginTop: '0.75rem', position: 'relative' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            placeholder="Ask about stockout risks, SKU recommendations, forecasts, or anomaly alerts..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            style={{
              flex: 1,
              padding: '0.85rem 1.25rem',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-strong)',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '0.925rem',
              outline: 'none',
            }}
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputQuery.trim() || loading}
            className="btn btn-primary"
            style={{
              padding: '0.85rem 1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontWeight: 600,
              cursor: !inputQuery.trim() || loading ? 'not-allowed' : 'pointer'
            }}
          >
            <Send size={16} />
            Ask
          </button>
        </div>
      </div>
    </div>
  );
}
