import './OnboardingProgress.css';

const STEPS = ['Profile', 'Sleep', 'Lifestyle', 'Journal'];
const ACTIVE_STEP = 1; // Sleep is step index 1

export function OnboardingProgress() {
  const done = ACTIVE_STEP;
  const total = STEPS.length;
  const pct = Math.round((done / total) * 100);

  return (
    <div className="onboarding-bar">
      <span className="onboarding-bar-label">Setup</span>

      <div className="onboarding-track">
        <div className="onboarding-fill" style={{ width: `${pct}%` }} />
      </div>

      <div className="onboarding-steps">
        {STEPS.map((_, i) => (
          <span
            key={i}
            className={`onboarding-dot${i < done ? ' is-done' : i === done ? ' is-active' : ''}`}
            title={STEPS[i]}
          />
        ))}
      </div>

      <span className="onboarding-bar-count">{done}/{total}</span>
    </div>
  );
}
