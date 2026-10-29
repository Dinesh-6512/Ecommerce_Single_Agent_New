import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { askAgent } from '../api';
import { useAuth } from '../context/AuthContext';

export default function Chat() {
  const { isAuthenticated, token } = useAuth();
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: 'Hello! I am your store assistant. You can ask me anything about our products, prices, stock availability, or the items in your shopping cart.'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  if (!isAuthenticated) {
    return (
      <div className="auth-wrapper" id="chat-screen">
        <div className="info-card" style={{ maxWidth: '480px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>💬</div>
          <h2>Ask the Store</h2>
          <p>Please log in to chat with the store assistant about products, prices, stock, and your cart.</p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
            <Link to="/login" className="btn-primary" style={{ width: 'auto', textDecoration: 'none' }} id="chat-login-link">
              Login to Chat
            </Link>
            <Link to="/" className="btn-primary" style={{ width: 'auto', textDecoration: 'none', backgroundColor: '#64748b' }}>
              Browse Products
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const trimmed = inputMessage.trim();
    if (!trimmed || loading) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: trimmed
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setLoading(true);

    try {
      const data = await askAgent(token, trimmed);
      const reply = data.answer || 'I am sorry, but I could not find information on that in the store database.';
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          text: reply
        }
      ]);
    } catch (err) {
      let friendlyError = 'Sorry, I encountered an issue answering your question. Please try again.';
      const msg = (err.message || '').toLowerCase();

      if (msg.includes('rate limit') || msg.includes('temporarily unavailable')) {
        friendlyError = 'The AI assistant is temporarily busy with high request volume. Please wait a moment and try again.';
      } else if (msg.includes('not authenticated') || msg.includes('credentials')) {
        friendlyError = 'Your login session appears to have expired. Please log in again to continue.';
      } else if (msg.includes('groq api key') || msg.includes('not configured')) {
        friendlyError = 'The AI assistant is currently unavailable due to missing server configuration.';
      } else if (msg.includes('valid question') || msg.includes('too long')) {
        friendlyError = err.message || 'Please provide a clear question about store products, prices, stock, or your cart.';
      } else if (err.message) {
        friendlyError = err.message;
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          text: friendlyError,
          isError: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="chat-screen" className="chat-wrapper">
      <div className="page-header" style={{ marginBottom: '1.25rem' }}>
        <div>
          <h1 className="page-title">💬 Ask the Store</h1>
          <p className="page-subtitle">Chat with our AI assistant about products, prices, stock, and your cart</p>
        </div>
      </div>

      <div className="chat-card">
        <div className="chat-header">
          <div className="chat-header-title">
            <span>Store AI Assistant</span>
          </div>
          <span className="chat-badge">Live • Read-Only</span>
        </div>

        <div className="chat-messages" id="chat-messages-area">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat-message ${msg.sender}`}>
              <div
                className={`chat-bubble ${
                  msg.sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'
                } ${msg.isError ? 'chat-bubble-error' : ''}`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-thinking" id="chat-thinking-indicator">
              <span>💭 Thinking...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSendMessage} className="chat-input-form">
          <input
            type="text"
            className="chat-input"
            id="chat-input-field"
            placeholder="Ask about products, prices, stock, or your cart..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={loading}
            maxLength={1000}
          />
          <button
            type="submit"
            className="chat-send-btn"
            id="chat-send-btn"
            disabled={loading || !inputMessage.trim()}
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}
