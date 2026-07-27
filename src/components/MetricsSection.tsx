import React from 'react';
import { motion } from 'framer-motion';

export const MetricsSection: React.FC = () => {
  const metrics = [
    { value: '2.4ms', label: 'Synaptic Latency' },
    { value: '99.7%', label: 'Signal Accuracy' },
    { value: '140B', label: 'Neural Parameters' }
  ];

  return (
    <section className="relative w-full min-h-screen overflow-hidden bg-black flex items-center justify-center py-32 px-6">
      <video
        src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260622_095810_ecea3dd2-fc5e-4e41-8696-4219290b6589.mp4"
        className="absolute inset-0 w-full h-full object-cover z-0"
        autoPlay
        muted
        loop
        playsInline
      />

      <div className="relative z-10 max-w-6xl w-full mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 1.2 }}
          viewport={{ once: true, amount: 0.3 }}
          className="text-white/40 text-[13px] sm:text-[14px] tracking-[0.2em] uppercase mb-20 text-center"
        >
          Performance Metrics
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-16 md:gap-8 text-center">
          {metrics.map((metric, i) => (
            <motion.div
              key={i}
              initial={{ y: 30, opacity: 0 }}
              whileInView={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.8, delay: i * 0.15 }}
              viewport={{ once: true, amount: 0.3 }}
              className="flex flex-col items-center"
            >
              <div className="text-white text-[clamp(48px,10vw,96px)] font-light tracking-[-0.04em] leading-none">
                {metric.value}
              </div>
              <div className="text-white/40 text-[13px] sm:text-[15px] mt-4 tracking-wide">
                {metric.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
