import React from 'react';
import { motion } from 'framer-motion';

interface CaseStat {
  value: string;
  label: string;
}

interface CaseStudy {
  title: string;
  url: string;
  urlLabel: string;
  description: string;
  stats: CaseStat[];
}

const cases: CaseStudy[] = [
  {
    title: 'AVIOR — мастерская по ремонту электроники',
    url: 'https://avior.moscow',
    urlLabel: 'avior.moscow →',
    description:
      'Ремонт ноутбуков, смартфонов и техники в Москве. Сайт с нуля: 9 отдельных страниц под каждую услугу с честным SEO, автоматические уведомления о заявках, статус ремонта прямо на сайте, светлая и тёмная тема.',
    stats: [
      { value: '9', label: 'услуг со своей SEO-страницей' },
      { value: '2', label: 'темы: светлая и тёмная' },
      { value: '0', label: 'ручного разбора заявок' },
      { value: '100%', label: 'рабочий сайт, не демо' }
    ]
  },
  {
    title: 'LIVETVAZ — новостной портал и прямой эфир',
    url: 'https://livetvaz.ru',
    urlLabel: 'livetvaz.ru →',
    description:
      'Азербайджанский телеканал для диаспоры в России. Новостной портал с категориями и отдельными страницами под каждую новость, встроенный прямой эфир, интеграция с YouTube и RuTube.',
    stats: [
      { value: '7', label: 'категорий новостей' },
      { value: 'Live', label: 'эфир прямо на сайте' },
      { value: '2', label: 'соцплатформы: YouTube и RuTube' },
      { value: '100%', label: 'у каждой новости своя SEO-страница' }
    ]
  }
];

export const CaseSection: React.FC = () => {
  return (
    <section id="case" className="relative w-full min-h-screen bg-black flex items-center justify-center py-32 px-6">
      <video
        src="/video3.mp4"
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
          transition={{ duration: 0.8 }}
          viewport={{ once: true, amount: 0.3 }}
          className="mb-16"
        >
          <div className="text-[#33d17e] text-[13px] tracking-[0.2em] uppercase mb-3">
            // ПРИМЕРЫ РАБОТ
          </div>
          <h2 className="text-white font-light text-[clamp(28px,5vw,46px)] leading-tight">
            Действующие сайты, а не просто макеты
          </h2>
          <p className="text-white/50 text-[15px] mt-4 max-w-xl leading-relaxed">
            Строю по тем же принципам, что предлагаю клиентам — рабочий результат, а не демо-версия.
          </p>
        </motion.div>

        <div className="flex flex-col gap-8">
          {cases.map((c, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, delay: idx * 0.1 }}
              viewport={{ once: true, amount: 0.3 }}
              className="p-8 sm:p-12 border border-white/10 rounded-2xl bg-white/[0.03] backdrop-blur-md"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <h3 className="text-white text-[22px] sm:text-[28px] font-semibold">
                  {c.title}
                </h3>
                <a
                  href={c.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#33d17e] hover:text-[#ffb15c] transition-colors text-[14px] flex items-center gap-1 flex-shrink-0"
                >
                  {c.urlLabel}
                </a>
              </div>

              <p className="text-white/60 text-[15px] leading-relaxed max-w-3xl mb-12">
                {c.description}
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-8 border-t border-white/10 pt-8">
                {c.stats.map((stat, i) => (
                  <div key={i}>
                    <div className="text-[#33d17e] text-[clamp(36px,6vw,64px)] font-light leading-none">
                      {stat.value}
                    </div>
                    <div className="text-white/50 text-[13px] mt-2 leading-snug">
                      {stat.label}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
