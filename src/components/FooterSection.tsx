import React from 'react';
import { AviorLogo } from './AviorLogo';

export const FooterSection: React.FC = () => {
  return (
    <footer className="w-full bg-black border-t border-white/10 py-12 px-6 sm:px-12">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-6 text-[13px] text-white/40 font-mono">
        <div className="flex items-center gap-3">
          <AviorLogo className="text-[16px]" />
          <span>© 2026 AVIOR UX</span>
        </div>
        <div>
          ux.avior.moscow
        </div>
      </div>
    </footer>
  );
};
