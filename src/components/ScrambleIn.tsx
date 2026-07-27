import React, { useEffect, useState, useRef } from 'react';

interface ScrambleInProps {
  text: string;
  delay: number;
  triggered: boolean;
  className?: string;
}

const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+~|}{[]:;?><АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя';

export const ScrambleIn: React.FC<ScrambleInProps> = ({ text, delay, triggered, className = '' }) => {
  const [displayText, setDisplayText] = useState<string>('');
  const [isStarted, setIsStarted] = useState<boolean>(false);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    if (!triggered) return;
    const timeout = setTimeout(() => setIsStarted(true), delay);
    return () => clearTimeout(timeout);
  }, [triggered, delay]);

  useEffect(() => {
    if (!isStarted) return;

    const interval = setInterval(() => {
      frameRef.current += 1;
      const currentRevealIndex = Math.floor(frameRef.current * 0.5);

      if (currentRevealIndex >= text.length) {
        setDisplayText(text);
        clearInterval(interval);
        return;
      }

      let result = '';
      for (let i = 0; i < text.length; i++) {
        if (text[i] === ' ') {
          result += ' ';
          continue;
        }

        if (i < currentRevealIndex) {
          result += text[i];
        } else if (i <= currentRevealIndex + 3) {
          result += CHARS[Math.floor(Math.random() * CHARS.length)];
        } else {
          break;
        }
      }

      setDisplayText(result);
    }, 25);

    return () => clearInterval(interval);
  }, [isStarted, text]);

  if (!triggered || (!isStarted && displayText === '')) {
    return <span className={className} dangerouslySetInnerHTML={{ __html: '&nbsp;' }} />;
  }

  return <span className={className}>{displayText}</span>;
};
