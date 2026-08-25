import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ScrambleIn } from './ScrambleIn';
import { Warp } from '@paper-design/shaders-react';

const LEAD_WEBHOOK = 'https://avior.moscow/lead.php';

type SendState = 'idle' | 'sending' | 'ok' | 'error';

export const ContactSection: React.FC = () => {
  const [headingTriggered, setHeadingTriggered] = useState(false);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [channel, setChannel] = useState<'telegram' | 'max' | 'call'>('telegram');
  const [text, setText] = useState('');
  const [website, setWebsite] = useState(''); // honeypot
  const [state, setState] = useState<SendState>('idle');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (website) return; // honeypot: бот заполнил скрытое поле — тихо игнорируем
    if (!name.trim() || !phone.trim()) return;

    setState('sending');
    try {
      const r = await fetch(LEAD_WEBHOOK, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          phone: phone.trim(),
          channel,
          text: text.trim(),
          page: window.location.href,
          ts: new Date().toISOString(),
        }),
      });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      setState('ok');
      setName('');
      setPhone('');
      setText('');
    } catch {
      setState('error');
    }
  };

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

            {state === 'ok' ? (
              <div className="max-w-md mx-auto py-6">
                <div className="text-[#33d17e] text-[18px] font-medium mb-2">Заявка отправлена</div>
                <p className="text-white/50 text-[14px]">Отвечаю лично, обычно в течение часа в рабочее время.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="max-w-md mx-auto text-left flex flex-col gap-4">
                <input
                  type="text"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  tabIndex={-1}
                  autoComplete="off"
                  className="absolute -left-[9999px] opacity-0"
                  aria-hidden="true"
                />

                <div className="flex flex-col gap-1.5">
                  <label htmlFor="cs-name" className="text-white/50 text-[13px]">Имя</label>
                  <input
                    id="cs-name"
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Как к вам обращаться"
                    className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/10 text-white placeholder-white/30 text-[15px] focus:outline-none focus:border-[#33d17e]/60 transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label htmlFor="cs-phone" className="text-white/50 text-[13px]">Телефон или ник в мессенджере</label>
                  <input
                    id="cs-phone"
                    type="text"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+7 ___ ___-__-__ или @ник"
                    className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/10 text-white placeholder-white/30 text-[15px] focus:outline-none focus:border-[#33d17e]/60 transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <span className="text-white/50 text-[13px]">Как удобнее получить ответ</span>
                  <div className="flex gap-2 flex-wrap">
                    {([
                      { value: 'telegram', label: 'Telegram' },
                      { value: 'max', label: 'MAX' },
                      { value: 'call', label: 'Звонок' },
                    ] as const).map((opt) => (
                      <label
                        key={opt.value}
                        className={`px-4 py-2 rounded-full border text-[14px] cursor-pointer transition-colors ${
                          channel === opt.value
                            ? 'bg-[#33d17e] text-black border-[#33d17e]'
                            : 'bg-white/[0.03] text-white/70 border-white/10 hover:border-white/30'
                        }`}
                      >
                        <input
                          type="radio"
                          name="channel"
                          value={opt.value}
                          checked={channel === opt.value}
                          onChange={() => setChannel(opt.value)}
                          className="hidden"
                        />
                        {opt.label}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label htmlFor="cs-text" className="text-white/50 text-[13px]">О проекте</label>
                  <textarea
                    id="cs-text"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Чем занимается бизнес и что должен делать сайт"
                    rows={3}
                    className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/10 text-white placeholder-white/30 text-[15px] focus:outline-none focus:border-[#33d17e]/60 transition-colors resize-none"
                  />
                </div>

                <label className="flex items-start gap-2 text-white/40 text-[12px] leading-snug">
                  <input type="checkbox" required className="mt-0.5" />
                  <span>
                    Согласен(а) на обработку персональных данных в соответствии с{' '}
                    <a href="https://avior.moscow/privacy.html" target="_blank" rel="noreferrer" className="underline hover:text-white/60">
                      политикой конфиденциальности
                    </a>
                  </span>
                </label>

                <button
                  type="submit"
                  disabled={state === 'sending'}
                  className="inline-flex items-center justify-center gap-3 px-8 py-4 bg-[#33d17e] text-black font-semibold rounded-full hover:bg-[#ffb15c] transition-colors text-[16px] disabled:opacity-50"
                >
                  {state === 'sending' ? 'Отправляю…' : 'Отправить заявку'}
                </button>

                {state === 'error' && (
                  <div className="text-[#ff6b6b] text-[13px] text-center">
                    Не отправилось. Попробуйте ещё раз или напишите в{' '}
                    <a href="https://t.me/ghost0590" target="_blank" rel="noreferrer" className="underline">Telegram</a>.
                  </div>
                )}

                <div className="text-white/30 text-[12px] text-center">
                  Отвечаю лично, обычно в течение часа в рабочее время.
                </div>
              </form>
            )}
          </div>
        </motion.div>
      </div>
    </section>
  );
};
