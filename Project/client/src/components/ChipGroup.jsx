import React from 'react';
import './ChipGroup.css';

function ChipGroup({ options, selected, onSelect, multiSelect = false, onSubmit }) {
    const handleClick = (option) => {
        if (multiSelect) {
            const val = option.value;
            if (selected.includes(val)) {
                onSelect(selected.filter(v => v !== val));
            } else {
                onSelect([...selected, val]);
            }
        } else {
            onSelect(option.value);
        }
    };

    return (
        <div className="chip-group-wrapper">
            <div className="chip-group">
                {options.map((opt) => {
                    const isActive = multiSelect
                        ? selected.includes(opt.value)
                        : selected === opt.value;

                    return (
                        <button
                            key={opt.value}
                            className={`chip ${isActive ? 'chip-active' : ''}`}
                            onClick={() => handleClick(opt)}
                            type="button"
                        >
                            {opt.label}
                        </button>
                    );
                })}
            </div>
            {multiSelect && (
                <button
                    className="chip-send-btn"
                    onClick={onSubmit}
                    disabled={selected.length === 0}
                    type="button"
                >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M22 2L11 13" />
                        <path d="M22 2L15 22L11 13L2 9L22 2Z" />
                    </svg>
                    Send
                </button>
            )}
        </div>
    );
}

export default ChipGroup;
