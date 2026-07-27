import React, { useEffect, useState, useRef } from 'react';

interface ScrambleTextProps {
  text: string;
  isHovered: boolean;
  className?: string;
}

const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+~|}{[]:;?><АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя';

export const ScrambleText: React.FC<ScrambleTextProps> = ({ text, isHovered, className = '' }) => {
  const [displayText, setDisplayText] = useState<string>(text);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    if (!isHovered) {
      setDisplayText(text);
      frameRef.current = 0;
      return;
    }

    const interval = setInterval(() => {
      frameRef.current += 1;
      const revealIndex = Math.floor(frameRef.current / 4);

      if (revealIndex >= text.length) {
        setDisplayText(text);
        clearInterval(interval);
        return;
      }

      let scrambled = '';
      for (let i = 0; i < text.length; i++) {
        if (text[i] === ' ') {
          scrambled += ' ';
        } else if (i < revealIndex) {
          scrambled += text[i];
        } else {
          scrambled += CHARS[Math.floor(Math.random() * CHARS.length)];
        }
      }

      setDisplayText(scrambled);
    }, 25);

    return () => clearInterval(interval);
  }, [isHovered, text]);

  return <span className={className}>{displayText}</span>;
};
