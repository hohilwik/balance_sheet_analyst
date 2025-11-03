// version with better styling
import React, { useState } from 'react';
import './Chat.css';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = { role: 'user', content: inputMessage, webSearch: useWebSearch };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          message: inputMessage,
          use_web_search: useWebSearch
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: data.response,
          webSearchUsed: data.web_search_used,
          sources: data.web_sources || [],
          timestamp: new Date().toLocaleTimeString()
        }]);
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `Error: ${data.error || 'Failed to get response'}`,
          isError: true
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Network error: Could not connect to server',
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      {/* Header with Web Search Toggle */}
      <div className="chat-header">
        <div className="header-content">
          <h2>Financial Analyst</h2>
          <div className="web-search-control">
            <div className="toggle-container">
              <label className="toggle-label">
                <div className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={useWebSearch}
                    onChange={(e) => setUseWebSearch(e.target.checked)}
                    className="toggle-checkbox"
                  />
                  <span className="toggle-slider"></span>
                </div>
                <span className="toggle-text">
                  {useWebSearch ? '🌐 Web Search ON' : '📊 Internal Data Only'}
                </span>
              </label>
            </div>
            <div className="toggle-description">
              {useWebSearch ? 
                "I'll search the web for current information" : 
                "Using your company's financial data only"}
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="messages-container">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role} ${msg.isError ? 'error' : ''}`}>
            <div className="message-header">
              <strong>{msg.role === 'user' ? 'You' : 'Financial Analyst'}</strong>
              {msg.role === 'user' && msg.webSearch && (
                <span className="web-search-indicator">🔍</span>
              )}
              {msg.timestamp && <span className="timestamp">{msg.timestamp}</span>}
            </div>
            <div className="message-content">{msg.content}</div>
            {msg.webSearchUsed && msg.sources && msg.sources.length > 0 && (
              <div className="web-sources">
                <div className="sources-label">Information Sources:</div>
                {msg.sources.map((source, i) => (
                  <a key={i} href={source} target="_blank" rel="noopener noreferrer" className="source-link">
                    {new URL(source).hostname}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="message assistant loading">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
                {useWebSearch && " Searching web..."}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-container">
        <div className="input-wrapper">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder={
              useWebSearch ? 
                "Ask about current market trends, news, or financial data..." : 
                "Ask about your company's financial data..."
            }
            disabled={isLoading}
          />
          <button 
            onClick={sendMessage} 
            disabled={!inputMessage.trim() || isLoading}
            className="send-button"
          >
            {isLoading ? '...' : 'Send'}
          </button>
        </div>
        <div className="input-hint">
          {useWebSearch ? 
            "Web search may take longer but provides current information" : 
            "Quick responses using your company's data"}
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;