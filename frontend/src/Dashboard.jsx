import React, { useState, useEffect, useRef } from 'react';
import './Dashboard.css';

const sampleMessages = [
  {
    timestamp: "2026-08-04T09:12:00Z",
    channel: "telegram",
    query: "How do I reset my password?",
    reply: "You can reset it from Settings > Account > Reset Password.",
  },
  {
    timestamp: "2026-08-04T09:20:00Z",
    channel: "discord",
    query: "What are your support hours?",
    reply: "Our team is available 9am–6pm IST, Monday to Friday.",
  },
];

function Dashboard() {
  const [activeTab, setActiveTab] = useState('analytics');
  const [messages, setMessages] = useState([]);
  
  // Chat state
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([
    { sender: 'ai', text: 'Hello! How can I help you with your onboarding or queries today?' }
  ]);

  const messagesEndRef = useRef(null);

  // Fallback to sampleMessages if database analytics is empty
  const displayMessages = messages.length > 0 ? messages : sampleMessages;

  const channelCounts = displayMessages.reduce((acc, m) => {
    acc[m.channel] = (acc[m.channel] || 0) + 1;
    return acc;
  }, {});

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics');
      if (res.ok) {
        const data = await res.json();
        if (data && data.messages && data.messages.length > 0) {
          // Sort descending by timestamp so latest messages are first in log
          const sorted = [...data.messages].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
          setMessages(sorted);
        }
      }
    } catch (err) {
      console.error("Error fetching analytics:", err);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 5000);
    return () => clearInterval(interval);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const queryText = chatInput.trim();
    if (!queryText) return;

    // Add user message to chat window
    const newChatMessages = [...chatMessages, { sender: 'user', text: queryText }];
    setChatMessages(newChatMessages);
    setChatInput('');

    // Add typing placeholder
    setChatMessages((prev) => [...prev, { sender: 'ai', text: 'Typing...', isLoading: true }]);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: queryText }),
      });

      if (response.ok) {
        const data = await response.json();
        setChatMessages((prev) => {
          const filtered = prev.filter(msg => !msg.isLoading);
          return [...filtered, { sender: 'ai', text: data.reply || "No reply received from agent." }];
        });
      } else {
        throw new Error('API server returned error');
      }
    } catch (err) {
      console.error("Error communicating with AI agent:", err);
      setChatMessages((prev) => {
        const filtered = prev.filter(msg => !msg.isLoading);
        return [...filtered, { sender: 'ai', text: 'Connection error. Please check if the backend is running.' }];
      });
    }

    // Refresh dashboard messages log
    fetchAnalytics();
  };

  return (
    <div className="app-container">
      {/* Top Heading */}
      <header className="app-header">
        <h1>CASPIAN AI AGENT HACKATHON</h1>
      </header>

      {/* Navigation Bar */}
      <nav className="navbar">
        <button 
          className={`nav-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          ANALYTICS
        </button>
        <button 
          className={`nav-btn ${activeTab === 'chatbox' ? 'active' : ''}`}
          onClick={() => setActiveTab('chatbox')}
        >
          CHATBOX
        </button>
      </nav>

      {/* Main Content Area */}
      <main className="content-container">
        {activeTab === 'analytics' ? (
          <div className="dashboard-content">
            <div className="dashboard-header">
              <h2>Caspian Agent Dashboard</h2>
              <p className="subtitle">Live view of onboarding &amp; FAQ conversations</p>
            </div>

            <section className="stats-row">
              {Object.entries(channelCounts).map(([channel, count]) => (
                <div className="stat-card" key={channel}>
                  <span className="stat-count">{count}</span>
                  <span className="stat-label">{channel}</span>
                </div>
              ))}
              <div className="stat-card">
                <span className="stat-count">{displayMessages.length}</span>
                <span className="stat-label">total messages</span>
              </div>
            </section>

            <section className="message-log">
              <h3>Recent Messages</h3>
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Channel</th>
                      <th>Query</th>
                      <th>Reply</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayMessages.map((m, i) => (
                      <tr key={i}>
                        <td>{new Date(m.timestamp).toLocaleString()}</td>
                        <td>
                          <span className={`channel-badge channel-${m.channel}`}>
                            {m.channel}
                          </span>
                        </td>
                        <td>{m.query}</td>
                        <td>{m.reply}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        ) : (
          <div className="chatbox-section">
            <h2>AI Chat Interface</h2>
            <div className="chat-window">
              <div className="chat-messages">
                {chatMessages.map((msg, index) => (
                  <div key={index} className={`message ${msg.sender}`}>
                    <span>{msg.text}</span>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
              <form className="chat-input-area" onSubmit={handleSendMessage}>
                <input 
                  type="text" 
                  placeholder="Type a message..." 
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                />
                <button type="submit">Send</button>
              </form>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>BY - <span>SIRJAN MURMU</span></p>
      </footer>
    </div>
  );
}

export default Dashboard;