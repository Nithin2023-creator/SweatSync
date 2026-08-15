import React, { useState } from 'react';
import Model from 'react-body-highlighter';
import MuscleExerciseList from './MuscleExerciseList';
import './AnatomyExplorer.css';

const AnatomyExplorer = ({ authToken }) => {
    const [modelType, setModelType] = useState('anterior'); // 'anterior' or 'posterior'
    const [selectedMuscle, setSelectedMuscle] = useState(null);
    const [showExercises, setShowExercises] = useState(false);

    // We pass empty data because we just want the interactive SVG, not necessarily colored by frequency yet
    const data = [];

    const handleClick = ({ muscle }) => {
        setSelectedMuscle(muscle);
        setShowExercises(false); // Reset list if clicking a new muscle
    };

    const formatMuscleName = (name) => {
        if (!name) return '';
        return name.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    };

    return (
        <div className="anatomy-explorer-container">
            <div className="anatomy-header">
                <h2>Targeted Muscle Groups</h2>
                <p>Select a muscle to explore isolation exercises.</p>
                <div className="anatomy-toggle">
                    <button
                        className={modelType === 'anterior' ? 'active' : ''}
                        onClick={() => setModelType('anterior')}
                    >
                        Front
                    </button>
                    <button
                        className={modelType === 'posterior' ? 'active' : ''}
                        onClick={() => setModelType('posterior')}
                    >
                        Back
                    </button>
                </div>
            </div>

            <div className="anatomy-body-wrapper">
                <div className="anatomy-model-container">
                    <Model
                        data={data}
                        style={{ width: '100%', maxWidth: '300px', height: 'auto', padding: '1rem' }}
                        onClick={handleClick}
                        type={modelType}
                        bodyColor="#1a1f2e"
                        highlightedColors={['#00E5FF']} // Our cyan accent
                    />
                </div>

                {selectedMuscle && (
                    <div className="muscle-popup-card glass-card">
                        <div className="muscle-popup-header">
                            <h3>{formatMuscleName(selectedMuscle)}</h3>
                            <button className="close-popup" onClick={() => setSelectedMuscle(null)}>×</button>
                        </div>
                        <p>Explore tactical movements specifically targeting the {formatMuscleName(selectedMuscle)}.</p>
                        <button
                            className="view-exercises-btn"
                            onClick={() => setShowExercises(true)}
                        >
                            View Exercises →
                        </button>
                    </div>
                )}
            </div>

            {showExercises && selectedMuscle && (
                <MuscleExerciseList
                    muscle={selectedMuscle}
                    muscleName={formatMuscleName(selectedMuscle)}
                    onClose={() => setShowExercises(false)}
                    authToken={authToken}
                />
            )}
        </div>
    );
};

export default AnatomyExplorer;
