import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ScrambleIn } from './ScrambleIn';

export const ServicesSection: React.FC = () => {
  const [headingTriggered, setHeadingTriggered] = useState(false);
  const tiers = [
    {
      tag: 'Уровень 1',
      title: 'Лендинг',
      price: 'от 25 000 ₽',
      popular: false,
      features: [
        'Одна страница под ваш бизнес',
        'Адаптивная вёрстка под мобильные',
        'Форма приема заявок в Telegram',
        'Базовая SEO-оптимизация'
      ]
    },
    {
      tag: 'Уровень 2 · Популярно',
      title: 'Лендинг + админка',
      price: 'от 55 000 ₽',
      popular: true,
      features: [
        'Всё из уровня 1',
        'Несколько страниц (услуги, о вас)',
        'Своя админка — правите тексты и цены сами',
        'Интеграция с картами и мессенджерами'
      ]
    },
    {
      tag: 'Уровень 3',
      title: 'Полный цикл',
      price: 'от 120 000 ₽',
      popular: false,
      features: [
        'Всё из уровня 2',
        'Интеграции: CRM, боты, аналитика',
        'Автоматизация заявок и уведомлений',
        'Полное сопровождение после запуска'
      ]
    }
  ];

  return (
    <section id="services" className="relative w-full min-h-screen bg-black flex items-center justify-center py-32 px-6">
      <video
        src="/video4.mp4"
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
            // УРОВНИ СБОРКИ
          </div>
          <h2 className="text-white font-light text-[clamp(28px,5vw,46px)] leading-tight">
            <ScrambleIn text="Выбирайте нужную глубину" delay={100} triggered={headingTriggered} />
          </h2>
          <p className="text-white/50 text-[15px] mt-4 max-w-xl leading-relaxed">
            Каждый следующий уровень включает предыдущий. Стартуете с малого — доращиваете, когда бизнес готов.
          </p>
        </motion.div>

        {/* Tiers Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {tiers.map((tier, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: i * 0.15 }}
              viewport={{ once: true, amount: 0.3 }}
              className={`p-8 rounded-2xl flex flex-col justify-between backdrop-blur-md transition-colors ${
                tier.popular 
                  ? 'bg-white/[0.06] border-2 border-[#33d17e]' 
                  : 'bg-white/[0.02] border border-white/10'
              }`}
            >
              <div>
                <div className={`text-[12px] uppercase tracking-wider mb-3 ${tier.popular ? 'text-[#33d17e] font-semibold' : 'text-white/40'}`}>
                  {tier.tag}
                </div>
                <h3 className="text-white text-[24px] font-semibold mb-2">{tier.title}</h3>
                <div className="text-[#ffb15c] text-[20px] font-mono mb-6">{tier.price}</div>

                <ul className="space-y-3 mb-8">
                  {tier.features.map((feat, f) => (
                    <li key={f} className="text-white/60 text-[14px] flex items-start gap-2">
                      <span className="text-[#33d17e]">—</span>
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <a 
                href="#contact"
                className={`w-full py-3.5 rounded-lg text-center text-[14px] font-semibold transition-colors ${
                  tier.popular
                    ? 'bg-[#33d17e] text-black hover:bg-[#ffb15c]'
                    : 'bg-white/10 text-white hover:bg-white/20'
                }`}
              >
                Выбрать уровень
              </a>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
