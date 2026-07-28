import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ScrambleIn } from './ScrambleIn';

export const ProcessSection: React.FC = () => {
  const [headingTriggered, setHeadingTriggered] = useState(false);
  const steps = [
    {
      num: '01',
      title: 'Диагностика',
      desc: 'Обсуждаем, что должен решать сайт: заявки, витрину, автоматизацию рутины.'
    },
    {
      num: '02',
      title: 'Дизайн',
      desc: 'Макет под конкретно ваш бизнес — не шаблон с заменённым логотипом.'
    },
    {
      num: '03',
      title: 'Сборка',
      desc: 'Вёрстка, формы, интеграции, скорость загрузки — всё, что реально работает.'
    },
    {
      num: '04',
      title: 'Запуск',
      desc: 'Домен, хостинг, доступ к правкам — сайт остаётся вашим, а не заложником разработчика.'
    }
  ];

  return (
    <section id="process" className="relative w-full min-h-screen bg-black flex items-center justify-center py-32 px-6">
      <div className="max-w-6xl w-full mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          onViewportEnter={() => setHeadingTriggered(true)}
          transition={{ duration: 0.8 }}
          viewport={{ once: true, amount: 0.3 }}
          className="mb-16"
        >
          <div className="text-[#33d17e] text-[13px] tracking-[0.2em] uppercase mb-3">
            // КАК СТРОИМ
          </div>
          <h2 className="text-white font-light text-[clamp(28px,5vw,46px)] leading-tight">
            <ScrambleIn text="Четыре стадии. Без сюрпризов." delay={100} triggered={headingTriggered} />
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: i * 0.1 }}
              viewport={{ once: true, amount: 0.3 }}
              className="p-6 border-t-2 border-[#33d17e] bg-white/[0.02] border-x border-b border-white/10 rounded-b-xl"
            >
              <div className="text-[#33d17e] text-[14px] font-mono mb-3">{step.num}</div>
              <h3 className="text-white text-[18px] font-semibold mb-2">{step.title}</h3>
              <p className="text-white/50 text-[13px] leading-relaxed">{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
