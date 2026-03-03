import React from 'react';
import './TypingIndicator.css';

function TypingIndicator() {
    return (
        <div className="message-row ai">
            <div className="avatar">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                    <circle cx="14" cy="14" r="14" fill="url(#avatarGrad2)" />
                    <path d="M9 18c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="#0A0A0F" strokeWidth="1.5" strokeLinecap="round" />
                    <circle cx="14" cy="10" r="3" stroke="#0A0A0F" strokeWidth="1.5" />
                    <defs>
                        <linearGradient id="avatarGrad2" x1="0" y1="0" x2="28" y2="28">
                            <stop stopColor="#00E5FF" />
                            <stop offset="1" stopColor="#00B8D4" />
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <div className="typing-bubble">
                <span className="typing-dot" style={{ animationDelay: '0s' }}></span>
                <span className="typing-dot" style={{ animationDelay: '0.15s' }}></span>
                <span className="typing-dot" style={{ animationDelay: '0.3s' }}></span>
            </div>
        </div>
    );
}

export default TypingIndicator;
