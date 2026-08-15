import React, { useState, useEffect, useRef } from 'react';
import './OnboardingCard.css';

function OnboardingCard({
    question,
    inputType,
    suggestedOptions = [],
    onAnswer,
    isLoading,
    stepIndex = 1,
    totalSteps = 10
}) {
    const [value, setValue] = useState('');
    const [selectedChips, setSelectedChips] = useState([]);
    const inputRef = useRef(null);

    // Reset local state when a new question arrives
    useEffect(() => {
        setValue('');
        setSelectedChips([]);
        if (inputRef.current) {
            inputRef.current.focus();
        }
    }, [question]);

    const handleSubmit = (e) => {
        if (e) e.preventDefault();
        if (isLoading) return;

        if (inputType === 'multi_select') {
            if (selectedChips.length > 0) {
                onAnswer(selectedChips.join(', '));
            }
        } else if (value.trim()) {
            onAnswer(value.trim());
        }
    };

    const handleChipClick = (option) => {
        if (isLoading) return;

        if (inputType === 'multi_select') {
            setSelectedChips((prev) =>
                prev.includes(option)
                    ? prev.filter((o) => o !== option)
                    : [...prev, option]
            );
        } else {
            // single_select – send immediately
            onAnswer(option);
        }
    };

    const progress = (stepIndex / totalSteps) * 100;

    return (
        <div className={'onboarding-card-container' + (isLoading ? ' loading' : '')}>
            <div className="onboarding-card-glass">
                {/* Header with progress */}
                <div className="onboarding-header">
                    <div className="onboarding-header-top">
                        <div className="step-counter">Step {stepIndex} of {totalSteps}</div>
                        <div className="progress-percent-mini">{Math.round(progress)}%</div>
                    </div>
                    <div className="progress-track-mini">
                        <div className="progress-fill-mini" style={{ width: progress + '%' }} />
                    </div>
                </div>

                {/* Main content area */}
                <div className="onboarding-content">
                    <h2 className="question-text">{question}</h2>

                    {/* Suggestion chips */}
                    {suggestedOptions.length > 0 && (
                        <div className="chips-container">
                            {suggestedOptions.map((opt, i) => (
                                <button
                                    key={i}
                                    className={'suggestion-chip' + (selectedChips.includes(opt) ? ' active' : '')}
                                    onClick={() => handleChipClick(opt)}
                                    disabled={isLoading}
                                    type="button"
                                >
                                    {opt}
                                    {inputType === 'multi_select' && selectedChips.includes(opt) && (
                                        <span className="check-icon">✓</span>
                                    )}
                                </button>
                            ))}
                        </div>
                    )}

                    {/* Free text / numeric input */}
                    {(inputType === 'text' || inputType === 'numeric' || (inputType === 'multi_select' && suggestedOptions.length === 0)) && (
                        <form className="card-input-form" onSubmit={handleSubmit}>
                            <input
                                ref={inputRef}
                                type={inputType === 'numeric' ? 'number' : 'text'}
                                inputMode={inputType === 'numeric' ? 'numeric' : 'text'}
                                className="card-input"
                                value={value}
                                onChange={(e) => setValue(e.target.value)}
                                placeholder={inputType === 'numeric' ? 'Enter a number...' : 'Type your answer...'}
                                disabled={isLoading}
                                autoFocus
                            />
                        </form>
                    )}
                </div>

                {/* Footer with continue button */}
                <div className="onboarding-footer">
                    {((inputType === 'multi_select' && selectedChips.length > 0) || value.trim()) ? (
                        <button className="continue-btn" onClick={handleSubmit} disabled={isLoading} type="button">
                            {isLoading ? 'Processing...' : 'Continue'}
                            {!isLoading && (
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="5" y1="12" x2="19" y2="12" />
                                    <polyline points="12 5 19 12 12 19" />
                                </svg>
                            )}
                        </button>
                    ) : (
                        <div className="footer-hint">
                            {suggestedOptions.length > 0 ? 'Select an option to continue' : 'Type your answer above'}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default OnboardingCard;
