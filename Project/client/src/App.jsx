import React, { useState, useCallback, useEffect } from 'react';
import SplashScreen from './components/SplashScreen';
import OnboardingCard from './components/OnboardingCard';
import PipelineProgress from './components/PipelineProgress';
import PlanView from './components/PlanView';
import Login from './components/Login';
import AppBackground from './components/AppBackground';
import './App.css';

const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

function App() {
  const [authToken, setAuthToken] = useState(localStorage.getItem('sweatsync_token'));
  const [showSplash, setShowSplash] = useState(true);
  const [isAppLoading, setIsAppLoading] = useState(true); // Initial auth/startup
  const [isLoading, setIsLoading] = useState(false); // In-session actions
  const [completedSho, setCompletedSho] = useState(null);
  const [finalPlan, setFinalPlan] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [provider, setProvider] = useState('groq'); // 'groq' | 'ollama'

  // Fetch existing user data on load
  useEffect(() => {
    const fetchUserData = async () => {
      if (!authToken) {
        setIsAppLoading(false);
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/user/data`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (res.ok) {
          const data = await res.json();
          if (data.sho) {
            setCompletedSho(data.sho);
            setShowSplash(false);
          }
          if (data.plan) {
            setFinalPlan(data.plan);
          }
          if (data.session_id) {
            setSessionId(data.session_id);
          }
        } else if (res.status === 401) {
          setAuthToken(null);
          localStorage.removeItem('sweatsync_token');
        }
      } catch (err) {
        console.error('Failed to fetch user data:', err);
      } finally {
        setIsAppLoading(false);
      }
    };
    fetchUserData();
  }, [authToken]);

  const [currentQuestion, setCurrentQuestion] = useState('');
  const [inputType, setInputType] = useState('text');
  const [suggestedOptions, setSuggestedOptions] = useState([]);
  const [conversationHistory, setConversationHistory] = useState([]);

  const [stepIndex, setStepIndex] = useState(0);

  // Start conversation when user taps "Get Started"
  const startConversation = async (currentProvider) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat/start?provider=${currentProvider || provider}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (!res.ok) {
        if (res.status === 401) {
          setAuthToken(null);
          localStorage.removeItem('sweatsync_token');
          return;
        }
        throw new Error('Failed to start chat');
      }
      const data = await res.json();

      const aiMsg = { role: 'assistant', content: data.reply };
      setConversationHistory([aiMsg]);
      setCurrentQuestion(data.reply);
      setInputType(data.input_type || 'text');
      setSuggestedOptions(data.suggested_options || []);
      setStepIndex(1);
    } catch (err) {
      console.error('Start error:', err);
      setCurrentQuestion('Failed to connect to the server. Please ensure the API is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = useCallback(async (text) => {
    if (!text.trim() || isLoading) return;

    const userMsg = { role: 'user', content: text };
    const updatedHistory = [...conversationHistory, userMsg];
    setConversationHistory(updatedHistory);
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          messages: updatedHistory,
          provider: provider
        }),
      });

      if (!res.ok) throw new Error('Chat request failed');
      const data = await res.json();

      // Update UI instructions from agent
      let newType = data.input_type || 'text';
      let newOptions = data.suggested_options || [];

      // Defensive safety net
      if (!data.is_complete && newOptions.length === 0 && newType !== 'text' && newType !== 'numeric') {
        newType = 'text';
      }

      // ===== ONBOARDING COMPLETE → PIPELINE =====
      if (data.is_complete && data.sho) {
        setTimeout(() => {
          setCompletedSho(data.sho);
        }, 800);
        return;
      }

      // Normal conversation turn — update card
      const aiMsg = { role: 'assistant', content: data.reply };
      setConversationHistory((prev) => [...prev, aiMsg]);
      setCurrentQuestion(data.reply);
      setInputType(newType);
      setSuggestedOptions(newOptions);
      setStepIndex((prev) => prev + 1);

    } catch (err) {
      console.error('Chat error:', err);
      setCurrentQuestion('Connection error. Please check the API server and try again.');
    } finally {
      setIsLoading(false);
    }
  }, [conversationHistory, isLoading, provider]);

  const handleStart = () => {
    setShowSplash(false);
    startConversation(provider);
  };

  const toggleProvider = () => {
    setProvider(prev => prev === 'groq' ? 'ollama' : 'groq');
  };

  const handleLogout = () => {
    setAuthToken(null);
    localStorage.removeItem('sweatsync_token');

    // Reset session-specific state
    setCompletedSho(null);
    setFinalPlan(null);
    setSessionId(null);
    setConversationHistory([]);
    setCurrentQuestion('');
    setStepIndex(0);
    setShowSplash(true);
  };

  // --- Render Flow ---
  return (
    <>
      <AppBackground />
      {/* Global Top Actions for Authenticated Users */}
      {isAppLoading && !!authToken ? (
        <div className="app">
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-secondary)' }}>
            Authenticating...
          </div>
        </div>
      ) : !authToken ? (
        <Login onLogin={(token) => {
          setAuthToken(token);
          setIsAppLoading(true);
        }} />
      ) : finalPlan ? (
        <div className="app">
          <PlanView 
            plan={finalPlan} 
            onUpdate={setFinalPlan} 
            sessionId={sessionId} 
            provider={provider} 
            authToken={authToken} 
            onLogout={handleLogout}
          />
        </div>
      ) : (
        <>
          {authToken && (
            <div className="top-actions">
              <button className="logout-btn" onClick={handleLogout}>Logout</button>
            </div>
          )}
          {completedSho ? (
            <PipelineProgress
              sho={completedSho}
              provider={provider}
              authToken={authToken}
              onComplete={(plan, sid) => {
                setSessionId(sid);
                setFinalPlan(plan);
              }}
            />
          ) : showSplash ? (
            <SplashScreen onStart={handleStart} provider={provider} onToggleProvider={toggleProvider} />
          ) : (
            <div className="app">
              <OnboardingCard
                question={currentQuestion}
                inputType={inputType}
                suggestedOptions={suggestedOptions}
                onAnswer={handleSend}
                isLoading={isLoading}
                stepIndex={stepIndex}
                totalSteps={10}
              />
            </div>
          )}
        </>
      )}
    </>
  );
}

export default App;
