import { useMemo } from 'react';
import './FloatingStars.css';

export default function FloatingStars({ count = 60 }) {
  const stars = useMemo(() => (
    Array.from({ length: count }, (_, i) => ({
      id:       i,
      top:      `${Math.random() * 100}%`,
      left:     `${Math.random() * 100}%`,
      size:     Math.random() * 2 + 1,
      opacityMin:      Math.random() * 0.18 + 0.06,
      opacityMax:      Math.random() * 0.45 + 0.4,
      floatDuration:   Math.random() * 6 + 5,
      floatDelay:      -(Math.random() * 8),
      twinkleDuration: Math.random() * 2.8 + 1.2,
      twinkleDelay:    -(Math.random() * 6),
    }))
  ), []);

  return (
    <div className="floating-stars" aria-hidden="true">
      {stars.map((s) => (
        <span
          key={s.id}
          className="floating-star"
          style={{
            top:                 s.top,
            left:                s.left,
            width:               s.size,
            height:              s.size,
            '--opacity-min':     s.opacityMin,
            '--opacity-max':     Math.min(1, s.opacityMax),
            '--float-duration':  `${s.floatDuration}s`,
            '--float-delay':     `${s.floatDelay}s`,
            '--twinkle-duration': `${s.twinkleDuration}s`,
            '--twinkle-delay':    `${s.twinkleDelay}s`,
          }}
        />
      ))}
    </div>
  );
}
