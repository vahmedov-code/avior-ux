import React from 'react';
import { motion } from 'framer-motion';

export const TechSection: React.FC = () => {
  const items = [
    { title: 'Cortical Mapping', desc: 'Real-time spatial reconstruction of active neural regions.' },
    { title: 'Signal Isolation', desc: 'Separates cognitive intent from biological noise.' },
    { title: 'State Prediction', desc: 'Anticipates cognitive transitions before they occur.' },
    { title: 'Loop Feedback', desc: 'Closed-loop adjustment based on outcome correlation.' }
  ];

  return (
    <section className="relative w-full h-screen h-[100dvh] overflow-hidden bg-black flex flex-col justify-between px-8 sm:px-12 md:px-16 py-12 sm:py-16">
      <video
        src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260622_095750_32a52ce0-2005-45c9-9093-41f03fde9530.mp4"
        className="absolute inset-0 w-full h-full object-cover z-0"
        autoPlay
        muted
        loop
        playsInline
      />

      <div className="relative z-10 flex flex-col md:flex-row md:justify-between md:items-start gap-6">
        <motion.h2
          initial={{ y: 40, opacity: 0 }}
          whileInView={{ y: 0, opacity: 1 }}
          transition={{ duration: 1.0 }}
          viewport={{ once: true, amount: 0.3 }}
          className="text-white font-light text-[clamp(36px,8vw,72px)] leading-[0.95] tracking-[-0.03em]"
        >
          Adaptive /<br />Intelligence
        </motion.h2>

        <motion.p
          initial={{ y: 20, opacity: 0 }}
          whileInView={{ y: 0, opacity: 1 }}
          transition={{ duration: 1.0, delay: 0.2 }}
          viewport={{ once: true, amount: 0.3 }}
          className="text-white/50 text-[13px] sm:text-[15px] leading-relaxed max-w-xs md:text-right md:pt-2"
        >
          The system learns your neural baseline within 72 hours. From there, every cognitive state is mapped, predicted, and optimized in real time.
        </motion.p>
      </div>

      <div className="flex-1" />

      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 1.0, delay: 0.3 }}
        viewport={{ once: true, amount: 0.3 }}
        className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-6"
      >
        {items.map((item, i) => (
          <motion.div
            key={i}
            initial={{ y: 20, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.7, delay: i * 0.1 }}
            viewport={{ once: true, amount: 0.3 }}
          >
            <h3 className="text-white text-[14px] sm:text-[16px] font-normal mb-2">
              {item.title}
            </h3>
            <p className="text-white/40 text-[12px] sm:text-[14px] leading-relaxed">
              {item.desc}
            </p>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
};
