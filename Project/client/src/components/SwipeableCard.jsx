import React, { useState, useRef, useCallback } from 'react';
import './SwipeableCard.css';

function SwipeableCard({ children, onSwipeRight, className = '', pinLabel = 'Pin' }) {
    const [translateX, setTranslateX] = useState(0);
    const [isSwiping, setIsSwiping] = useState(false);
    const [isPinned, setIsPinned] = useState(false);
    const startXRef = useRef(0);
    const startYRef = useRef(0);
    const isHorizontalRef = useRef(null); // null = undecided, true = horizontal, false = vertical
    const SWIPE_THRESHOLD = 70;

    const handleTouchStart = useCallback((e) => {
        startXRef.current = e.touches[0].clientX;
        startYRef.current = e.touches[0].clientY;
        isHorizontalRef.current = null;
        setIsSwiping(true);
    }, []);

    const handleTouchMove = useCallback((e) => {
        if (!isSwiping) return;

        const deltaX = e.touches[0].clientX - startXRef.current;
        const deltaY = e.touches[0].clientY - startYRef.current;

        // Decide direction on first significant move
        if (isHorizontalRef.current === null) {
            if (Math.abs(deltaX) > 8 || Math.abs(deltaY) > 8) {
                isHorizontalRef.current = Math.abs(deltaX) > Math.abs(deltaY);
            }
            return;
        }

        // If vertical scroll, bail out
        if (!isHorizontalRef.current) return;

        // Only allow swiping right, with resistance curve
        if (deltaX > 0) {
            const dampened = deltaX * 0.6; // Resistance
            setTranslateX(Math.min(dampened, 100));
        }
    }, [isSwiping]);

    const handleTouchEnd = useCallback(() => {
        if (translateX >= SWIPE_THRESHOLD) {
            // Flash the pinned state briefly
            setIsPinned(true);
            setTimeout(() => setIsPinned(false), 600);
            if (onSwipeRight) onSwipeRight();
        }
        setIsSwiping(false);
        setTranslateX(0);
    }, [translateX, onSwipeRight]);

    // Swipe progress (0 to 1) for opacity interpolation
    const progress = Math.min(translateX / SWIPE_THRESHOLD, 1);
    const isActive = isSwiping && translateX > 5;

    return (
        <div 
            className={`swipeable-wrapper ${className} ${isPinned ? 'just-pinned' : ''}`}
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
        >
            {/* Action indicator — only visible during swipe */}
            <div 
                className="swipe-action-bg"
                style={{ opacity: isActive ? progress * 0.9 : 0 }}
            >
                <div className={`swipe-action-icon ${progress >= 1 ? 'ready' : ''}`}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="12" y1="17" x2="12" y2="22"></line>
                        <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.68V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3v4.68a2 2 0 0 1-1.11 1.87l-1.78.89A2 2 0 0 0 5 15.24Z"></path>
                    </svg>
                </div>
                {progress >= 0.5 && (
                    <span className="swipe-action-label" style={{ opacity: (progress - 0.5) * 2 }}>
                        {pinLabel}
                    </span>
                )}
            </div>

            <div 
                className={`swipe-content ${isSwiping && isHorizontalRef.current ? 'swiping' : ''}`}
                style={{ 
                    transform: `translateX(${translateX}px)`,
                    ...(isActive ? { borderColor: `rgba(0, 229, 255, ${progress * 0.3})` } : {})
                }}
            >
                {/* Desktop hover pin button */}
                <button 
                    className="desktop-pin-btn" 
                    onClick={(e) => {
                        e.stopPropagation();
                        setIsPinned(true);
                        setTimeout(() => setIsPinned(false), 600);
                        if (onSwipeRight) onSwipeRight();
                    }}
                    title="Pin to Chat"
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="12" y1="17" x2="12" y2="22"></line>
                        <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.68V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3v4.68a2 2 0 0 1-1.11 1.87l-1.78.89A2 2 0 0 0 5 15.24Z"></path>
                    </svg>
                </button>
                {children}
            </div>
        </div>
    );
}

export default SwipeableCard;
