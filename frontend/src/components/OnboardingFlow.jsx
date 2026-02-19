import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, User, Bot, Loader2, ChevronRight } from 'lucide-react';
import DynamicInputRenderer from './DynamicInputRenderer';

const API_BASE_URL = 'http://localhost:5000/api/onboarding';

const OnboardingFlow = () => {
    const [chatHistory, setChatHistory] = useState([]);
    const [currentStep, setCurrentStep] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isComplete, setIsComplete] = useState(false);
    const scrollRef = useRef(null);

    // Initial fetch
    useEffect(() => {
        fetchNextStep([]);
    }, []);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [chatHistory, currentStep]);

    const fetchNextStep = async (history) => {
        setIsLoading(true);
        try {
            const response = await axios.post(`${API_BASE_URL}/next-step`, {
                chat_history: history
            });

            const stepData = response.data;
            setCurrentStep(stepData);

            if (stepData.onboarding_complete) {
                setIsComplete(true);
            }
        } catch (error) {
            console.error('Error fetching next step:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleUserAnswer = (answer, displayValue = null) => {
        const newUserMessage = { role: 'user', content: answer };
        const newHistory = [...chatHistory];

        // If we have an assistant message currently being shown, add it to history
        if (currentStep && currentStep.agent_message) {
            newHistory.push({ role: 'assistant', content: currentStep.agent_message });
        }

        newHistory.push(newUserMessage);
        setChatHistory(newHistory);
        setCurrentStep(null); // Clear while fetching
        fetchNextStep(newHistory);
    };

    return (
        <div className="flex flex-col h-screen w-full max-w-2xl mx-auto bg-slate-950 text-slate-100 overflow-hidden shadow-2xl">
            {/* Header */}
            <header className="p-4 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md flex items-center justify-between">
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                    SweatSync AI
                </h1>
                <div className="text-xs text-slate-400 px-2 py-1 rounded-full border border-slate-800 bg-slate-900">
                    Onboarding
                </div>
            </header>

            {/* Chat Area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth"
            >
                <AnimatePresence>
                    {chatHistory.map((msg, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div className={`flex max-w-[85%] items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                <div className={`p-2 rounded-lg ${msg.role === 'user' ? 'bg-blue-600' : 'bg-slate-800'}`}>
                                    {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                                </div>
                                <div className={`p-3 rounded-2xl ${msg.role === 'user'
                                        ? 'bg-blue-600/20 border border-blue-500/30'
                                        : 'bg-slate-900 border border-slate-800'
                                    }`}>
                                    <p className="text-sm md:text-base leading-relaxed">{msg.content}</p>
                                </div>
                            </div>
                        </motion.div>
                    ))}

                    {currentStep && !isComplete && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex justify-start"
                        >
                            <div className="flex max-w-[85%] items-start gap-3">
                                <div className="p-2 rounded-lg bg-emerald-600">
                                    <Bot size={18} />
                                </div>
                                <div className="p-3 rounded-2xl bg-slate-900 border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                                    <p className="text-sm md:text-base leading-relaxed italic">{currentStep.agent_message}</p>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {isLoading && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex justify-start"
                        >
                            <div className="flex items-center gap-2 p-3 text-slate-400">
                                <Loader2 className="animate-spin" size={16} />
                                <span className="text-xs uppercase tracking-widest font-bold">SweatSync is thinking...</span>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Input Area */}
            <footer className="p-4 border-t border-slate-800 bg-slate-900/80">
                {!isComplete ? (
                    <DynamicInputRenderer
                        step={currentStep}
                        onAnswer={handleUserAnswer}
                        disabled={isLoading}
                    />
                ) : (
                    <div className="text-center p-4">
                        <h2 className="text-emerald-400 font-bold mb-2 text-xl">Onboarding Complete!</h2>
                        <p className="text-slate-400 text-sm mb-4">I'm now generating your personalized 7-week plan based on your profile.</p>
                        <button className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all">
                            See My Plan <ChevronRight size={20} />
                        </button>
                    </div>
                )}
            </footer>
        </div>
    );
};

export default OnboardingFlow;
