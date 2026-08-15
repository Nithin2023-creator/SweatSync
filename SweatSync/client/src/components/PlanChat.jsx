import React, { useState, useRef, useEffect } from 'react';
import './PlanChat.css';

const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

function PlanChat({ context, pinnedContext, onClearPin, currentPlan, onPlanUpdate, sessionId, authToken, provider = 'groq' }) {
    const [prompt, setPrompt] = useState('');
    const [isSending, setIsSending] = useState(false);
    const [messages, setMessages] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const [isFocused, setIsFocused] = useState(false);
    const [replanPreview, setReplanPreview] = useState(null);
    const [pendingPlan, setPendingPlan] = useState(null);
    const inputRef = useRef(null);
    const containerRef = useRef(null);
    const threadRef = useRef(null);

    // Expansion logic
    const isExpanded = isFocused || (isOpen && messages.length > 0) || !!pinnedContext;

    // Determine effective context for API
    const effectiveContext = pinnedContext ? {
        level: pinnedContext.type,
        week_index: pinnedContext.weekIdx,
        day_key: pinnedContext.dayKey,
        exercise_index: pinnedContext.exerciseIdx
    } : context;

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (threadRef.current) {
            threadRef.current.scrollTop = threadRef.current.scrollHeight;
        }
    }, [messages, replanPreview]);

    // Open the thread when messages exist
    useEffect(() => {
        if (messages.length > 0) setIsOpen(true);
    }, [messages]);

    const handleSubmit = async (e) => {
        if (e) e.preventDefault();
        if (!prompt.trim() || isSending) return;

        const userMsg = { role: 'user', text: prompt };
        setMessages(prev => [...prev, userMsg]);
        setPrompt('');
        setIsSending(true);

        try {
            const res = await fetch(`${API_BASE}/api/plan/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    prompt: userMsg.text,
                    context: effectiveContext,
                    current_plan: currentPlan,
                    session_id: sessionId || null,
                    provider: provider
                })
            });

            if (!res.ok) {
                const errText = await res.text().catch(() => '');
                console.error(`Plan chat HTTP ${res.status}:`, errText);
                throw new Error(`Server error (${res.status})`);
            }
            const data = await res.json();

            // Check if this is a replan action — show confirmation
            if (data.action === 'replan' && data.preview) {
                setMessages(prev => [...prev, { role: 'ai', text: data.reply }]);
                setReplanPreview(data.preview);
                setPendingPlan(data.updated_plan);
            } else {
                setMessages(prev => [...prev, { role: 'ai', text: data.reply }]);
                if (data.updated_plan) {
                    onPlanUpdate(data.updated_plan);
                }
            }
        } catch (err) {
            console.error('Plan chat error:', err);
            setMessages(prev => [...prev, { 
                role: 'ai', 
                text: `⚠️ ${err.message || 'Connection error'}. Please try again.` 
            }]);
        } finally {
            setIsSending(false);
        }
    };

    const handleApplyReplan = () => {
        if (pendingPlan) {
            onPlanUpdate(pendingPlan);
            setMessages(prev => [...prev, { role: 'system', text: '✅ Plan restructured successfully!' }]);
        }
        setReplanPreview(null);
        setPendingPlan(null);
    };

    const handleCancelReplan = () => {
        setMessages(prev => [...prev, { role: 'system', text: 'Replan cancelled — plan unchanged.' }]);
        setReplanPreview(null);
        setPendingPlan(null);
    };

    const handleClear = () => {
        setMessages([]);
        setIsOpen(false);
        setReplanPreview(null);
        setPendingPlan(null);
    };

    const contextLabel = pinnedContext 
        ? pinnedContext.label
        : context.level === 'week'
            ? `Week ${(context.week_index ?? 0) + 1}`
            : context.level === 'day'
                ? `${context.day_key?.replace('_', ' ')}`
                : 'Session';

    return (
        <div 
            ref={containerRef}
            className={`plan-chat-container ${isExpanded ? 'expanded' : 'collapsed'}`}
        >

            {/* Chat Thread */}
            {isOpen && messages.length > 0 && (
                <div className="plan-chat-thread glass-card">
                    <div className="thread-header">
                        <span className="thread-title">
                            <span className="thread-dot" /> AI Trainer — {contextLabel}
                        </span>
                        <button className="thread-close" onClick={handleClear}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18" />
                                <line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                        </button>
                    </div>
                    <div className="thread-messages" ref={threadRef}>
                        {messages.map((msg, i) => (
                            <div key={i} className={`thread-msg ${msg.role}`}>
                                <div className="msg-bubble">
                                    {msg.text}
                                </div>
                            </div>
                        ))}
                        {isSending && (
                            <div className="thread-msg ai">
                                <div className="msg-bubble typing">
                                    <span /><span /><span />
                                </div>
                            </div>
                        )}

                        {/* Replan Confirmation Card */}
                        {replanPreview && (
                            <div className="replan-confirm-card">
                                <div className="replan-header">
                                    <span className="replan-icon">⚡</span>
                                    <span>Plan Restructure</span>
                                </div>
                                <div className="replan-details">
                                    {replanPreview.skipped_weeks?.length > 0 && (
                                        <div className="replan-row">
                                            <span className="replan-label">Skipping</span>
                                            <span className="replan-value skip">
                                                {replanPreview.skipped_weeks.map(w => `Week ${w}`).join(', ')}
                                            </span>
                                        </div>
                                    )}
                                    {replanPreview.affected_weeks?.length > 0 && (
                                        <div className="replan-row">
                                            <span className="replan-label">Adjusted</span>
                                            <span className="replan-value adjust">
                                                {replanPreview.affected_weeks.map(w => `Week ${w}`).join(', ')}
                                            </span>
                                        </div>
                                    )}
                                    {replanPreview.compensation && (
                                        <div className="replan-compensation">
                                            {replanPreview.compensation}
                                        </div>
                                    )}
                                </div>
                                <div className="replan-actions">
                                    <button className="replan-btn apply" onClick={handleApplyReplan}>
                                        Apply Changes
                                    </button>
                                    <button className="replan-btn cancel" onClick={handleCancelReplan}>
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Input Bar */}
            <form className="plan-chat-bar" onSubmit={handleSubmit}>
                {pinnedContext && (
                    <div className="context-chip">
                        <svg className="context-chip-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="12" y1="17" x2="12" y2="22"></line>
                            <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.68V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3v4.68a2 2 0 0 1-1.11 1.87l-1.78.89A2 2 0 0 0 5 15.24Z"></path>
                        </svg>
                        <span className="context-chip-label">{pinnedContext.label}</span>
                        <button type="button" className="context-chip-dismiss" onClick={onClearPin}>
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                        </button>
                    </div>
                )}
                <input
                    ref={inputRef}
                    type="text"
                    className="plan-chat-input"
                    placeholder={isFocused || pinnedContext ? `Ask about ${contextLabel}...` : "Click to chat..."}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    disabled={isSending || !!replanPreview}
                />
                <button
                    type="submit"
                    className={`plan-chat-send ${isSending ? 'loading' : ''}`}
                    disabled={!prompt.trim() || isSending || !!replanPreview}
                >
                    {isSending ? (
                        <div className="loader-mini" />
                    ) : (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="22" y1="2" x2="11" y2="13" />
                            <polygon points="22 2 15 22 11 13 2 9 22 2" />
                        </svg>
                    )}
                </button>
            </form>
        </div>
    );
}

export default PlanChat;
