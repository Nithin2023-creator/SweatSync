import React, { useState, useEffect, useRef } from 'react';
import './PipelineProgress.css';

const STAGES = [
    { key: 'guardian', label: 'The Guardian', subtitle: 'Clinical Safety Review' },
    { key: 'architect', label: 'The Architect', subtitle: 'Strategic Blueprint' },
    { key: 'curator', label: 'The Curator', subtitle: '7-Week Exercise Plan' },
];

function PipelineProgress({ sho, onComplete, authToken, provider = 'groq' }) {
    const [stageStatuses, setStageStatuses] = useState({});
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);
    const [retryCount, setRetryCount] = useState(0);
    const eventSourceRef = useRef(null);

    useEffect(() => {
        const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

        // Use fetch with ReadableStream for POST + SSE
        const abortController = new AbortController();

        const startGeneration = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/generate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        sho,
                        provider: provider
                    }),
                    signal: abortController.signal,
                });

                if (!response.ok) throw new Error('Generation failed');

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); // Keep incomplete line in buffer

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                handleEvent(data);
                            } catch (e) {
                                console.warn('SSE parse error:', e);
                            }
                        }
                    }
                }
            } catch (err) {
                if (err.name !== 'AbortError') {
                    console.error('Generation error:', err);
                    setError('Failed to connect to the pipeline. Please try again.');
                }
            }
        };

        startGeneration();

        return () => abortController.abort();
    }, [sho, retryCount]);

    const handleEvent = (data) => {
        if (data.stage === 'complete') {
            setProgress(100);
            setTimeout(() => onComplete(data.plan, data.session_id), 1500);
            return;
        }

        setStageStatuses(prev => ({
            ...prev,
            [data.stage]: {
                status: data.status,
                summary: data.summary || '',
                week: data.week,
            }
        }));

        if (data.progress !== undefined) {
            setProgress(data.progress);
        }

        if (data.status === 'error') {
            setError(data.summary);
        }
    };

    const getStageClass = (stageKey) => {
        const info = stageStatuses[stageKey];
        if (!info) return 'pending';
        return info.status;
    };

    const getStageIcon = (stageKey) => {
        const info = stageStatuses[stageKey];
        if (!info) return <span className="icon">○</span>;
        if (info.status === 'running') return <div className="stage-spinner" />;
        if (info.status === 'done') return <span className="icon">✓</span>;
        if (info.status === 'error') return <span className="icon">✗</span>;
        return <span className="icon">○</span>;
    };

    const getStatusText = () => {
        if (error) return 'Pipeline encountered an error';
        if (progress >= 100) return 'Plan generation complete!';
        const running = STAGES.find(s => stageStatuses[s.key]?.status === 'running');
        if (running) return `${running.label} is working...`;
        return 'Initializing pipeline...';
    };

    return (
        <div className="pipeline-overlay">
            {/* Ambient Accents */}
            <div className="pipeline-ambient">
                <div className="p-orb p-orb-1" />
                <div className="p-orb p-orb-2" />
            </div>

            <div className="pipeline-card">
                <h2>Generating Your Plan</h2>
                <p className="pipeline-subtitle">{getStatusText()}</p>

                <div className="pipeline-timeline">
                    {STAGES.map((stage) => {
                        const info = stageStatuses[stage.key];
                        return (
                            <div
                                key={stage.key}
                                className={`pipeline-stage ${getStageClass(stage.key)}`}
                            >
                                <div className="stage-indicator">
                                    {getStageIcon(stage.key)}
                                </div>
                                <div className="stage-content">
                                    <div className="stage-label">
                                        {stage.label}
                                        <span className="stage-subtitle-inline">
                                            {stage.subtitle}
                                        </span>
                                    </div>
                                    <div className="stage-summary">
                                        {info?.summary || 'Waiting...'}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                <div className="pipeline-progress-bar">
                    <div className="progress-track">
                        <div className="progress-fill" style={{ width: `${progress}%` }} />
                    </div>
                    <div className="progress-label">
                        <span className="progress-text">
                            {progress < 100 ? 'Processing...' : 'Complete!'}
                        </span>
                        <span className="progress-percent">{progress}%</span>
                    </div>
                </div>

                {error && (
                    <div className="pipeline-error-action">
                        <button onClick={() => {
                            setError(null);
                            setProgress(0);
                            setStageStatuses({});
                            setRetryCount(prev => prev + 1);
                        }}>
                            Retry
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default PipelineProgress;
