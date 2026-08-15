import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import './ChatWindow.css';

function ChatWindow({ messages, isLoading }) {
    const bottomRef = useRef(null);

    useEffect(() => {
        if (bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, isLoading]);

    return (
        <div className="chat-window">
            <div className="chat-header">
                <div className="chat-header-inner">
                    <div className="header-logo">
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                            <rect width="32" height="32" rx="10" fill="url(#logoGrad)" />
                            <path d="M10 22V14L16 10L22 14V22" stroke="#0A0A0F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <circle cx="16" cy="16" r="2.5" fill="#0A0A0F" />
                            <defs>
                                <linearGradient id="logoGrad" x1="0" y1="0" x2="32" y2="32">
                                    <stop stopColor="#00E5FF" />
                                    <stop offset="1" stopColor="#00E676" />
                                </linearGradient>
                            </defs>
                        </svg>
                    </div>
                    <div className="header-text">
                        <h1>SweatSync</h1>
                        <span className="header-status">
                            <span className="status-dot"></span>
                            AI Onboarding
                        </span>
                    </div>
                </div>
            </div>

            <div className="messages-container">
                {messages.map((msg, i) => (
                    <MessageBubble key={i} message={msg} />
                ))}
                {isLoading && <TypingIndicator />}
                <div ref={bottomRef} className="scroll-anchor" />
            </div>
        </div>
    );
}

export default ChatWindow;
