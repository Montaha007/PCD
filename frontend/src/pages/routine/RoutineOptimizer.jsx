import { useState, useEffect } from 'react';
import { GlassCard } from '../../components/GlassCard';
import AppSidebar from '../../components/AppSidebar';
import FloatingStars from '../../components/FloatingStars';
import { motion } from 'motion/react';
import {
  Sparkles, Clock, Moon, Zap, Heart, Wind,
  Droplet, BookOpen, AlertTriangle, Loader,
} from 'lucide-react';
import './RoutineOptimizer.css';

const API_BASE = import.meta.env.VITE_API_BASE;

// ── Icon / gradient mapping by action_id prefix ────────────────────────────

const STEP_STYLES = [
  { icon: Moon,          from: '#6366f1', to: '#8b5cf6' },
  { icon: Wind,          from: '#06b6d4', to: '#3b82f6' },
  { icon: BookOpen,      from: '#3b82f6', to: '#6366f1' },
  { icon: Droplet,       from: '#8b5cf6', to: '#06b6d4' },
  { icon: Heart,         from: '#6366f1', to: '#3b82f6' },
  { icon: Sparkles,      from: '#3b82f6', to: '#8b5cf6' },
];

const SUGGESTION_ICONS = [Heart, Sparkles, Moon, Zap, Wind, BookOpen];

function iconForId(id = '') {
  if (id.startsWith('SH'))  return Moon;
  if (id.startsWith('CBT')) return Zap;
  if (id.startsWith('LA'))  return Heart;
  if (id.startsWith('CL'))  return AlertTriangle;
  return Clock;
}

// ── Long-term normalizer ───────────────────────────────────────────────────
// Handles both: array of actions OR { duration, phases: [{ interventions }] }
function normalizeLongTerm(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (Array.isArray(raw.phases)) {
    return raw.phases.flatMap(p =>
      (p.interventions ?? []).map(a => ({
        ...a,
        _phase: `Phase ${p.phase} (${p.weeks}) — ${p.focus}`,
      }))
    );
  }
  return [];
}

// ── Data hook ──────────────────────────────────────────────────────────────

