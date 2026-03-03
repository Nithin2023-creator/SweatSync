import React from 'react';
import './ProfileComplete.css';

function ProfileComplete({ sho }) {
    return (
        <div className="profile-complete-overlay">
            <div className="profile-card">
                <div className="profile-card-glow" />
                <div className="profile-icon">
                    <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                        <circle cx="28" cy="28" r="28" fill="url(#completeGrad)" />
                        <path d="M18 28L25 35L38 22" stroke="#0A0A0F" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
                        <defs>
                            <linearGradient id="completeGrad" x1="0" y1="0" x2="56" y2="56">
                                <stop stopColor="#00E676" />
                                <stop offset="1" stopColor="#00E5FF" />
                            </linearGradient>
                        </defs>
                    </svg>
                </div>

                <h2>Profile Complete!</h2>
                <p className="profile-subtitle">
                    Handing your data over to <span className="highlight">The Guardian</span> for clinical safety review...
                </p>

                <div className="sho-summary">
                    <div className="sho-row">
                        <span className="sho-label">Age</span>
                        <span className="sho-value">{sho.age} years</span>
                    </div>
                    <div className="sho-row">
                        <span className="sho-label">Weight</span>
                        <span className="sho-value">{sho.weight_kg} kg</span>
                    </div>
                    <div className="sho-row">
                        <span className="sho-label">Height</span>
                        <span className="sho-value">{sho.height_cm} cm</span>
                    </div>
                    <div className="sho-row">
                        <span className="sho-label">Goal</span>
                        <span className="sho-value">{sho.goals}</span>
                    </div>
                    <div className="sho-row">
                        <span className="sho-label">Experience</span>
                        <span className="sho-value capitalize">{sho.experience_level}</span>
                    </div>
                    <div className="sho-row">
                        <span className="sho-label">Timeline</span>
                        <span className="sho-value">{sho.target_timeline || 'N/A'}</span>
                    </div>
                    <div className="sho-row">
                        <span className="sho-label">Training Days</span>
                        <span className="sho-value">{sho.training_days_per_week}/week</span>
                    </div>
                    {sho.medical_flags && sho.medical_flags.length > 0 && (
                        <div className="sho-row">
                            <span className="sho-label">Medical Flags</span>
                            <span className="sho-value warn">{sho.medical_flags.join(', ')}</span>
                        </div>
                    )}
                </div>

                <div className="progress-bar-wrapper">
                    <div className="progress-bar">
                        <div className="progress-fill" />
                    </div>
                    <span className="progress-text">Processing with Guardian Agent...</span>
                </div>
            </div>
        </div>
    );
}

export default ProfileComplete;
