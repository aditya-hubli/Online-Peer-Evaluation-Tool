import { useState, useEffect, useRef } from 'react';
import { chatsAPI } from '../api';
import { MessageCircle, Send, Trash2, Users as UsersIcon, X } from 'lucide-react';
import './TeamChat.css';

function TeamChat({ teamId, teamName, user, onClose }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [showMembers, setShowMembers] = useState(false);
  const messagesEndRef = useRef(null);
  const pollingIntervalRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadMessages = async () => {
    try {
      const res = await chatsAPI.getMessages(teamId, user.id);
      setMessages(res.data.messages || []);
      scrollToBottom();
    } catch (error) {
      console.error('Failed to load messages:', error);
      if (error.response?.status !== 403) {
        alert('Failed to load messages');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadMembers = async () => {
    try {
      const res = await chatsAPI.getTeamMembers(teamId, user.id);
      setMembers(res.data.members || []);
    } catch (error) {
      console.error('Failed to load members:', error);
    }
  };

  useEffect(() => {
    loadMessages();
    loadMembers();

    // Poll for new messages every 3 seconds
    pollingIntervalRef.current = setInterval(() => {
      loadMessages();
    }, 3000);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [teamId, user.id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      const messageData = { message: newMessage };
      await chatsAPI.sendMessage(teamId, user.id, messageData);
      setNewMessage('');
      await loadMessages();
    } catch (error) {
      console.error('Failed to send message:', error);
      alert(error.response?.data?.detail || 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const handleDeleteMessage = async (messageId) => {
    if (!confirm('Are you sure you want to delete this message?')) return;

    try {
      await chatsAPI.deleteMessage(messageId, user.id);
      await loadMessages();
    } catch (error) {
      console.error('Failed to delete message:', error);
      alert(error.response?.data?.detail || 'Failed to delete message');
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  if (loading) {
    return (
      <div className="team-chat">
        <div className="chat-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <MessageCircle size={20} color="#4f46e5" />
            <h3>{teamName}</h3>
          </div>
          <button className="btn-icon" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        <div className="chat-body">
          <div className="loading">Loading messages...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="team-chat">
      <div className="chat-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MessageCircle size={20} color="#4f46e5" />
          <h3>{teamName}</h3>
          <span className="member-count">({members.length} members)</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            className="btn-icon" 
            onClick={() => setShowMembers(!showMembers)}
            title="View members"
          >
            <UsersIcon size={20} />
          </button>
          <button className="btn-icon" onClick={onClose} title="Close chat">
            <X size={20} />
          </button>
        </div>
      </div>

      {showMembers && (
        <div className="members-panel">
          <div className="members-header">
            <span style={{ fontWeight: '600' }}>Team Members</span>
            <button className="btn-text" onClick={() => setShowMembers(false)}>
              Hide
            </button>
          </div>
          <div className="members-list">
            {members.map((member) => (
              <div key={member.id} className="member-item">
                <div className="member-avatar">
                  {member.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="member-name">{member.name}</div>
                  <div className="member-email">{member.email}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="chat-body">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <MessageCircle size={48} color="#d1d5db" />
            <p>No messages yet</p>
            <p style={{ fontSize: '14px', color: '#9ca3af' }}>
              Start a conversation with your team!
            </p>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((msg) => (
              <div 
                key={msg.id} 
                className={`message ${msg.sender_id === user.id ? 'own-message' : ''}`}
              >
                <div className="message-avatar">
                  {msg.sender_name.charAt(0).toUpperCase()}
                </div>
                <div className="message-content">
                  <div className="message-header">
                    <span className="message-sender">
                      {msg.sender_id === user.id ? 'You' : msg.sender_name}
                    </span>
                    <span className="message-time">
                      {formatTimestamp(msg.created_at)}
                    </span>
                  </div>
                  <div className="message-text">{msg.message}</div>
                  {msg.sender_id === user.id && (
                    <button 
                      className="message-delete"
                      onClick={() => handleDeleteMessage(msg.id)}
                      title="Delete message"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <form className="chat-footer" onSubmit={handleSendMessage}>
        <input
          type="text"
          className="message-input"
          placeholder="Type a message..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          disabled={sending}
        />
        <button 
          type="submit" 
          className="btn-send"
          disabled={!newMessage.trim() || sending}
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}

export default TeamChat;
