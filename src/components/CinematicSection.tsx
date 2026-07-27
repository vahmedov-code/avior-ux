import React, { useRef } from 'react';
import { motion, useScroll, useSpring, useTransform, useMotionTemplate } from 'framer-motion';

export const CinematicSection: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start end', 'end start']
  });

  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 15,
    damping: 32,
    mass: 1.8
  });

  const yScaleValue = useTransform(smoothProgress, [0, 1], [60, -120]);
  const opacityValue = useTransform(smoothProgress, [0.3, 0.5], [0, 1]);

  const transformStyle = useMotionTemplate`perspective(400px) rotateX(24deg) translateY(${yScaleValue}px) translateZ(15px)`;

  return (
    <section ref={containerRef} className="relative w-full h-screen h-[100dvh] overflow-hidden bg-black flex items-center justify-center">
      <video
        src="/video2.mp4"
        className="absolute inset-0 w-full h-full object-cover z-0"
        autoPlay
        muted
        loop
        playsInline
      />

      <div 
        className="absolute top-0 left-0 w-full h-[180px] z-10 pointer-events-none"
        style={{ background: 'linear-gradient(to bottom, #010103, transparent)' }}
      />

      <div className="relative z-20 max-w-5xl px-6 sm:px-12 text-center">
        <motion.p
          style={{
            transform: transformStyle,
            opacity: opacityValue
          }}
          className="font-sans font-normal text-[22px] sm:text-[30px] md:text-[36px] lg:text-[42px] text-white leading-[1.35] tracking-[-0.02em] select-none"
        >
          A neural-AI interface built on the architecture of the human nervous system. SynapseX translates synaptic activity into computational intelligence. Every signal becomes measurable, structured, and visible. It continuously reconstructs internal state as a dynamic neural map. Biological noise is filtered into actionable cognitive patterns.
        </motion.p>
      </div>
    </section>
  );
};
