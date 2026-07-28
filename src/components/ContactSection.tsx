import React from 'react';
import { motion } from 'framer-motion';

export const ContactSection: React.FC = () => {
  return (
    <section id="contact" className="relative w-full min-h-screen bg-black flex items-center justify-center py-32 px-6">
      <div className="max-w-3xl w-full mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true, amount: 0.3 }}
          className="p-10 sm:p-16 border border-white/10 rounded-3xl bg-white/[0.02] backdrop-blur-xl"
        >
          <div className="text-[#33d17e] text-[13px] tracking-[0.2em] uppercase mb-4">
            // КОНТАКТЫ
          </div>
          <h2 className="text-white font-light text-[clamp(32px,5vw,52px)] leading-tight mb-6">
            Обсудим ваш сайт
          </h2>
          <p className="text-white/50 text-[15px] sm:text-[17px] leading-relaxed max-w-lg mx-auto mb-10">
            Расскажите, чем занимается ваш бизнес и что должен делать сайт — отвечу с честной оценкой объёма и сроков.
          </p>

          <a 
            href="https://t.me/ghost0590" 
            target="_blank" 
            rel="noreferrer"
            className="inline-flex items-center gap-3 px-8 py-4 bg-[#33d17e] text-black font-semibold rounded-full hover:bg-[#ffb15c] transition-colors text-[16px]"
          >
            <i className="bi bi-telegram text-[20px]"></i>
            <span>Написать в Telegram</span>
          </a>
        </motion.div>
      </div>
    </section>
  );
};
