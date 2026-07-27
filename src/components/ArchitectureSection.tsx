import React from 'react';
import { motion } from 'framer-motion';

export const ArchitectureSection: React.FC = () => {
  const layers = [
    { num: 'Layer 1', label: 'Capture' },
    { num: 'Layer 2', label: 'Process' },
    { num: 'Layer 3', label: 'Interface' },
  ];

  return (
    <section className="relative w-full min-h-screen bg-black flex items-center justify-center py-32 px-6">
      <div className="max-w-3xl w-full text-center">
        <motion.div
          initial={{ y: 30, opacity: 0 }}
          whileInView={{ y: 0, opacity: 1 }}
          transition={{ duration: 1.0 }}
          viewport={{ once: true, amount: 0.4 }}
        >
          <div className="text-white/40 text-[13px] sm:text-[14px] tracking-[0.2em] uppercase mb-8">
            Architecture
          </div>
          <h2 className="text-white font-light text-[clamp(28px,6vw,56px)] leading-[1.15] tracking-[-0.02em] mb-10">
            Three layers. Zero friction.
          </h2>
          <p className="text-white/45 text-[15px] sm:text-[17px] leading-relaxed max-w-xl mx-auto">
            Sensor layer captures raw bioelectric signals. Processing layer isolates intent. Interface layer delivers structured output to any connected system.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 1.2, delay: 0.4 }}
          viewport={{ once: true, amount: 0.4 }}
          className="mt-20 flex flex-col items-center gap-4"
        >
          {layers.map((layer, i) => (
            <div
              key={i}
              className="w-full max-w-md h-[72px] border border-white/10 rounded-lg flex items-center justify-between px-6 bg-white/[0.02]"
            >
              <span className="text-white/30 text-[12px] tracking-[0.15em] uppercase">
                {layer.num}
              </span>
              <span className="text-white text-[16px] sm:text-[18px] font-light">
                {layer.label}
              </span>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};
