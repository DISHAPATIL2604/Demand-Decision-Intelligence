import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import api from '../../services/api';
import '../../styles/main.css';

export default function AssistantPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchSuggestions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchSuggestions = async () => {
    try {
      const data = await api.getChatSuggestions();
      setSuggestions(data.suggestions);
    } catch (err) {
      console.error('Failed to load suggestions:', err);
    }
  };

  const handleSubmit = async (e, customText = null) => {
    if (e) e.preventDefault();
    const text = customText || input;
    if (!text.trim() || isLoading) return;

    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      // Use history excluding the very last one we just added to state (it might not have updated yet)
      const currentHistory = messages.map(m => ({ role: m.role, content: m.content }));
      const response = await api.sendChatMessage(text, currentHistory);
      
      const botMsg = { 
        role: 'assistant', 
        content: response.reply,
        citations: response.citations
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setError(err.message || 'Failed to get a response from the assistant');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessageContent = (content) => {
    // Simple markdown renderer for bold and lists
    let html = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>')
      .replace(/```text<br\/>([\s\S]*?)```/g, '<pre style="background: #1f2937; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 0.85em; margin-top: 10px;">$1</pre>');
    
    return <div dangerouslySetInnerHTML={{ __html: html }} />;
  };

  return (
    <div style={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
          <Sparkles style={{ color: 'var(--accent-primary)' }} />
          AI Decision Assistant
        </h2>
        <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>
          Natural language Q&A across your demand, inventory, and anomaly data.
        </p>
      </div>

      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0 }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {messages.length === 0 && (
            <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-muted)', maxWidth: 400 }}>
              <Bot size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
              <h3>How can I help you today?</h3>
              <p style={{ fontSize: '0.9rem' }}>Ask about stockout risks, demand forecasts, anomalies, or general sales performance.</p>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '2rem' }}>
                {suggestions.map((sug, idx) => (
                  <button 
                    key={idx}
                    onClick={() => handleSubmit(null, sug)}
                    style={{ 
                      background: 'var(--bg-secondary)', 
                      border: '1px solid var(--border-color)',
                      padding: '0.75rem 1rem',
                      borderRadius: '0.5rem',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontSize: '0.9rem',
                      transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
                    onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} style={{ 
              display: 'flex', 
              gap: '1rem',
              alignItems: 'flex-start',
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
            }}>
              <div style={{ 
                width: 36, height: 36, borderRadius: '50%', 
                background: msg.role === 'user' ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0
              }}>
                {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
              </div>
              
              <div style={{ 
                maxWidth: '75%', 
                background: msg.role === 'user' ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                padding: '1rem',
                borderRadius: '0.75rem',
                borderTopRightRadius: msg.role === 'user' ? 0 : '0.75rem',
                borderTopLeftRadius: msg.role === 'assistant' ? 0 : '0.75rem',
                boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
              }}>
                {renderMessageContent(msg.content)}
                
                {msg.citations && msg.citations.length > 0 && (
                  <div style={{ 
                    marginTop: '1rem', 
                    paddingTop: '0.75rem', 
                    borderTop: '1px solid rgba(255,255,255,0.1)',
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)'
                  }}>
                    <strong>Sources:</strong> {msg.citations.join(', ')}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
              <div style={{ 
                width: 36, height: 36, borderRadius: '50%', 
                background: 'var(--bg-tertiary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <Bot size={20} />
              </div>
              <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '0.75rem', borderTopLeftRadius: 0 }}>
                <Loader2 size={20} className="spinner" style={{ animation: 'spin 1s linear infinite' }} />
              </div>
            </div>
          )}
          
          {error && (
            <div style={{ 
              margin: '0 auto', 
              background: 'rgba(244, 63, 94, 0.1)', 
              border: '1px solid var(--accent-rose)',
              color: 'var(--accent-rose)',
              padding: '0.75rem 1rem',
              borderRadius: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.9rem'
            }}>
              <AlertCircle size={18} />
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', background: 'var(--bg-primary)' }}>
          <form onSubmit={(e) => handleSubmit(e)} style={{ display: 'flex', gap: '0.75rem' }}>
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about your demand, inventory, or anomalies..."
              style={{ 
                flex: 1, 
                background: 'var(--bg-secondary)', 
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                padding: '0.75rem 1rem',
                borderRadius: '0.5rem',
                outline: 'none',
                fontSize: '0.95rem'
              }}
              disabled={isLoading}
            />
            <button 
              type="submit"
              disabled={isLoading || !input.trim()}
              style={{
                background: 'var(--accent-primary)',
                color: 'white',
                border: 'none',
                padding: '0 1.25rem',
                borderRadius: '0.5rem',
                cursor: (isLoading || !input.trim()) ? 'not-allowed' : 'pointer',
                opacity: (isLoading || !input.trim()) ? 0.7 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'opacity 0.2s'
              }}
            >
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>
      
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
