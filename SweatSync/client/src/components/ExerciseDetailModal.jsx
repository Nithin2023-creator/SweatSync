import React, { useState, useEffect } from 'react';
import './ExerciseDetailModal.css';

function ExerciseDetailModal({ exerciseId, exerciseNameFallback, exerciseContext, onClose, authToken }) {
    const [exerciseData, setExerciseData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

    useEffect(() => {
        let isMounted = true;
        const fetchExerciseData = async () => {
            setIsLoading(true);
            setError(null);

            try {
                let res;

                // Always try fetching by ID if it's a valid ID
                if (exerciseId && exerciseId !== "custom" && exerciseId !== "unknown") {
                    res = await fetch(`${API_BASE}/api/exercise/details/${exerciseId}`, {
                        headers: authToken ? { 'Authorization': `Bearer ${authToken}` } : {}
                    });
                }

                // Fallback to name search if ID fetch failed, wasn't attempted, or returned 404
                if (!res || !res.ok) {
                    const searchName = encodeURIComponent(exerciseNameFallback?.toLowerCase() || "");
                    res = await fetch(`${API_BASE}/api/exercise/search?name=${searchName}`, {
                        headers: authToken ? { 'Authorization': `Bearer ${authToken}` } : {}
                    });
                }

                if (!res.ok) throw new Error('Failed to fetch exercise details');

                const data = await res.json();
                if (data.error) {
                    throw new Error(data.error);
                }

                if (isMounted) {
                    setExerciseData(Array.isArray(data) ? data[0] : data);
                }
            } catch (err) {
                if (isMounted) setError(err.message);
            } finally {
                if (isMounted) setIsLoading(false);
            }
        };

        if (exerciseId || exerciseNameFallback) {
            fetchExerciseData();
        } else {
            setIsLoading(false);
            setError("This exercise is custom or lacks database matching.");
        }

        return () => { isMounted = false; };
    }, [exerciseId, exerciseNameFallback, API_BASE, authToken]);

    // Handle clicks outside the modal content to close
    const handleOverlayClick = (e) => {
        if (e.target.className.includes('exercise-modal-overlay')) {
            onClose();
        }
    };

    return (
        <div className="exercise-modal-overlay" onClick={handleOverlayClick}>
            <div className="exercise-modal-content glass-card">
                <button className="close-btn" onClick={onClose}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>

                {isLoading ? (
                    <div className="modal-loading">
                        <div className="loader-spinner"></div>
                        <p>Loading exercise data...</p>
                    </div>
                ) : error ? (
                    <div className="modal-error">
                        <p>{error}</p>
                        <p className="error-subtext">No detailed visualization available for "{exerciseNameFallback}".</p>
                        {exerciseContext && (
                            <div className="fallback-context">
                                <h3>Plan Context</h3>
                                <p><strong>Target:</strong> {exerciseContext.sets} sets of {exerciseContext.reps}</p>
                            </div>
                        )}
                    </div>
                ) : exerciseData ? (
                    <div className="modal-body">
                        <h2>{exerciseData.name}</h2>

                        <div className="modal-hero">
                            <div className="image-container">
                                {/* We pipe the GIF securely so the RapidAPI key is never exposed */}
                                <img
                                    src={`${API_BASE}/api/exercise/image/${exerciseData.id}`}
                                    alt={exerciseData.name}
                                    className="exercise-gif"
                                />
                            </div>

                            <div className="quick-stats">
                                <div className="stat-pill">
                                    <span className="stat-label">Target</span>
                                    <span className="stat-value">{exerciseData.target}</span>
                                </div>
                                <div className="stat-pill">
                                    <span className="stat-label">Body Part</span>
                                    <span className="stat-value">{exerciseData.bodyPart}</span>
                                </div>
                                <div className="stat-pill">
                                    <span className="stat-label">Equipment</span>
                                    <span className="stat-value">{exerciseData.equipment}</span>
                                </div>
                                {exerciseContext && (
                                    <div className="stat-pill plan-target">
                                        <span className="stat-label">Goal</span>
                                        <span className="stat-value">{exerciseContext.sets}x{exerciseContext.reps}</span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {exerciseData.secondaryMuscles && exerciseData.secondaryMuscles.length > 0 && (
                            <div className="secondary-muscles">
                                <h3>Secondary Muscles</h3>
                                <div className="muscle-tags">
                                    {exerciseData.secondaryMuscles.map((m, i) => (
                                        <span key={i} className="muscle-tag">{m}</span>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="instructions-section">
                            <h3>Form & Instructions</h3>
                            <ol className="instructions-list">
                                {exerciseData.instructions.map((step, i) => (
                                    <li key={i}>{step}</li>
                                ))}
                            </ol>
                        </div>
                    </div>
                ) : null}
            </div>
        </div>
    );
}

export default ExerciseDetailModal;
