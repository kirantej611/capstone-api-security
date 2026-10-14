'use client';

import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Bot, User } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<'quick' | 'ai'>('quick');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I am your AEGIS-AI Security Assistant. How can I help you analyze the threat landscape today?',
      timestamp: new Date()
    }
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const toggleChat = () => setIsOpen((open) => !open);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date()
    };

    if (mode === 'ai') {
      setInput('');
    }

    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch('/api/proxy/gateway/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: text })
      });
      
      const responseText = await response.text();
      let data: { reply?: unknown; detail?: unknown } = {};
      try {
        data = JSON.parse(responseText);
      } catch {
        const diagnostic = responseText.trim().slice(0, 300);
        throw new Error(
          response.ok
            ? 'Gateway returned an invalid response body.'
            : `Gateway returned HTTP ${response.status}${diagnostic ? `: ${diagnostic}` : ''}.`
        );
      }

      if (!response.ok) {
        const detail =
          typeof data.detail === 'string'
            ? `: ${data.detail}`
            : response.statusText
              ? `: ${response.statusText}`
              : '';
        throw new Error(`Gateway returned HTTP ${response.status}${detail}`);
      }
      if (typeof data.reply !== 'string' || !data.reply.trim()) {
        throw new Error('Gateway response did not include a reply.');
      }
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.reply,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: error instanceof Error
          ? `Could not get a SecOps response. ${error.message}`
          : 'Could not get a SecOps response due to an unknown error.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999 }}>
      {isOpen && (
        <div 
          style={{
            position: 'absolute',
            bottom: '72px',
            right: '0',
            width: '350px',
            height: '500px',
            backgroundColor: '#0a0a0a',
            border: '1px solid #333',
            borderRadius: '12px',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.8)',
            overflow: 'hidden'
          }}
        >
          {/* Header */}
          <div style={{
            padding: '16px',
            borderBottom: '1px solid #333',
            backgroundColor: '#111',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fff' }}>
              <Bot size={20} color="#00ff9d" />
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, fontFamily: 'Inter, sans-serif' }}>SecOps Assistant</h3>
            </div>
            <button 
              onClick={toggleChat}
              aria-label="Close SecOps Assistant"
              style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer', padding: 0 }}
            >
              <X size={20} />
            </button>
          </div>

          {/* Messages Area */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            fontFamily: 'Inter, sans-serif'
          }}>
            {messages.map((msg) => (
              <div 
                key={msg.id}
                style={{
                  display: 'flex',
                  flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                  gap: '8px',
                  alignItems: 'flex-start'
                }}
              >
                <div style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  backgroundColor: msg.role === 'user' ? '#333' : '#003320',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  {msg.role === 'user' ? <User size={16} color="#aaa" /> : <Bot size={16} color="#00ff9d" />}
                </div>
                <div style={{
                  maxWidth: '75%',
                  padding: '10px 14px',
                  borderRadius: '12px',
                  backgroundColor: msg.role === 'user' ? '#222' : '#11221c',
                  color: msg.role === 'user' ? '#eee' : '#00ff9d',
                  fontSize: '14px',
                  lineHeight: '1.4',
                  border: msg.role === 'user' ? '1px solid #333' : '1px solid #005530',
                  borderTopRightRadius: msg.role === 'user' ? '2px' : '12px',
                  borderTopLeftRadius: msg.role === 'user' ? '12px' : '2px',
                  wordBreak: 'break-word'
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Mode Toggle */}
          <div style={{ display: 'flex', borderBottom: '1px solid #333', backgroundColor: '#0a0a0a' }}>
            <button
              onClick={() => setMode('quick')}
              style={{
                flex: 1,
                padding: '12px',
                backgroundColor: mode === 'quick' ? '#111' : '#0a0a0a',
                color: mode === 'quick' ? '#00ff9d' : '#888',
                border: 'none',
                borderBottom: mode === 'quick' ? '2px solid #00ff9d' : '2px solid transparent',
                cursor: 'pointer',
                fontFamily: 'Inter, sans-serif',
                fontSize: '13px',
                fontWeight: 600
              }}
            >
              Quick Actions
            </button>
            <button
              onClick={() => setMode('ai')}
              style={{
                flex: 1,
                padding: '12px',
                backgroundColor: mode === 'ai' ? '#111' : '#0a0a0a',
                color: mode === 'ai' ? '#00ff9d' : '#888',
                border: 'none',
                borderBottom: mode === 'ai' ? '2px solid #00ff9d' : '2px solid transparent',
                cursor: 'pointer',
                fontFamily: 'Inter, sans-serif',
                fontSize: '13px',
                fontWeight: 600
              }}
            >
              Ask AI (LLM)
            </button>
          </div>

          {/* Action/Input Area */}
          {mode === 'quick' ? (
            <div style={{
              padding: '16px',
              backgroundColor: '#111',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#888', fontFamily: 'Inter, sans-serif' }}>Select an action:</p>
              {[
                'Check Firewall Status',
                'Show Recent Threats',
                'System Health & Uptime'
              ].map((option, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(option)}
                  style={{
                    backgroundColor: '#003320',
                    color: '#00ff9d',
                    border: '1px solid #005530',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '13px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                    fontFamily: 'Inter, sans-serif'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#00442a'}
                  onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#003320'}
                >
                  {option}
                </button>
              ))}
            </div>
          ) : (
            <div style={{
              padding: '16px',
              backgroundColor: '#111'
            }}>
              <form 
                onSubmit={(e) => { e.preventDefault(); handleSend(input); }}
                style={{ display: 'flex', gap: '8px' }}
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask the LLM anything..."
                  aria-label="Message for the SecOps Assistant"
                  style={{
                    flex: 1,
                    padding: '10px 14px',
                    borderRadius: '8px',
                    border: '1px solid #333',
                    backgroundColor: '#000',
                    color: '#fff',
                    fontSize: '14px',
                    fontFamily: 'Inter, sans-serif',
                    outline: 'none'
                  }}
                />
                <button
                  type="submit"
                  disabled={!input.trim()}
                  aria-label="Send message"
                  style={{
                    backgroundColor: input.trim() ? '#00ff9d' : '#333',
                    color: input.trim() ? '#000' : '#888',
                    border: 'none',
                    borderRadius: '8px',
                    width: '40px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: input.trim() ? 'pointer' : 'not-allowed',
                    transition: 'all 0.2s'
                  }}
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          )}
        </div>
      )}

      {/* Floating Button */}
      <button
        onClick={toggleChat}
        aria-label={isOpen ? 'Close SecOps Assistant' : 'Open SecOps Assistant'}
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: '#00ff9d',
          color: '#000',
          border: 'none',
          boxShadow: '0 4px 16px rgba(0, 255, 157, 0.4)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'transform 0.2s'
        }}
      >
        {isOpen ? <X size={28} /> : <MessageSquare size={28} />}
      </button>
    </div>
  );
}
