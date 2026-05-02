import './OnboardingProgress.css';
import { useEffect, useMemo, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const STEPS = [
  { key: 'profile', label: 'Profile' },
  { key: 'sleep', label: 'Sleep' },
  { key: 'lifestyle', label: 'Lifestyle' },
  { key: 'journal', label: 'Journal' },
];
const DEFAULT_PROGRESS = {
  setup_completed_steps: ['profile'],
  setup_completed_count: 1,
  setup_total_steps: STEPS.length,
};

export function OnboardingProgress({ currentStep = 'sleep' }) {
  const [progress, setProgress] = useState(DEFAULT_PROGRESS);

  const completedSteps = useMemo(
    () => new Set(progress.setup_completed_steps || []),
    [progress.setup_completed_steps]
  );

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setProgress(DEFAULT_PROGRESS);
      return undefined;
    }

    let isMounted = true;

    const loadProgress = async () => {
      try {
        const res = await fetch(`${API_BASE}/profiles/api/me/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;

        const data = await res.json();
        if (!isMounted) return;

        setProgress({
          setup_completed_steps: Array.isArray(data.setup_completed_steps)
            ? data.setup_completed_steps
            : DEFAULT_PROGRESS.setup_completed_steps,
          setup_completed_count:
            typeof data.setup_completed_count === 'number'
              ? data.setup_completed_count
              : DEFAULT_PROGRESS.setup_completed_count,
          setup_total_steps:
            typeof data.setup_total_steps === 'number'
              ? data.setup_total_steps
              : DEFAULT_PROGRESS.setup_total_steps,
        });
      } catch {
        // Keep fallback UI if profile fetch fails.
      }
    };

    loadProgress();
    window.addEventListener('setup-progress-refresh', loadProgress);
    return () => {
      isMounted = false;
      window.removeEventListener('setup-progress-refresh', loadProgress);
    };
  }, []);

  const done = typeof progress.setup_completed_count === 'number'
    ? progress.setup_completed_count
    : completedSteps.size;
  const total = progress.setup_total_steps || STEPS.length;
  const pct = Math.round((done / total) * 100);

  return (
    <div className="onboarding-bar">
      <span className="onboarding-bar-label">Setup</span>

      <div className="onboarding-track">
        <div className="onboarding-fill" style={{ width: `${pct}%` }} />
      </div>

      <div className="onboarding-steps">
        {STEPS.map((step) => {
          const isDone = completedSteps.has(step.key);
          const isActive = !isDone && step.key === currentStep;
          return (
            <span
              key={step.key}
              className={`onboarding-dot${isDone ? ' is-done' : isActive ? ' is-active' : ''}`}
              title={step.label}
            />
          );
        })}
      </div>

      <span className="onboarding-bar-count">{done}/{total}</span>
    </div>
  );
}
