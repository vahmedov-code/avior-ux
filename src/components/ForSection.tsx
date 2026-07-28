import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ScrambleIn } from './ScrambleIn';

export const ForSection: React.FC = () => {
  const [headingTriggered, setHeadingTriggered] = useState(false);
  const items = [
    {
      num: '01',
      title: 'Мастера-одиночки',
      desc: 'Ремонт, услуги на дому, частная практика — там, где вы сами и мастер, и приёмщик, и бухгалтер.'
    },
    {
      num: '02',
      title: 'Малый бизнес',
      desc: 'Небольшая команда без штатного разработчика, которой нужен рабочий сайт, а не эксперимент на годы.'
    },
    {
      num: '03',
      title: 'Тем, кого уже подводили',
      desc: 'Если был опыт с агентством, которое взяло деньги и пропало — здесь работаем иначе, с понятным объёмом и сроком.'
    }
  ];

  return (
    <section id="for" className="relative w-full min-h-screen bg-black flex items-center justify-center py-32 px-6">
      <video
        src="/video2.mp4"
        className="absolute inset-0 w-full h-full object-cover z-0 opacity-20"
        autoPlay
        muted
        loop
        playsInline
      />

      <div className="relative z-10 max-w-6xl w-full mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          onViewportEnter={() => setHeadingTriggered(true)}
          transition={{ duration: 0.8 }}
          viewport={{ once: true, amount: 0.3 }}
          className="mb-16"
        >
          <div className="text-[#33d17e] text-[13px] tracking-[0.2em] uppercase mb-3">
            // ДЛЯ КОГО ЭТО
          </div>
          <h2 className="text-white font-light text-[clamp(28px,5vw,46px)] leading-tight max-w-2xl">
            <ScrambleIn text="Для тех, кто сам держит бизнес на себе" delay={100} triggered={headingTriggered} />
          </h2>
          <p className="text-white/50 text-[15px] mt-4 max-w-xl leading-relaxed">
            Не для стартапов с раундом инвестиций. Для тех, кто хочет, чтобы сайт реально приводил клиентов, а не просто был «для галочки».
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {items.map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: i * 0.15 }}
              viewport={{ once: true, amount: 0.3 }}
              className="p-8 border border-white/10 rounded-xl bg-white/[0.03] backdrop-blur-md hover:border-[#33d17e]/50 transition-colors flex flex-col justify-between"
            >
              <div>
                <div className="text-[#33d17e] text-[14px] font-mono mb-4">{item.num}</div>
                <h3 className="text-white text-[20px] font-semibold mb-3">{item.title}</h3>
                <p className="text-white/50 text-[14px] leading-relaxed">{item.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
