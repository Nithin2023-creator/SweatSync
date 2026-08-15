import React from 'react';
import './SplashScreen.css';

function SplashScreen({ onStart, provider, onToggleProvider }) {
    return (
        <div className="splash-screen">
            <div className="splash-particles">
                {[...Array(6)].map((_, i) => (
                    <div key={i} className="particle" style={{
                        left: `${Math.random() * 100}%`,
                        animationDelay: `${Math.random() * 5}s`,
                        animationDuration: `${5 + Math.random() * 5}s`
                    }} />
                ))}
            </div>

            <div className="splash-content">
                <div className="splash-logo">
                    <svg width="100" height="100" viewBox="0 0 32 32" fill="none">
                        <rect width="32" height="32" rx="10" fill="url(#splashGrad)" />
                        <path d="M10 22V14L16 10L22 14V22" stroke="#0A0A0F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <circle cx="16" cy="16" r="2.5" fill="#0A0A0F" />
                        <defs>
                            <linearGradient id="splashGrad" x1="0" y1="0" x2="32" y2="32">
                                <stop stopColor="#00E5FF" />
                                <stop offset="1" stopColor="#00E676" />
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
                <h1 className="splash-title">SweatSync</h1>
                <p className="splash-subtitle">Your AI-powered fitness journey begins here.</p>

                <div className="splash-provider-select">
                    <p className="provider-info-text">Choose your intelligence platform:</p>
                    <div className="provider-options">
                        <button 
                            className={`provider-opt ${provider === 'ollama' ? 'active' : ''}`}
                            onClick={() => provider !== 'ollama' && onToggleProvider()}
                        >
                            <span className="opt-title">Private Local</span>
                            <span className="opt-sub">Ollama (192.168.1.18)</span>
                        </button>
                        <button 
                            className={`provider-opt ${provider === 'groq' ? 'active' : ''}`}
                            onClick={() => provider !== 'groq' && onToggleProvider()}
                        >
                            <span className="opt-title">Cloud Performance</span>
                            <span className="opt-sub">Groq (Llama 3.1)</span>
                        </button>
                    </div>
                </div>

                <button className="splash-btn" onClick={onStart}>
                    Get Started
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="5" y1="12" x2="19" y2="12" />
                        <polyline points="12 5 19 12 12 19" />
                    </svg>
                </button>
            </div>

            <div className="splash-footer">
                Professional Grade • AI Driven
            </div>
        </div>
    );
}

export default SplashScreen;
