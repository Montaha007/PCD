import { useEffect, useRef } from 'react';
import './ui.css';

export function Slider({ value, onValueChange, min, max, step, className = '' }) {
  const inputRef = useRef(null);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    const pct = ((value[0] - min) / (max - min)) * 100;
    el.style.setProperty('--pct', `${pct}%`);
  }, [value, min, max]);

  return (
    <input
      ref={inputRef}
      type="range"
      value={value[0]}
      onChange={(e) => onValueChange([Number(e.target.value)])}
      min={min}
      max={max}
      step={step}
      className={`sl-slider-input ${className}`}
    />
  );
}
