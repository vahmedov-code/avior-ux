import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ScrambleIn } from './ScrambleIn';
import { Warp } from '@paper-design/shaders-react';

export const ContactSection: React.FC = () => {
  const [headingTriggered, setHeadingTriggered] = useState(false);
  return (
    <section id="contact" className="relative w-full min-h-screen bg-black flex items-center justify-center py-32 px-6 overflow-hidden">
      <video
        src="/video2.mp4"
        className="absolute inset-0 w-full h-full object-cover z-0 opacity-25"
        autoPlay
        muted
        loop
        playsInline
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-black/60 via-black/40 to-black/80" />

      <div className="relative z-10 max-w-3xl w-full mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          onViewportEnter={() => setHeadingTriggered(true)}
          transition={{ duration: 0.8 }}
          viewport={{ once: true, amount: 0.3 }}
          className="relative overflow-hidden p-10 sm:p-16 border border-white/10 rounded-3xl bg-white/[0.02] backdrop-blur-xl"
        >
          <div className="absolute inset-0 z-0 opacity-25">
            <Warp
              style={{ height: '100%', width: '100%' }}
              proportion={0.35}
              softness={1.3}
              distortion={0.12}
              swirl={0.5}
              swirlIterations={6}
              shape="checks"
              shapeScale={0.08}
              scale={1}
              rotation={0}
              speed={0.35}
              colors={['hsl(152, 63%, 12%)', 'hsl(152, 70%, 52%)', 'hsl(35, 100%, 60%)', 'hsl(210, 25%, 8%)']}
            />
          </div>
          <div className="absolute inset-0 z-0 bg-black/40" />

          <div className="relative z-10">
            <div className="text-[#33d17e] text-[13px] tracking-[0.2em] uppercase mb-4">
              // КОНТАКТЫ
            </div>
            <h2 className="text-white font-light text-[clamp(32px,5vw,52px)] leading-tight mb-6">
              <ScrambleIn text="Обсудим ваш сайт" delay={100} triggered={headingTriggered} />
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
          </div>
        </motion.div>
      </div>
    </section>
  );
};
