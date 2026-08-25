import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ScrambleIn } from './ScrambleIn';
import { Warp } from '@paper-design/shaders-react';

interface HeroSectionProps {
  onEntranceComplete: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onEntranceComplete }) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [entranceComplete, setEntranceComplete] = useState(false);
  const isSeeking = useRef(false);
  const lastXRef = useRef<number | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setEntranceComplete(true);
      onEntranceComplete();
    }, 800);
    return () => clearTimeout(timer);
  }, [onEntranceComplete]);

  // Интерактивная перемотка видео мышью (Scrubbing)
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    video.pause();

    const handleSeeked = () => {
      isSeeking.current = false;
    };

    video.addEventListener('seeked', handleSeeked);

    const handleMouseMove = (e: MouseEvent) => {
      if (lastXRef.current === null) {
        lastXRef.current = e.clientX;
        return;
      }

      const deltaX = e.clientX - lastXRef.current;
      lastXRef.current = e.clientX;

      if (video.duration && !isSeeking.current) {
        const sensitivity = 0.8;
        const deltaSec = (deltaX / window.innerWidth) * video.duration * sensitivity;
        let newTime = video.currentTime + deltaSec;

        if (newTime < 0) newTime = 0;
        if (newTime > video.duration) newTime = video.duration;

        isSeeking.current = true;
        video.currentTime = newTime;
      }
    };

    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      video.removeEventListener('seeked', handleSeeked);
    };
  }, []);

  return (
    <section className="relative w-full min-h-screen overflow-hidden flex flex-col justify-between pt-24 pb-12 px-4 sm:px-8 select-none">
      {/* Видео, управляемое мышью */}
      <video
        ref={videoRef}
        src="/video1.mp4"
        className="absolute inset-0 w-full h-full object-cover z-0 opacity-40 pointer-events-none"
        muted
        playsInline
      />

      {/* Точечный сетчатый оверлей */}
      <div 
        className="absolute inset-0 z-10 pointer-events-none opacity-10"
        style={{
          backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)',
          backgroundSize: '24px 24px'
        }}
      />

      {/* Фоновый водяной знак */}
      <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none translate-y-[20px]">
        <div
          aria-hidden="true"
          className="font-watermark uppercase tracking-[-4px] opacity-10 text-[clamp(100px,25vw,450px)] leading-none text-center"
          style={{
            backgroundImage: 'radial-gradient(circle, rgba(51,209,126,0.3) 0%, #33d17e 70%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}
        >
          AVIOR UX
        </div>
      </div>

      {/* Контент Hero */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: entranceComplete ? 1 : 0 }}
        transition={{ duration: 1.0 }}
        className="relative z-20 max-w-6xl mx-auto w-full flex-1 flex flex-col justify-center my-auto"
      >
        <div className="text-[#33d17e] text-[12px] sm:text-[14px] tracking-[0.2em] uppercase font-mono mb-6">
          // Сайты для мастеров и малого бизнеса
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Левый блок с заглавием */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            <h1 className="text-white font-light leading-[1.05] tracking-[-0.03em] text-[32px] sm:text-[42px] md:text-[52px]">
              <ScrambleIn text="Сайт, который приводит клиентов —" delay={200} triggered={entranceComplete} />
              <br />
              <span className="text-white/80">
                <ScrambleIn text="а не просто существует в интернете" delay={700} triggered={entranceComplete} />
              </span>
            </h1>

            <motion.p 
              initial={{ y: 25, opacity: 0 }}
              animate={entranceComplete ? { y: 0, opacity: 1 } : {}}
              transition={{ duration: 0.9, delay: 0.4 }}
              className="text-[14px] sm:text-[16px] text-white/60 leading-relaxed max-w-xl"
            >
              Строю сайты под ключ: от лендинга до сайта с админкой и интеграциями. Тот же принцип, что и в ремонте техники — сначала честный разбор задачи, потом цена, без сюрпризов в процессе.
            </motion.p>

            <div className="flex flex-wrap gap-4 pt-4">
              <a 
                href="#contact" 
                className="px-6 py-3.5 bg-[#33d17e] text-black font-semibold rounded-lg hover:bg-[#ffb15c] transition-colors text-[14px]"
              >
                Обсудить сайт
              </a>
              <a 
                href="#case" 
                className="px-6 py-3.5 border border-white/20 text-white rounded-lg hover:border-white/50 transition-colors text-[14px]"
              >
                Смотреть пример работы
              </a>
            </div>
          </div>

          {/* Правый блок (Карточка ЗАЯВКА UX-047) */}
          <div className="lg:col-span-5">
            <motion.div 
              initial={{ y: 30, opacity: 0 }}
              animate={entranceComplete ? { y: 0, opacity: 1 } : {}}
              transition={{ duration: 0.9, delay: 0.6 }}
              className="relative rounded-xl overflow-hidden shadow-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl font-mono"
            >
              {/* Анимированный шейдер-фон в фирменной палитре */}
              <div className="absolute inset-0 z-0 opacity-30">
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
                  speed={0.4}
                  colors={['hsl(152, 63%, 12%)', 'hsl(152, 65%, 51%)', 'hsl(30, 100%, 68%)', 'hsl(210, 25%, 8%)']}
                />
              </div>
              <div className="absolute inset-0 z-0 bg-[#0e1218]/40" />

              <div className="relative z-10 p-5 border-b border-dashed border-white/15 flex justify-between items-start">
                <div>
                  <div className="text-[11px] text-white/40 tracking-widest">ЗАЯВКА</div>
                  <div className="text-[18px] font-bold text-white">UX-047</div>
                </div>
                <div className="text-[11px] font-bold border-2 border-[#33d17e] text-[#33d17e] px-2 py-1 rounded -rotate-3 uppercase tracking-wider bg-[#0e1218]/60">
                  В РАБОТЕ
                </div>
              </div>

              <div className="relative z-10 p-5 space-y-3 text-[13px]">
                <div className="flex items-center gap-3">
                  <span className="w-4 h-4 bg-[#33d17e] text-[#0e1218] rounded flex items-center justify-center text-[10px] font-bold">✓</span>
                  <span className="text-white font-medium">Адаптивная вёрстка под все экраны</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="w-4 h-4 bg-[#33d17e] text-[#0e1218] rounded flex items-center justify-center text-[10px] font-bold">✓</span>
                  <span className="text-white font-medium">SEO-структура и микроразметка</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="w-4 h-4 bg-[#33d17e] text-[#0e1218] rounded flex items-center justify-center text-[10px] font-bold">✓</span>
                  <span className="text-white font-medium">Форма заявок с уведомлениями</span>
                </div>
                <div className="flex items-center gap-3 text-white/40">
                  <span className="w-4 h-4 border border-white/30 rounded"></span>
                  <span>Админка для самостоятельных правок</span>
                </div>
                <div className="flex items-center gap-3 text-white/40">
                  <span className="w-4 h-4 border border-white/30 rounded"></span>
                  <span>Интеграции: CRM, боты, аналитика</span>
                </div>
              </div>

              <div className="relative z-10 p-4 border-t border-white/15 flex justify-between text-[11px] text-white/40 bg-black/20">
                <span>СРОК: 5–14 ДНЕЙ</span>
                <span>МАСТЕР: ВЕЙС</span>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </section>
  );
};