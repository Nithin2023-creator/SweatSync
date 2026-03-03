import React, { useState, useEffect, useCallback } from 'react';
import ChatWindow from './components/ChatWindow';
import DynamicInputBar from './components/DynamicInputBar';
import ProfileComplete from './components/ProfileComplete';
import './App.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);       // { role, content }
  const [isLoading, setIsLoading] = useState(false);
  const [completedSho, setCompletedSho] = useState(null);
  const [inputType, setInputType] = useState('text');
  const [suggestedOptions, setSuggestedOptions] = useState([]);
  const [conversationHistory, setConversationHistory] = useState([]); // sent to API

  // Kick off the conversation with the AI greeting
  useEffect(() => {
    const startConversation = async () => {
      setIsLoading(true);
      try {
        const res = await fetch(`${API_BASE}/api/chat/start`);
        if (!res.ok) throw new Error('Failed to start chat');
        const data = await res.json();

        const aiMsg = { role: 'assistant', content: data.reply };
        setMessages([aiMsg]);
        setConversationHistory([aiMsg]);
        setInputType(data.input_type || 'text');
        setSuggestedOptions(data.suggested_options || []);
      } catch (err) {
        console.error('Start error:', err);
        setMessages([{
          role: 'system',
          content: 'Failed to connect to the server. Please ensure the API is running.'
        }]);
      } finally {
        setIsLoading(false);
      }
    };

    startConversation();
  }, []);

  const handleSend = useCallback(async (text) => {
    if (!text.trim() || isLoading) return;

    const userMsg = { role: 'user', content: text };

    // Optimistic update
    setMessages(prev => [...prev, userMsg]);
    const updatedHistory = [...conversationHistory, userMsg];
    setConversationHistory(updatedHistory);
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: updatedHistory }),
      });

      if (!res.ok) throw new Error('Chat request failed');
      const data = await res.json();

      // Update UI instructions from agent
      setInputType(data.input_type || 'text');
      setSuggestedOptions(data.suggested_options || []);

      // ===== JSON INTERCEPTOR =====
      if (data.is_complete && data.sho) {
        if (data.reply && data.reply.trim()) {
          const aiMsg = { role: 'assistant', content: data.reply };
          setMessages(prev => [...prev, aiMsg]);
        }

        const systemMsg = {
          role: 'system',
          content: 'Profile complete! Handing your data over to The Guardian for clinical safety review...'
        };
        setMessages(prev => [...prev, systemMsg]);

        setTimeout(() => {
          setCompletedSho(data.sho);
        }, 1500);

        return;
      }

      // Normal conversation turn
      const aiMsg = { role: 'assistant', content: data.reply };
      setMessages(prev => [...prev, aiMsg]);
      setConversationHistory(prev => [...prev, aiMsg]);

    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Connection error. Please check the API server and try again.'
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [conversationHistory, isLoading]);

  if (completedSho) {
    return <ProfileComplete sho={completedSho} />;
  }

  return (
    <div className="app">
      <ChatWindow messages={messages} isLoading={isLoading} />
      <DynamicInputBar
        inputType={inputType}
        suggestedOptions={suggestedOptions}
        onSend={handleSend}
        disabled={isLoading}
      />
    </div>
  );
}

export default App;
