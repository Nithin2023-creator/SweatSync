import React, { useState } from 'react';
import './Login.css';

const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

const Login = ({ onLogin }) => {
    const [isRegister, setIsRegister] = useState(false);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';

        try {
            const loginData = new URLSearchParams();
            loginData.append('username', username);
            loginData.append('password', password);

            const res = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                body: isRegister ? JSON.stringify({ username, password }) : loginData,
                headers: isRegister ? { 'Content-Type': 'application/json' } : { 'Content-Type': 'application/x-www-form-urlencoded' },
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || 'Authentication failed');
            }

            if (isRegister) {
                setIsRegister(false);
                setError('Registration successful! Please login.');
            } else {
                localStorage.setItem('sweatsync_token', data.access_token);
                onLogin(data.access_token);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <div className="brand-logo">Sy</div>
                    <h1>SweatSync</h1>
                    <p>{isRegister ? 'Create your elite fitness account' : 'Welcome back, athlete'}</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="input-group">
                        <label>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter your username"
                            required
                        />
                    </div>
                    <div className="input-group">
                        <label>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            required
                        />
                    </div>

                    {error && <div className={`auth-message ${error.includes('successful') ? 'success' : 'error'}`}>{error}</div>}

                    <button type="submit" className="login-btn" disabled={isLoading}>
                        {isLoading ? 'Processing...' : (isRegister ? 'Create Account' : 'Login')}
                    </button>
                </form>

                <div className="login-footer">
                    <button onClick={() => setIsRegister(!isRegister)} className="toggle-btn">
                        {isRegister ? 'Already have an account? Login' : "Don't have an account? Register"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Login;
