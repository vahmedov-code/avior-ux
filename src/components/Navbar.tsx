import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AviorLogo } from './AviorLogo';
import { SquashHamburger } from './SquashHamburger';
import { ScrambleText } from './ScrambleText';

interface NavbarProps {
  entranceComplete: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ entranceComplete }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [hoveredLink, setHoveredLink] = useState<string | null>(null);
  const [isCtaHovered, setIsCtaHovered] = useState(false);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
    setIsMenuOpen(false);
  };

  return (
    <motion.header 
      initial={{ opacity: 0 }}
      animate={{ opacity: entranceComplete ? 1 : 0 }}
      transition={{ duration: 0.8 }}
      className="fixed top-0 left-0 w-full h-20 z-50 pointer-events-auto px-4 sm:px-8 flex items-center justify-between"
    >
      {/* DESKTOP */}
      <div className="hidden sm:flex items-center gap-2">
        <motion.div 
          whileHover={{ scale: 1.02, backgroundColor: 'rgba(255, 255, 255, 0.22)' }}
          whileTap={{ scale: 0.98 }}
          className="h-12 px-5 bg-white/15 backdrop-blur-md border border-white/10 rounded-[14px] flex items-center gap-3 cursor-pointer select-none transition-colors"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        >
          <AviorLogo className="text-[16px]" />
        </motion.div>

        <motion.div 
          animate={{ width: isMenuOpen ? 460 : 48 }}
          transition={{ type: 'spring', stiffness: 350, damping: 28 }}
          className="h-12 bg-white/15 backdrop-blur-md border border-white/10 rounded-[14px] flex items-center overflow-hidden"
        >
          <button 
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className={`transition-all duration-300 flex items-center justify-center ${
              isMenuOpen ? 'w-9 h-9 bg-white/10 hover:bg-white/20 rounded-[11px] ml-1.5' : 'w-12 h-12 rounded-[14px]'
            }`}
          >
            <SquashHamburger isOpen={isMenuOpen} />
          </button>

          <AnimatePresence>
            {isMenuOpen && (
              <motion.div 
                initial={{ opacity: 0, x: 15 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 15 }}
                transition={{ duration: 0.2 }}
                className="flex items-center gap-5 ml-4 whitespace-nowrap"
              >
                {[
                  { id: 'for', label: 'Для кого' },
                  { id: 'case', label: 'Кейс' },
                  { id: 'services', label: 'Услуги' },
                  { id: 'process', label: 'Как строим' },
                  { id: 'contact', label: 'Контакты' },
                ].map((item) => (
                  <button 
                    key={item.id}
                    onClick={() => scrollTo(item.id)}
                    onMouseEnter={() => setHoveredLink(item.id)}
                    onMouseLeave={() => setHoveredLink(null)}
                    className="text-[14px] font-normal text-white/85 hover:text-white transition-colors"
                  >
                    <ScrambleText text={item.label} isHovered={hoveredLink === item.id} />
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* MOBILE */}
      <div className="flex sm:hidden items-center justify-between w-full">
        <div className="flex items-center gap-1.5 flex-1 pr-2">
          <motion.div 
            animate={{ width: isMenuOpen ? 0 : 'auto', opacity: isMenuOpen ? 0 : 1, paddingLeft: isMenuOpen ? 0 : 12, paddingRight: isMenuOpen ? 0 : 12 }}
            transition={{ type: 'spring', stiffness: 350, damping: 28 }}
            className="h-9 bg-white/15 backdrop-blur-md rounded-[10px] flex items-center gap-2 overflow-hidden cursor-pointer whitespace-nowrap"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          >
            <AviorLogo className="text-[13px]" />
          </motion.div>

          <motion.div 
            animate={{ width: isMenuOpen ? '100%' : 36 }}
            transition={{ type: 'spring', stiffness: 350, damping: 28 }}
            className="h-9 bg-white/15 backdrop-blur-md rounded-[10px] flex items-center overflow-hidden"
          >
            <button 
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className={`flex items-center justify-center transition-all ${
                isMenuOpen ? 'w-7 h-7 bg-white/10 rounded-[7px] ml-1' : 'w-9 h-9'
              }`}
            >
              <SquashHamburger isOpen={isMenuOpen} isMobile={true} />
            </button>

            {isMenuOpen && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-3 ml-2 text-[12px] whitespace-nowrap overflow-x-auto"
              >
                <button onClick={() => scrollTo('for')}>Для кого</button>
                <button onClick={() => scrollTo('case')}>Кейс</button>
                <button onClick={() => scrollTo('services')}>Услуги</button>
                <button onClick={() => scrollTo('contact')}>Контакты</button>
              </motion.div>
            )}
          </motion.div>
        </div>

        <motion.button 
          whileTap={{ scale: 0.95 }}
          onClick={() => scrollTo('contact')}
          className="h-9 px-3.5 bg-[#33d17e] text-black rounded-full flex items-center gap-1 text-[12px] font-semibold flex-shrink-0"
        >
          <span>Обсудить</span>
        </motion.button>
      </div>

      {/* DESKTOP CTA */}
      <motion.button 
        whileHover={{ scale: 1.03, backgroundColor: '#ffb15c' }}
        whileTap={{ scale: 0.97 }}
        onMouseEnter={() => setIsCtaHovered(true)}
        onMouseLeave={() => setIsCtaHovered(false)}
        onClick={() => scrollTo('contact')}
        className="hidden sm:flex h-12 px-6 bg-[#33d17e] text-black rounded-full items-center gap-2 text-[14px] font-semibold cursor-pointer transition-colors"
      >
        <i className="bi bi-telegram text-[16px]"></i>
        <ScrambleText text="Обсудить сайт" isHovered={isCtaHovered} />
      </motion.button>
    </motion.header>
  );
};
