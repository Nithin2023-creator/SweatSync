import React from 'react';
import './MessageBubble.css';

const AVATAR_SVG = (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        <circle cx="14" cy="14" r="14" fill="url(#avatarGrad)" />
        <path d="M9 18c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="#0A0A0F" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="14" cy="10" r="3" stroke="#0A0A0F" strokeWidth="1.5" />
        <path d="M7 9l3 2M21 9l-3 2" stroke="#00E5FF" strokeWidth="1.2" strokeLinecap="round" />
        <defs>
            <linearGradient id="avatarGrad" x1="0" y1="0" x2="28" y2="28">
                <stop stopColor="#00E5FF" />
                <stop offset="1" stopColor="#00B8D4" />
            </linearGradient>
        </defs>
    </svg>
);

function MessageBubble({ message }) {
    const { role, content } = message;
    const isUser = role === 'user';
    const isSystem = role === 'system';

    return (
        <div className={`message-row ${isUser ? 'user' : 'ai'} ${isSystem ? 'system' : ''}`}>
            {!isUser && !isSystem && (
                <div className="avatar">{AVATAR_SVG}</div>
            )}
            <div className={`bubble ${isUser ? 'bubble-user' : isSystem ? 'bubble-system' : 'bubble-ai'}`}>
                {isSystem && <span className="system-icon">✅</span>}
                <p>{content}</p>
            </div>
        </div>
    );
}

export default MessageBubble;
