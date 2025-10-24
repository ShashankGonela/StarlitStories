/**
 * FlipCard Component
 * 
 * Displays a story with a 3D flip animation to reveal the moral.
 * - Front: Story text
 * - Back: Moral summary with glowing typography
 * - Flip trigger: Right-click (or long-press on mobile)
 */

import { useState, useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';

interface FlipCardProps {
  title: string;
  story: string;
  moral: string;
}

export const FlipCard: React.FC<FlipCardProps> = ({ title, story, moral }) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const [longPressTimer, setLongPressTimer] = useState<NodeJS.Timeout | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  // Handle right-click to flip
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsFlipped(!isFlipped);
  };

  // Handle touch start for mobile long-press
  const handleTouchStart = () => {
    const timer = setTimeout(() => {
      setIsFlipped(!isFlipped);
    }, 500); // 500ms long press
    setLongPressTimer(timer);
  };

  // Clear timer on touch end
  const handleTouchEnd = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (longPressTimer) {
        clearTimeout(longPressTimer);
      }
    };
  }, [longPressTimer]);

  return (
    <div 
      className="flip-card-container perspective"
      onContextMenu={handleContextMenu}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      ref={cardRef}
    >
      <div className={`flip-card ${isFlipped ? 'flipped' : ''}`} style={{ minHeight: 'auto' }}>
        {/* Front Side - Story */}
        <div className="flip-card-front" style={{ position: isFlipped ? 'absolute' : 'relative', minHeight: 'auto' }}>
          <div className="message-bubble assistant-message w-full max-w-none fade-in">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl md:text-3xl font-bold text-[#FFD369] glow-text-soft">
                {title}
              </h2>
              <div className="text-[#B9AFFF] text-xs italic opacity-70 hidden md:block">
                Right-click to reveal moral ✨
              </div>
              <div className="text-[#B9AFFF] text-xs italic opacity-70 md:hidden">
                Long-press for moral ✨
              </div>
            </div>
            <p className="text-[#F2F2F7] leading-relaxed whitespace-pre-wrap text-base md:text-lg">
              {story}
            </p>
          </div>
        </div>

        {/* Back Side - Moral */}
        <div className="flip-card-back" style={{ position: isFlipped ? 'relative' : 'absolute', minHeight: 'auto' }}>
          <div className="message-bubble moral-card w-full max-w-none fade-in">
            <div className="flex items-center gap-3 mb-6">
              <Sparkles className="text-[#FFD369]" size={28} />
              <h3 className="text-2xl md:text-3xl font-bold text-[#FFD369] glow-text-strong">
                The Moral
              </h3>
              <Sparkles className="text-[#FFD369]" size={28} />
            </div>
            <p className="text-[#F2F2F7] leading-relaxed text-lg md:text-xl font-medium moral-glow">
              {moral}
            </p>
            <div className="text-[#B9AFFF] text-sm italic opacity-70 mt-6 text-center">
              Right-click again to see the story ✨
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