function useWellnessRoutine() {
  const [routine,  setRoutine]  = useState(null);   // full final_output
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);

  useEffect(() => {
    let cancelled = false;
    const token   = localStorage.getItem('access_token');
    const headers = { Authorization: `Bearer ${token}` };
    const todayISO = new Date().toISOString().split('T')[0];

    setLoading(true);
    setError(null);

    const tryWellness = id =>
      fetch(`${API_BASE}/api/sleeplog/${id}/wellness-analysis/`, { headers })
        .then(r => r.json())
        .then(json => {
          if (json.success) return json;
          return fetch(`${API_BASE}/api/sleeplog/${id}/wellness-analysis/`,
            { method: 'POST', headers }
          ).then(r => r.json());
        });

    fetch(`${API_BASE}/api/sleeplog/`, { headers })
      .then(r => r.json())
      .then(logs => {
        const todayLog = logs.find(l =>
          (l.sleep_time ?? '').startsWith(todayISO) ||
          (l.created_at ?? '').startsWith(todayISO)
        );
        if (!todayLog) throw new Error('No sleep log found for today. Please log your sleep first.');
        return tryWellness(todayLog.id);
      })
      .then(json => {
        if (cancelled) return;
        if (json.success) setRoutine(json.data?.final_output ?? null);
        else setError(json.error || 'Analysis failed.');
      })
      .catch(err => { if (!cancelled) setError(err.message || 'Could not load recommendations.'); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, []);

  return { routine, loading, error };
}

// ── Status cycling ─────────────────────────────────────────────────────────

const STATUSES  = ['Not started', 'In progress', 'Done'];
const STATUS_META = {
  'Not started': { color: '#8fa8c8', bg: 'rgba(100,160,255,0.08)',  border: 'rgba(100,160,255,0.20)' },
  'In progress': { color: '#fbbf24', bg: 'rgba(251,191,36,0.10)',  border: 'rgba(251,191,36,0.30)'  },
  'Done':        { color: '#5dcf8a', bg: 'rgba(93,207,138,0.10)',  border: 'rgba(93,207,138,0.30)'  },
};

function StatusBadge({ status, onClick }) {
  const m = STATUS_META[status];
  return (
    <button
      type="button"
      className="ro-status-badge"
      style={{ color: m.color, background: m.bg, borderColor: m.border }}
      onClick={onClick}
      title="Click to cycle status"
    >
      <span className="ro-status-dot" style={{ background: m.color }} />
      {status}
    </button>
  );
}

// ── Bedtime card ───────────────────────────────────────────────────────────

function BedtimeCard({ routine }) {
  // Derive bedtime from the last timed action, or fall back to "22:00"
  const steps = routine?.action_plan?.short_term ?? [];
  const timed = steps.filter(s => /^\d{1,2}:\d{2}$/.test(s.timing ?? ''));
  const bedtime = timed.length
    ? timed[timed.length - 1].timing
    : '22:00';

  return (
    <GlassCard className="ro-bedtime-card">
      <div className="ro-bedtime-inner">
        <div className="ro-bedtime-moon-ring">
          <Moon size={28} strokeWidth={1.6} style={{ color: '#c7b8ff' }} />
        </div>
        <div>
          <p className="ro-bedtime-label">Optimal bedtime</p>
          <div className="ro-bedtime-time">{bedtime}</div>
        </div>
      </div>
      {routine?.plan_summary && (
        <p className="ro-bedtime-sub">{routine.plan_summary}</p>
      )}
      {routine?.referral_required && routine?.referral_message && (
        <div className="ro-referral-banner">
          <AlertTriangle size={14} strokeWidth={2} />
          {routine.referral_message}
        </div>
      )}
    </GlassCard>
  );
}

// ── Step card ──────────────────────────────────────────────────────────────

function StepCard({ step, index, status, onStatusChange }) {
  const style   = STEP_STYLES[index % STEP_STYLES.length];
  const Icon    = iconForId(step.action_id);

  return (
    <motion.div
      className="ro-step"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08, duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      {/* time badge */}
      {step.timing && (
        <span className="ro-step-time">{step.timing}</span>
      )}

      {/* gradient icon */}
      <div
        className="ro-step-icon"
        style={{ background: `linear-gradient(135deg, ${style.from}, ${style.to})` }}
      >
        <Icon size={22} strokeWidth={1.8} color="#fff" />
      </div>

      {/* body */}
      <div className="ro-step-body">
        <div className="ro-step-top">
          <h3 className="ro-step-title">{step.action}</h3>
          <StatusBadge
            status={status}
            onClick={() => {
              const next = STATUSES[(STATUSES.indexOf(status) + 1) % STATUSES.length];
              onStatusChange(step.action_id, next);
            }}
          />
        </div>
        {step._phase && (
          <p className="ro-step-phase">{step._phase}</p>
        )}
        {(step.quantity || step.frequency) && (
          <p className="ro-step-desc">
            {[step.quantity, step.frequency].filter(Boolean).join(' · ')}
          </p>
        )}
      </div>
    </motion.div>
  );
}

// ── Suggestion card ────────────────────────────────────────────────────────

function SuggestionCard({ pe, index }) {
  const Icon = SUGGESTION_ICONS[index % SUGGESTION_ICONS.length];
  const style = STEP_STYLES[index % STEP_STYLES.length];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.92 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.5 + index * 0.1, duration: 0.3 }}
    >
      <GlassCard className="ro-suggestion-card">
        <div
          className="ro-suggestion-icon"
          style={{ background: `linear-gradient(135deg, ${style.from}33, ${style.to}33)`,
                   borderColor: `${style.from}44` }}
        >
          <Icon size={22} strokeWidth={1.8} style={{ color: style.from }} />
        </div>
        <h3 className="ro-suggestion-title">{pe.topic}</h3>
        <p className="ro-suggestion-desc">{pe.description}</p>
      </GlassCard>
    </motion.div>
  );
}

// ── Progress bar ───────────────────────────────────────────────────────────

