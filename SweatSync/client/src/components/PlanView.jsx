import React, { useState } from 'react';
import PlanChat from './PlanChat';
import ExerciseDetailModal from './ExerciseDetailModal';
import AnatomyExplorer from './AnatomyExplorer';
import SwipeableCard from './SwipeableCard';
import './PlanView.css';

function PlanView({ plan, onUpdate, sessionId, authToken, provider = 'groq', onLogout }) {
    const [view, setView] = useState('weeks'); // 'weeks' | 'days' | 'session'
    const [activeWeekIdx, setActiveWeekIdx] = useState(0);
    const [activeDayKey, setActiveDayKey] = useState(null);
    const [selectedExerciseContext, setSelectedExerciseContext] = useState(null);
    const [showAnatomy, setShowAnatomy] = useState(false);
    const [pinnedContext, setPinnedContext] = useState(null);

    const weeks = plan?.weeks || [];

    if (!weeks.length) {
        return (
            <div className="plan-overlay">
                <div className="plan-empty">
                    <h3>No Plan Data</h3>
                    <p>The pipeline did not produce any workout weeks.</p>
                </div>
            </div>
        );
    }

    const handleBack = () => {
        if (view === 'session') {
            setView('days');
            setActiveDayKey(null);
        } else if (view === 'days') {
            setView('weeks');
        }
    };

    const handleWeekSelect = (idx) => {
        setActiveWeekIdx(idx);
        setView('days');
    };

    const handleDaySelect = (key) => {
        setActiveDayKey(key);
        setView('session');
    };

    const currentWeek = weeks[activeWeekIdx];
    const days = currentWeek?.days || {};
    const activeDay = activeDayKey ? days[activeDayKey] : null;

    // Determine current chat context
    const defaultChatContext = {
        level: view === 'weeks' ? 'week' : view === 'days' ? 'day' : 'session',
        week_index: activeWeekIdx,
        day_key: activeDayKey
    };

    const handlePin = (type, label, weekIdx, dayKey, exerciseIdx) => {
        setPinnedContext({ type, label, weekIdx, dayKey, exerciseIdx });
    };

    // --- View Renderers ---

    const renderWeeks = () => (
        <div className="dashboard-container">
            <div className="dashboard-hero">
                <div className="hero-content">
                    <span className="hero-tag">Active Evolution</span>
                    <h1>Tactical Dashboard</h1>
                    <p>Strategic overview of your multi-phase training progression.</p>
                </div>
                <div className="muscle-cta-card glass-card" onClick={() => setShowAnatomy(true)}>
                    <div className="cta-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <path d="M12 2a5 5 0 0 0-5 5v3a5 5 0 0 0 10 0V7a5 5 0 0 0-5-5z" />
                            <path d="M12 15a7 7 0 0 0-7 7" />
                            <path d="M12 15a7 7 0 0 1 7 7" />
                        </svg>
                    </div>
                    <div className="cta-text">
                        <h3>Muscle Map</h3>
                        <p>Explore anatomical targets</p>
                    </div>
                    <div className="cta-arrow">→</div>
                </div>
            </div>

            <div className="weeks-grid">
                {weeks.map((week, idx) => (
                    <SwipeableCard
                        key={idx}
                        className="week-card-swipe-wrapper"
                        onSwipeRight={() => handlePin('week', `Phase ${idx + 1}`, idx, null, null)}
                        pinLabel="Pin Week"
                    >
                        <div
                            className={`week-card-large glass-card ${idx === activeWeekIdx ? 'active' : ''}`}
                            onClick={() => handleWeekSelect(idx)}
                            style={{ animationDelay: `${idx * 0.1}s` }}
                        >
                            <div className="week-card-top">
                                <div className="week-card-badge">Phase {idx + 1}</div>
                                {idx === activeWeekIdx && <div className="current-week-tag">Current</div>}
                            </div>
                            <div className="week-card-phase">{week.phase}</div>
                            <div className="week-card-summary">
                                {Object.keys(week.days).length} Tactical Sessions
                            </div>
                            <div className="week-card-progress">
                                <div className="progress-bar-mini">
                                    <div className="progress-fill-mini" style={{ width: idx < activeWeekIdx ? '100%' : idx === activeWeekIdx ? '30%' : '0%' }} />
                                </div>
                            </div>
                        </div>
                    </SwipeableCard>
                ))}
            </div>
        </div>
    );

    const renderDays = () => (
        <div className="days-stack">
            {Object.entries(days).map(([key, day]) => {
                const dayLabel = day.day_label || key.replace('_', ' ');
                const exercises = day.exercises || [];
                const isRest = dayLabel.toLowerCase().includes('rest') || exercises.length === 0;

                return isRest ? (
                    <div
                        key={key}
                        className="day-row-card glass-card rest"
                    >
                        <div className="day-row-info">
                            <div className="day-row-name">{key.replace('_', ' ').toUpperCase()}</div>
                            <div className="day-row-label">{dayLabel}</div>
                        </div>
                        <div className="day-rest-pill">Active Rest</div>
                    </div>
                ) : (
                    <SwipeableCard
                        key={key}
                        className="day-row-swipe-wrapper"
                        onSwipeRight={() => handlePin('day', dayLabel, activeWeekIdx, key, null)}
                        pinLabel="Pin Day"
                    >
                        <div
                            className="day-row-card glass-card"
                            onClick={() => handleDaySelect(key)}
                        >
                            <div className="day-row-info">
                                <div className="day-row-name">{key.replace('_', ' ').toUpperCase()}</div>
                                <div className="day-row-label">{dayLabel}</div>
                            </div>
                            <div className="day-row-meta">
                                <span className="exercise-count">{exercises.length} Exercises</span>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="9 18 15 12 9 6" />
                                </svg>
                            </div>
                        </div>
                    </SwipeableCard>
                );
            })}
        </div>
    );

    const renderSessionData = () => {
        if (!activeDay) return null;
        const exercises = activeDay.exercises || [];

        return (
            <div className="session-detail">
                <div className="session-header">
                    <div className="session-title-wrap">
                        <h2>{activeDay.day_label}</h2>
                        <p>{exercises.length} Tactical Movements</p>
                    </div>
                    <div className="session-stats-bar">
                        <div className="s-stat">
                            <span className="s-val">{exercises.length}</span>
                            <span className="s-lbl">Exercises</span>
                        </div>
                        <div className="s-stat">
                            <span className="s-val">{exercises.reduce((acc, ex) => acc + (parseInt(ex.sets) || 0), 0)}</span>
                            <span className="s-lbl">Total Sets</span>
                        </div>
                        <div className="s-stat">
                            <span className="s-val">~{Math.round(exercises.length * 8)}</span>
                            <span className="s-lbl">Est. Min</span>
                        </div>
                    </div>
                </div>
                <div className="exercise-list-detailed">
                    {exercises.map((ex, i) => (
                        <SwipeableCard
                            key={i}
                            className="exercise-card-swipe-wrapper"
                            onSwipeRight={() => handlePin('exercise', `${ex.name} — ${ex.sets}x${ex.reps}`, activeWeekIdx, activeDayKey, i)}
                            pinLabel="Pin"
                        >
                            <div
                                className="exercise-detail-card glass-card clickable-exercise"
                                onClick={() => setSelectedExerciseContext(ex)}
                                style={{ cursor: 'pointer', transition: 'all 0.2s ease', margin: 0 }}
                            >
                                <div className="ex-main">
                                    <div className="ex-num">{i + 1}</div>
                                    <div className="ex-info">
                                        <h3>{ex.name}</h3>
                                        <p>{ex.equipment}</p>
                                    </div>
                                    <div className="ex-targets">
                                        <div className="target-pill">{ex.sets}x{ex.reps}</div>
                                        <div className="target-pill rpe">RPE {ex.rpe}</div>
                                    </div>
                                </div>
                            </div>
                        </SwipeableCard>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <div className="plan-overlay">
            <div className={`plan-viewer-container ${view}-view`}>

                {/* Header / Breadcrumbs */}
                <header className="plan-nav-header">
                    <div className="nav-header-left">
                        {view !== 'weeks' && (
                            <button className="nav-back" onClick={handleBack}>
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="19" y1="12" x2="5" y2="12" />
                                    <polyline points="12 19 5 12 12 5" />
                                </svg>
                            </button>
                        )}
                    <div className="nav-title-group">
                        <div className="breadcrumbs">
                            <span className={`crumb ${view === 'weeks' ? 'active' : 'clickable'}`} onClick={() => setView('weeks')}>Plan</span>
                            {view !== 'weeks' && (
                                <>
                                    <span className="crumb-sep">/</span>
                                    <span className={`crumb ${view === 'days' ? 'active' : 'clickable'}`} onClick={() => setView('days')}>Week {currentWeek.week_number}</span>
                                </>
                            )}
                            {view === 'session' && (
                                <>
                                    <span className="crumb-sep">/</span>
                                    <span className="crumb active">{activeDayKey.replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}</span>
                                </>
                            )}
                        </div>
                        {view !== 'weeks' && (
                            <div className="nav-title">
                                {view === 'days' && <h1>Week {currentWeek.week_number} <span className="phase-tag">{currentWeek.phase}</span></h1>}
                                {view === 'session' && <h1>{activeDay?.day_label || 'Session Plan'}</h1>}
                            </div>
                        )}
                    </div>
                    </div>

                    <div className="nav-header-right">
                        <button className="muscle-map-btn" onClick={() => setShowAnatomy(true)}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <path d="M12 2a5 5 0 0 0-5 5v3a5 5 0 0 0 10 0V7a5 5 0 0 0-5-5z" />
                                <path d="M12 15a7 7 0 0 0-7 7" />
                                <path d="M12 15a7 7 0 0 1 7 7" />
                            </svg>
                            <span>Muscle Map</span>
                        </button>
                        <button className="nav-logout-btn" onClick={onLogout} title="Logout">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                <polyline points="16 17 21 12 16 7" />
                                <line x1="21" y1="12" x2="9" y2="12" />
                            </svg>
                        </button>
                    </div>
                </header>

                <main className="plan-main-scroll">
                    <div className="view-slider">
                        {view === 'weeks' && renderWeeks()}
                        {view === 'days' && renderDays()}
                        {view === 'session' && renderSessionData()}
                    </div>
                </main>

                {/* Contextual Chat Bar */}
                <PlanChat
                    context={defaultChatContext}
                    pinnedContext={pinnedContext}
                    onClearPin={() => setPinnedContext(null)}
                    currentPlan={plan}
                    onPlanUpdate={onUpdate}
                    sessionId={sessionId}
                    provider={provider}
                    authToken={authToken}
                />
            </div>

            {selectedExerciseContext && (
                <ExerciseDetailModal
                    exerciseId={selectedExerciseContext.exercise_id}
                    exerciseNameFallback={selectedExerciseContext.name}
                    exerciseContext={selectedExerciseContext}
                    onClose={() => setSelectedExerciseContext(null)}
                    authToken={authToken}
                />
            )}
            {showAnatomy && (
                <div className="anatomy-modal-overlay" onClick={() => setShowAnatomy(false)}>
                    <div className="anatomy-modal-content glass-card" onClick={e => e.stopPropagation()}>
                        <button className="close-anatomy" onClick={() => setShowAnatomy(false)}>×</button>
                        <AnatomyExplorer authToken={authToken} />
                    </div>
                </div>
            )}
        </div>
    );
}

export default PlanView;
