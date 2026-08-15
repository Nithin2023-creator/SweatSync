import React, { useState, useEffect } from 'react';
import ExerciseDetailModal from './ExerciseDetailModal';
import './MuscleExerciseList.css';

const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

const MuscleExerciseList = ({ muscle, muscleName, onClose, authToken }) => {
    const [exercises, setExercises] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedExercise, setSelectedExercise] = useState(null);

    useEffect(() => {
        const fetchExercises = async () => {
            setLoading(true);
            setError(null);
            try {
                const res = await fetch(`${API_BASE}/api/exercises/muscle/${muscle}`, {
                    headers: authToken ? { 'Authorization': `Bearer ${authToken}` } : {}
                });

                if (!res.ok) {
                    throw new Error('Failed to fetch exercises');
                }
                const data = await res.json();
                setExercises(data);
            } catch (err) {
                console.error('Error fetching muscle exercises:', err);
                setError('Could not load exercises. Please try again.');
            } finally {
                setLoading(false);
            }
        };

        if (muscle) {
            fetchExercises();
        }
    }, [muscle, authToken]);

    const handleBackdropClick = (e) => {
        if (e.target.className === 'muscle-list-overlay') {
            onClose();
        }
    };

    return (
        <div className="muscle-list-overlay" onClick={handleBackdropClick}>
            <div className="muscle-list-modal glass-card">
                <div className="muscle-list-header">
                    <h2>{muscleName} Exercises</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="muscle-list-content">
                    {loading ? (
                        <div className="muscle-loading">
                            <div className="loader-ring"></div>
                            <p>Scanning Arsenal...</p>
                        </div>
                    ) : error ? (
                        <div className="muscle-error">{error}</div>
                    ) : exercises.length === 0 ? (
                        <div className="muscle-empty">No exercises found for this muscle group.</div>
                    ) : (
                        <div className="exercise-grid">
                            {exercises.map((ex) => (
                                <div
                                    key={ex.id}
                                    className="exercise-card glass-card"
                                    onClick={() => setSelectedExercise(ex)}
                                >
                                    <div className="ex-card-content">
                                        <h3>{ex.name}</h3>
                                        <div className="ex-tags">
                                            <span className="ex-tag equipment">{ex.equipment}</span>
                                            <span className="ex-tag target">{ex.target}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {selectedExercise && (
                <ExerciseDetailModal
                    exerciseId={selectedExercise.id}
                    exerciseNameFallback={selectedExercise.name}
                    exerciseContext={{ name: selectedExercise.name, equipment: selectedExercise.equipment }}
                    onClose={() => setSelectedExercise(null)}
                    authToken={authToken}
                />
            )}
        </div>
    );
};

export default MuscleExerciseList;
