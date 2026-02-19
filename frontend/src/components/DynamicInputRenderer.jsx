import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ArrowRight, Check } from 'lucide-react';

const DynamicInputRenderer = ({ step, onAnswer, disabled }) => {
    const [inputValue, setInputValue] = useState('');
    const [otherMode, setOtherMode] = useState(false);
    const [selectedMulti, setSelectedMulti] = useState([]);
    const inputRef = useRef(null);

    useEffect(() => {
        // Reset internal state on step change
        setInputValue('');
        setOtherMode(false);
        setSelectedMulti([]);
    }, [step]);

    useEffect(() => {
        if (otherMode && inputRef.current) {
            inputRef.current.focus();
        }
    }, [otherMode]);

    if (!step) return null;

    const { input_type, predicted_options } = step;

    const handleSubmit = () => {
        if (input_type === 'number' || input_type === 'number_pair') {
            onAnswer(inputValue);
        } else if (input_type === 'multi_choice') {
            const finalAnswers = [...selectedMulti];
            if (otherMode && inputValue) finalAnswers.push(inputValue);
            onAnswer(finalAnswers.join(', '));
        } else if (otherMode && inputValue) {
            onAnswer(inputValue);
        }
    };

    const handleOptionClick = (option) => {
        if (option === 'Other') {
            setOtherMode(true);
            return;
        }

        if (input_type === 'single_choice') {
            onAnswer(option);
        } else if (input_type === 'multi_choice') {
            setSelectedMulti(prev =>
                prev.includes(option) ? prev.filter(o => o !== option) : [...prev, option]
            );
        }
    };

    return (
        <div className="space-y-4">
            <AnimatePresence mode="wait">
                {/* Choice Options */}
                {(input_type === 'single_choice' || input_type === 'multi_choice') && !otherMode && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="grid grid-cols-1 sm:grid-cols-2 gap-2"
                    >
                        {predicted_options.map((option, idx) => {
                            const isSelected = selectedMulti.includes(option);
                            return (
                                <button
                                    key={idx}
                                    onClick={() => handleOptionClick(option)}
                                    disabled={disabled}
                                    className={`p-3 rounded-xl text-left transition-all flex items-center justify-between border ${isSelected
                                            ? 'bg-blue-600 border-blue-400 text-white shadow-[0_0_15px_rgba(37,99,235,0.2)]'
                                            : 'bg-slate-800 border-slate-700 hover:border-slate-500 text-slate-200'
                                        }`}
                                >
                                    <span className="font-medium">{option}</span>
                                    {isSelected ? <Check size={18} /> : <ChevronRight size={16} className="text-slate-500" />}
                                </button>
                            );
                        })}
                    </motion.div>
                )}

                {/* Other / text input */}
                {(otherMode || input_type === 'number' || input_type === 'number_pair') && (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex flex-col gap-2"
                    >
                        <div className="flex gap-2">
                            <input
                                ref={inputRef}
                                type={input_type.includes('number') ? 'number' : 'text'}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                placeholder={otherMode ? "Type your answer..." : "Enter value..."}
                                disabled={disabled}
                                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                                className="flex-1 bg-slate-800 border-2 border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-blue-500 transition-all"
                            />
                            <button
                                onClick={handleSubmit}
                                disabled={disabled || !inputValue}
                                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:bg-slate-700 text-white p-3 rounded-xl transition-all"
                            >
                                <ArrowRight size={24} />
                            </button>
                        </div>
                        {otherMode && (
                            <button
                                onClick={() => setOtherMode(false)}
                                className="text-xs text-slate-500 hover:text-slate-400 text-left px-2"
                            >
                                ← Back to options
                            </button>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Multi-choice Submit Button */}
            {input_type === 'multi_choice' && !otherMode && (
                <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    onClick={handleSubmit}
                    disabled={disabled || (selectedMulti.length === 0 && !inputValue)}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:bg-slate-700 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all"
                >
                    Continue <ArrowRight size={20} />
                </motion.button>
            )}
        </div>
    );
};

export default DynamicInputRenderer;