function ProgressBar({ statuses }) {
  const total      = statuses.length;
  const done       = statuses.filter(s => s === 'Done').length;
  const inProgress = statuses.filter(s => s === 'In progress').length;
  const pct        = total ? Math.round((done / total) * 100) : 0;

  return (
    <GlassCard className="ro-summary-card">
      <div className="ro-summary-top">
        <div className="ro-summary-icon">
          <Sparkles size={18} strokeWidth={1.8} style={{ color: '#c7b8ff' }} />
        </div>
        <div className="ro-summary-copy">
          <h2 className="ro-summary-title">Your Progress</h2>
          <p className="ro-summary-sub">
            {done} of {total} steps completed
            {inProgress > 0 ? ` · ${inProgress} in progress` : ''}
          </p>
        </div>
        <div className="ro-summary-pct" style={{ color: pct === 100 ? '#5dcf8a' : '#a7c7e7' }}>
          {pct}<span>%</span>
        </div>
      </div>
      <div className="ro-progress-track">
        <motion.div
          className="ro-progress-fill"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          style={{
            background: pct === 100
              ? 'linear-gradient(90deg, #5dcf8a, #66d4cf)'
              : 'linear-gradient(90deg, #6366f1, #8b5cf6)',
          }}
        />
      </div>
      <div className="ro-summary-pills">
        {STATUSES.map(s => {
          const count = statuses.filter(st => st === s).length;
          const m     = STATUS_META[s];
          return (
            <span key={s} className="ro-pill"
              style={{ color: m.color, background: m.bg, borderColor: m.border }}>
              <span className="ro-status-dot" style={{ background: m.color }} />
              {s}: {count}
            </span>
          );
        })}
      </div>
    </GlassCard>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function RoutineOptimizer() {
  const { routine, loading, error } = useWellnessRoutine();
  const [statusMap, setStatusMap]   = useState({});

  const steps           = routine?.action_plan?.short_term ?? [];
  const longSteps       = normalizeLongTerm(routine?.action_plan?.long_term);
  const allSteps        = [...steps, ...longSteps];
  const psychoeducation = routine?.psychoeducation ?? [];

  // Seed new steps into statusMap
  useEffect(() => {
    setStatusMap(prev => {
      const next = { ...prev };
      allSteps.forEach(s => { if (!(s.action_id in next)) next[s.action_id] = 'Not started'; });
      return next;
    });
  }, [allSteps.map(s => s.action_id).join(',')]);

  const handleStatusChange = (id, next) =>
    setStatusMap(prev => ({ ...prev, [id]: next }));

  const statuses = allSteps.map(s => statusMap[s.action_id] ?? 'Not started');

  return (
    <div className="wellness-shell">
      <FloatingStars />
      <AppSidebar />
      <main className="wellness-content">
        <div className="ro-wrap">

          {/* Header */}
          <div className="ro-header">
            <span className="ro-chip">AI Recommendations</span>
            <h1 className="ro-title">
              <Sparkles size={28} strokeWidth={1.8} className="ro-title-icon" />
              Routine Optimizer
            </h1>
            <p className="ro-sub">
              Personalized sleep routine generated from your daily wellness analysis.
            </p>
          </div>

          {/* Loading */}
          {loading && (
            <div className="ro-state-msg">
              <Loader size={20} className="ro-spin" />
              Generating your personalized plan…
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <div className="ro-state-msg ro-state-msg--error">
              <AlertTriangle size={18} />
              {error}
            </div>
          )}

          {/* Content */}
          {!loading && routine && (
            <>
              {/* Optimal bedtime card */}
              <BedtimeCard routine={routine} />

              {/* Progress bar — counts all steps */}
              {allSteps.length > 0 && <ProgressBar statuses={statuses} />}

              {/* Short-term routine steps */}
              {steps.length > 0 && (
                <div>
                  <h2 className="ro-section-title">Your personalized routine <span className="ro-section-badge">7 days</span></h2>
                  <div className="ro-steps-list">
                    {steps.map((step, i) => (
                      <StepCard
                        key={step.action_id}
                        step={step}
                        index={i}
                        status={statusMap[step.action_id] ?? 'Not started'}
                        onStatusChange={handleStatusChange}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Long-term plan */}
              {longSteps.length > 0 && (
                <div>
                  <h2 className="ro-section-title">Long-term plan <span className="ro-section-badge">6 weeks</span></h2>
                  <div className="ro-steps-list">
                    {longSteps.map((step, i) => (
                      <StepCard
                        key={step.action_id}
                        step={step}
                        index={i}
                        status={statusMap[step.action_id] ?? 'Not started'}
                        onStatusChange={handleStatusChange}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Psychoeducation suggestions */}
              {psychoeducation.length > 0 && (
                <div>
                  <h2 className="ro-section-title">Additional insights</h2>
                  <div className="ro-suggestions-grid">
                    {psychoeducation.map((pe, i) => (
                      <SuggestionCard key={pe.topic_id ?? i} pe={pe} index={i} />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

        </div>
      </main>
    </div>
  );
}
