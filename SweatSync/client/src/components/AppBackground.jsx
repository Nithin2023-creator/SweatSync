import React from 'react';
import './AppBackground.css';

const AppBackground = () => {
    return (
        <div className="app-background">
            <div className="mesh-grid" />
            <div className="ambient-glows">
                <div className="ambient-orb orb-primary" />
                <div className="ambient-orb orb-secondary" />
                <div className="ambient-orb orb-tertiary" />
            </div>
        </div>
    );
};

export default AppBackground;
