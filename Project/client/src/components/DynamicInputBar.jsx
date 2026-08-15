import React, { useState, useRef, useEffect } from 'react';
import ChipGroup from './ChipGroup';
import './DynamicInputBar.css';

function DynamicInputBar({ inputType, suggestedOptions, onSend, disabled }) {
    const [textValue, setTextValue] = useState('');
    const [selectedChips, setSelectedChips] = useState([]);
    const inputRef = useRef(null);

    // Reset state when suggested options change
    useEffect(() => {
        setTextValue('');
        setSelectedChips([]);
        if (inputRef.current) {
            inputRef.current.focus();
        }
    }, [suggestedOptions, inputType]);

    const handleTextSubmit = (e) => {
        e.preventDefault();
        if (textValue.trim() && !disabled) {
            onSend(textValue.trim());
            setTextValue('');
        }
    };

    const handleChipSingleSelect = (optionText) => {
        if (!disabled) {
            onSend(optionText);
        }
    };

    const handleChipMultiSubmit = () => {
        if (selectedChips.length > 0 && !disabled) {
            onSend(selectedChips.join(', '));
            setSelectedChips([]);
        }
    };

    // Format options for ChipGroup (which expects {label, value})
    // Since suggestedOptions are now plain strings, we map them
    const chipOptions = (suggestedOptions || []).map(opt => ({
        label: opt,
        value: opt
    }));

    return (
        <div className="input-bar">
            <div className="input-bar-container">
                {/* Chip Area */}
                {chipOptions.length > 0 && (
                    <div className="chips-area">
                        <ChipGroup
                            options={chipOptions}
                            selected={inputType === 'multi_select' ? selectedChips : null}
                            onSelect={inputType === 'multi_select' ? setSelectedChips : handleChipSingleSelect}
                            multiSelect={inputType === 'multi_select'}
                            onSubmit={inputType === 'multi_select' ? handleChipMultiSubmit : null}
                        />
                    </div>
                )}

                {/* Always show Text/Numeric Input */}
                <form className="input-bar-inner text-mode" onSubmit={handleTextSubmit}>
                    <input
                        ref={inputRef}
                        type={inputType === 'numeric' ? 'number' : 'text'}
                        inputMode={inputType === 'numeric' ? 'numeric' : 'text'}
                        value={textValue}
                        onChange={(e) => setTextValue(e.target.value)}
                        placeholder={
                            inputType === 'numeric'
                                ? 'Enter a number...'
                                : 'Type your message...'
                        }
                        disabled={disabled}
                        className="text-input"
                        autoFocus
                    />
                    <button
                        type="submit"
                        disabled={!textValue.trim() || disabled}
                        className="send-btn"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M22 2L11 13" />
                            <path d="M22 2L15 22L11 13L2 9L22 2Z" />
                        </svg>
                    </button>
                </form>
            </div>
        </div>
    );
}

export default DynamicInputBar;
