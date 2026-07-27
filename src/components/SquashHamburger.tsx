import React from 'react';
import { motion } from 'framer-motion';

interface SquashHamburgerProps {
  isOpen: boolean;
  onClick?: () => void;
  isMobile?: boolean;
}

export const SquashHamburger: React.FC<SquashHamburgerProps> = ({ isOpen, onClick, isMobile = false }) => {
  const springConfig = { type: 'spring', stiffness: 300, damping: 20 };
  const widthClass = isMobile ? 'w-[15px] h-[10px]' : 'w-[18px] h-[12px]';
  const barHeight = isMobile ? 1.2 : 1.5;

  return (
    <button 
      onClick={onClick} 
      className={`relative flex flex-col justify-between items-center ${widthClass} focus:outline-none`}
      aria-label="Toggle navigation"
    >
      <motion.span
        style={{ height: `${barHeight}px` }}
        className="w-full bg-white rounded-full block origin-center"
        animate={isOpen ? { rotate: 45, y: isMobile ? 4.4 : 5.25 } : { rotate: 0, y: 0 }}
        transition={springConfig}
      />
      <motion.span
        style={{ height: `${barHeight}px` }}
        className="w-full bg-white rounded-full block"
        animate={isOpen ? { opacity: 0, scaleX: 0 } : { opacity: 1, scaleX: 1 }}
        transition={springConfig}
      />
      <motion.span
        style={{ height: `${barHeight}px` }}
        className="w-full bg-white rounded-full block origin-center"
        animate={isOpen ? { rotate: -45, y: isMobile ? -4.4 : -5.25 } : { rotate: 0, y: 0 }}
        transition={springConfig}
      />
    </button>
  );
};
