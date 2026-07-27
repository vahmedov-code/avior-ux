import React from 'react';

export const AviorLogo: React.FC<{ className?: string }> = ({ className = "w-4 h-4" }) => {
  return (
    <div className={`flex items-center gap-1 font-bold tracking-tight text-white ${className}`}>
      <span>AVIOR</span>
      <span className="text-[#33d17e]">UX</span>
    </div>
  );
};
