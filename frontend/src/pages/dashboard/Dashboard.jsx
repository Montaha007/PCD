import { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { GlassCard } from '../../components/GlassCard';
import AppSidebar from '../../components/AppSidebar';
import FloatingStars from '../../components/FloatingStars';
import { motion } from 'motion/react';
import {
  Moon, Activity, BookOpen, AlertTriangle, Sparkles, Coffee,
  Smartphone, CheckCircle, Circle, TrendingUp, TrendingDown, Clock,
} from 'lucide-react';
import { toast } from 'sonner';
import './Dashboard.css';

const API_BASE = import.meta.env.VITE_API_BASE;

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

function ChartTooltip({ tooltip }) {
  if (!tooltip) return null;
  return (
    <div
      className="dash-tooltip"
      style={{
        left: tooltip.x,
        top: tooltip.y,
        transform: 'translate(-50%, calc(-100% - 12px))',
      }}
      role="status"
      aria-live="polite"
    >
      <div className="dash-tooltip-title">{tooltip.title}</div>
      {tooltip.lines?.map((line, i) => (
        <div key={i} className="dash-tooltip-line">{line}</div>
      ))}
    </div>
  );
}

// ── Helpers ────────────────────────────────────────────────────────────────

function todayISO() {
  return new Date().toISOString().split('T')[0];
}

function isToday(dateStr) {
  return !!dateStr && dateStr.startsWith(todayISO());
}

function parseDurationToHours(str) {
  if (!str) return 0;
  const dayMatch = str.match(/^(\d+) days?,\s*/);
  const extra = dayMatch ? parseInt(dayMatch[1], 10) * 24 : 0;
  const timePart = str.replace(/^\d+ days?,\s*/, '');
  const [h, m] = timePart.split(':').map(Number);
  return extra + (h || 0) + (m || 0) / 60;
}

function formatDuration(str) {
  if (!str) return '—';
  const dayMatch = str.match(/^(\d+) days?,\s*/);
  const extra = dayMatch ? parseInt(dayMatch[1], 10) * 24 : 0;
  const timePart = str.replace(/^\d+ days?,\s*/, '');
  const [h, m] = timePart.split(':').map(Number);
  return `${(h || 0) + extra}h ${String(m || 0).padStart(2, '0')}min`;
}

// ── Sleep Quality Score ────────────────────────────────────────────────────

function calcSleepScore({ sleepLog, sleepPrediction, lifestyleLog, lifestylePrediction, journalEntry }) {
  let score = 50;

  // Insomnia prediction — highest weight factor
  if (sleepPrediction) {
    score += sleepPrediction.prediction === 'insomnia' ? -25 : 20;
  }

  // Sleep duration
  if (sleepLog?.calculated_sleep_duration) {
    const h = parseDurationToHours(sleepLog.calculated_sleep_duration);
    if (h >= 7 && h <= 9)      score += 20;
    else if (h >= 6 && h < 7)  score += 8;
    else if (h > 9 && h <= 10) score += 5;
    else if (h >= 5 && h < 6)  score -= 10;
    else if (h < 5)            score -= 20;
    else if (h > 10)           score -= 10;
  }

  // Sleep quality booleans
  if (sleepLog) {
    if (sleepLog.satisfaction_of_sleep)       score += 10;
    if (sleepLog.late_night_sleep)            score -= 5;
    if (sleepLog.wake_up_frequently)          score -= 7;
    if (sleepLog.drowsiness_tiredness)        score -= 10;
    if (sleepLog.afraid_of_sleeping)          score -= 8;
    if (sleepLog.recent_psychological_attack) score -= 10;
    if (sleepLog.sleep_at_daytime)            score -= 5;
  }

  // Lifestyle raw data
  if (lifestyleLog) {
    if (lifestyleLog.CaffeineIntake > 200)    score -= 8;
    else if (lifestyleLog.CaffeineIntake > 150) score -= 4;
    if (lifestyleLog.PhoneTime > 4)           score -= 8;
    else if (lifestyleLog.PhoneTime > 3)      score -= 4;
    if (lifestyleLog.WorkoutTime >= 1)        score += 8;
    else if (lifestyleLog.WorkoutTime >= 0.5) score += 4;
    if (lifestyleLog.RelaxationTime >= 1)     score += 5;
  }

  // Lifestyle prediction quality label
  if (lifestylePrediction) {
    const lbl = lifestylePrediction.quality_label;
    if (lbl === 'healthy')      score += 8;
    else if (lbl === 'short')   score -= 5;
    else if (lbl === 'insufficient') score -= 10;
    else if (lbl === 'excessive')    score -= 3;
  }

  // Journal mood
  if (journalEntry?.predicted_mood) {
    const mood = journalEntry.predicted_mood.toLowerCase();
    if (mood === 'normal')                              score += 5;
    else if (['anxiety', 'stress'].includes(mood))      score -= 5;
    else if (['depression', 'bipolar'].includes(mood))  score -= 10;
    else if (mood === 'suicidal')                       score -= 15;
  }

  return Math.max(0, Math.min(100, Math.round(score)));
}

function getScoreMeta(score) {
  if (score >= 80) return { label: 'Excellent',  color: '#5dcf8a' };
  if (score >= 65) return { label: 'Good',       color: '#66d4cf' };
  if (score >= 50) return { label: 'Fair',       color: '#fbbf24' };
  if (score >= 35) return { label: 'Poor',       color: '#fb923c' };
  return               { label: 'Very Poor', color: '#f87171' };
}

// ── Detected Issues ────────────────────────────────────────────────────────

function getDetectedIssues({ sleepLog, lifestyleLog, sleepPrediction, journalEntry }) {
  const issues = [];
  if (sleepPrediction?.prediction === 'insomnia')
    issues.push({ icon: AlertTriangle, text: 'Insomnia pattern detected by AI model', severity: 'high' });
  if (sleepLog?.drowsiness_tiredness)
    issues.push({ icon: Moon, text: 'Chronic daytime fatigue reported', severity: 'high' });
  if (sleepLog?.afraid_of_sleeping)
    issues.push({ icon: AlertTriangle, text: 'Sleep-onset anxiety detected', severity: 'high' });
  if (sleepLog?.recent_psychological_attack)
    issues.push({ icon: AlertTriangle, text: 'Recent psychological event may affect sleep', severity: 'high' });
  if (sleepLog?.wake_up_frequently)
    issues.push({ icon: Clock, text: 'Frequent nighttime awakenings', severity: 'medium' });
  if (sleepLog?.late_night_sleep)
    issues.push({ icon: Moon, text: 'Irregular sleep schedule detected', severity: 'medium' });
  if (lifestyleLog?.PhoneTime > 3)
    issues.push({ icon: Smartphone, text: `High screen time (${lifestyleLog.PhoneTime}h) may suppress melatonin`, severity: 'medium' });
  if (lifestyleLog?.CaffeineIntake > 150)
    issues.push({ icon: Coffee, text: `Caffeine intake (${lifestyleLog.CaffeineIntake}mg) above optimal threshold`, severity: 'medium' });
  if (journalEntry?.predicted_mood) {
    const mood = journalEntry.predicted_mood.toLowerCase();
    if (['anxiety', 'stress', 'depression', 'bipolar', 'suicidal'].includes(mood))
      issues.push({ icon: BookOpen, text: `Mental health signal detected: ${journalEntry.predicted_mood}`, severity: mood === 'suicidal' ? 'high' : 'medium' });
  }
  return issues;
}

// ── SVG Line Chart ─────────────────────────────────────────────────────────

function SleepLineChart({ data }) {
  if (!data.length) return null;
  const W = 320, H = 160;
  const pad = { t: 16, b: 28, l: 28, r: 12 };
  const iW = W - pad.l - pad.r;
  const iH = H - pad.t - pad.b;

  const wrapRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);
  const [hoverIdx, setHoverIdx] = useState(null);

  const vals = data.map(d => d.hours);
  const maxV = Math.max(...vals, 9);
  const minV = Math.min(...vals, 5);
  const range = maxV - minV || 1;

  const xOf = i => data.length === 1
    ? pad.l + iW / 2
    : pad.l + (i / (data.length - 1)) * iW;
  const yOf = v => pad.t + iH - ((v - minV) / range) * iH;

  const pathD = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${xOf(i)} ${yOf(d.hours)}`).join(' ');
  const areaD = `${pathD} L ${xOf(data.length - 1)} ${H - pad.b} L ${xOf(0)} ${H - pad.b} Z`;

  const handleLeave = () => {
    setTooltip(null);
    setHoverIdx(null);
  };

  const showTooltip = (evt, idx) => {
    if (!wrapRef.current) return;
    const rect = wrapRef.current.getBoundingClientRect();
    const point = data[idx];
    setHoverIdx(idx);
    setTooltip({
      x: clamp(evt.clientX - rect.left, 24, rect.width - 24),
      y: clamp(evt.clientY - rect.top, 24, rect.height - 24),
      title: point.dateLabel || point.day,
      lines: [`${point.hours}h slept`],
    });
  };

  const moveTooltip = (evt) => {
    if (!wrapRef.current) return;
    const rect = wrapRef.current.getBoundingClientRect();
    setTooltip((prev) => (prev ? {
      ...prev,
      x: clamp(evt.clientX - rect.left, 24, rect.width - 24),
      y: clamp(evt.clientY - rect.top, 24, rect.height - 24),
    } : prev));
  };

  return (
    <div className="dash-chart-wrap" ref={wrapRef} onPointerLeave={handleLeave}>
      <ChartTooltip tooltip={tooltip} />
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ overflow: 'visible' }}>
      <defs>
        <linearGradient id="slGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor="#6ea8d8" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#6ea8d8" stopOpacity="0.02" />
        </linearGradient>
      </defs>
      {[0, 0.33, 0.66, 1].map(f => (
        <line key={f}
          x1={pad.l} y1={pad.t + iH * f}
          x2={W - pad.r} y2={pad.t + iH * f}
          stroke="rgba(100,160,255,0.1)" strokeWidth="1"
        />
      ))}
      {data.map((d, i) => (
        <text key={i} x={xOf(i)} y={H - 6} textAnchor="middle" fill="#8fa8c8" fontSize="10">
          {d.day}
        </text>
      ))}
      <path d={areaD} fill="url(#slGrad)" />
      <path d={pathD} fill="none" stroke="#6ea8d8" strokeWidth="2.5"
        strokeLinecap="round" strokeLinejoin="round" />
      {typeof hoverIdx === 'number' && (
        <line
          x1={xOf(hoverIdx)}
          x2={xOf(hoverIdx)}
          y1={pad.t}
          y2={H - pad.b}
          stroke="rgba(110,168,216,0.22)"
          strokeWidth="1"
        />
      )}
      {data.map((d, i) => {
        const isHovered = i === hoverIdx;
        return (
          <g
            key={i}
            onPointerEnter={(evt) => showTooltip(evt, i)}
            onPointerMove={moveTooltip}
            onPointerLeave={handleLeave}
            style={{ cursor: 'default' }}
          >
            <circle
              cx={xOf(i)}
              cy={yOf(d.hours)}
              r={isHovered ? 7 : 6}
              fill="transparent"
            />
            <circle
              className="dash-chart-point"
              cx={xOf(i)}
              cy={yOf(d.hours)}
              r={isHovered ? 5.5 : 4}
              fill={isHovered ? '#a7c7e7' : '#6ea8d8'}
              stroke="#040010"
              strokeWidth={isHovered ? 2.4 : 2}
            />
          </g>
        );
      })}
    </svg>
    </div>
  );
}

// ── SVG Bar Chart ──────────────────────────────────────────────────────────

function LifestyleBarChart({ data }) {
  if (!data.length) return null;
  const W = 320, H = 150;
  const pad = { t: 10, b: 30, l: 8, r: 8 };
  const iW = W - pad.l - pad.r;
  const iH = H - pad.t - pad.b;
  const slot = iW / data.length;
  const bW = slot * 0.55;

  const wrapRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);
  const [hoverIdx, setHoverIdx] = useState(null);

  const handleLeave = () => {
    setTooltip(null);
    setHoverIdx(null);
  };

  const showTooltip = (evt, idx) => {
    if (!wrapRef.current) return;
    const rect = wrapRef.current.getBoundingClientRect();
    const item = data[idx];
    setHoverIdx(idx);
    setTooltip({
      x: clamp(evt.clientX - rect.left, 24, rect.width - 24),
      y: clamp(evt.clientY - rect.top, 24, rect.height - 24),
      title: item.tooltipTitle || item.label,
      lines: [item.tooltipValue || `${item.rawValue}${item.unit || ''}`],
    });
  };

  const moveTooltip = (evt) => {
    if (!wrapRef.current) return;
    const rect = wrapRef.current.getBoundingClientRect();
    setTooltip((prev) => (prev ? {
      ...prev,
      x: clamp(evt.clientX - rect.left, 24, rect.width - 24),
      y: clamp(evt.clientY - rect.top, 24, rect.height - 24),
    } : prev));
  };

  return (
    <div className="dash-chart-wrap" ref={wrapRef} onPointerLeave={handleLeave}>
      <ChartTooltip tooltip={tooltip} />
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ overflow: 'visible' }}>
        {data.map((d, i) => {
          const x = pad.l + i * slot + (slot - bW) / 2;
          const frac = Math.min(Math.max(d.value / (d.maxValue || 1), 0), 1);
          const bH = frac * iH;
          const y = pad.t + iH - bH;
          const isHovered = i === hoverIdx;
          return (
            <g
              key={i}
              onPointerEnter={(evt) => showTooltip(evt, i)}
              onPointerMove={moveTooltip}
              onPointerLeave={handleLeave}
              style={{ cursor: 'default' }}
            >
              <rect x={x} y={pad.t} width={bW} height={iH} rx="4"
                fill="rgba(100,160,255,0.07)" />
              <rect
                className="dash-chart-bar"
                x={x}
                y={y}
                width={bW}
                height={bH}
                rx="4"
                fill={d.color}
                opacity={isHovered ? 1 : 0.85}
              />
              {isHovered && (
                <rect
                  x={x - 1}
                  y={pad.t - 1}
                  width={bW + 2}
                  height={iH + 2}
                  rx="6"
                  fill="transparent"
                  stroke="rgba(167,199,231,0.35)"
                  strokeWidth="1"
                />
              )}
              <text x={x + bW / 2} y={H - 10} textAnchor="middle"
                fill="#8fa8c8" fontSize="9.5">
                {d.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  const [sleepLog,            setSleepLog]            = useState(null);
  const [sleepPrediction,     setSleepPrediction]     = useState(null);
  const [lifestyleLog,        setLifestyleLog]        = useState(null);
  const [lifestylePrediction, setLifestylePrediction] = useState(null);
  const [journalEntry,        setJournalEntry]        = useState(null);
  const [sleepHistory,        setSleepHistory]        = useState([]);

  const getToken = () => localStorage.getItem('access_token');

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      const token = getToken();
      if (!token) { setLoading(false); return; }

      const headers = { Authorization: `Bearer ${token}` };

      try {
        const [sleepRes, journalRes, lifestyleRes] = await Promise.all([
          fetch(`${API_BASE}/api/sleeplog/`,        { headers }),
          fetch(`${API_BASE}/api/mood/entries/`,    { headers }),
          fetch(`${API_BASE}/api/lifestyle/logs/`,  { headers }),
        ]);

        // Sleep logs
        if (sleepRes.ok) {
          const logs = await sleepRes.json();
          const todayLog = logs.find(l =>
            isToday(l.sleep_time) || isToday(l.created_at)
          );
          setSleepLog(todayLog ?? null);

          // Build last-7 history for line chart (sorted by date, uses stored data)
          const sorted = logs.slice().sort((a, b) => (
            new Date(a.sleep_time || a.created_at) - new Date(b.sleep_time || b.created_at)
          ));
          const history = sorted.slice(-7).map(l => {
            const dt = new Date(l.sleep_time || l.created_at);
            return {
              day: dt.toLocaleDateString('en', { weekday: 'short' }),
              dateLabel: dt.toLocaleDateString('en', { month: 'short', day: 'numeric' }),
              dateISO: dt.toISOString(),
              hours: parseFloat(parseDurationToHours(l.calculated_sleep_duration).toFixed(1)),
            };
          });
          setSleepHistory(history);

          if (todayLog?.id) {
            const pr = await fetch(`${API_BASE}/api/sleeplog/${todayLog.id}/predict/`, { headers });
            if (pr.ok) setSleepPrediction(await pr.json());
          }
        }

        // Journal entries
        if (journalRes.ok) {
          const entries = await journalRes.json();
          setJournalEntry(entries.find(e => isToday(e.created_at)) ?? null);
        }

        // Lifestyle logs
        if (lifestyleRes.ok) {
          const logs = await lifestyleRes.json();
          const todayLog = logs.find(l => isToday(l.date));
          setLifestyleLog(todayLog ?? null);

          if (todayLog?.id) {
            const pr = await fetch(`${API_BASE}/api/lifestyle/logs/${todayLog.id}/predict/`, { headers });
            if (pr.ok) setLifestylePrediction(await pr.json());
          }
        }
      } catch {
        toast.error('Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, []);

  // ── Step completion ──────────────────────────────────────────────────────
  const STEPS = [
    { key: 'sleep',     label: 'Sleep Log',      icon: Moon,      done: !!sleepLog,     path: '/sleep-log' },
    { key: 'lifestyle', label: 'Lifestyle Log',  icon: Activity,  done: !!lifestyleLog, path: '/lifestyle' },
    { key: 'journal',   label: 'Journal Entry',  icon: BookOpen,  done: !!journalEntry, path: '/journal'   },
  ];
  const allDone   = STEPS.every(s => s.done);
  const doneCount = STEPS.filter(s => s.done).length;

  // ── Score ────────────────────────────────────────────────────────────────
  const score     = calcSleepScore({ sleepLog, sleepPrediction, lifestyleLog, lifestylePrediction, journalEntry });
  const scoreMeta = getScoreMeta(score);
  const issues    = allDone ? getDetectedIssues({ sleepLog, lifestyleLog, sleepPrediction, journalEntry }) : [];

  const sleepHours = sleepLog ? parseDurationToHours(sleepLog.calculated_sleep_duration) : 0;
  const sleepHoursFmt = sleepLog ? formatDuration(sleepLog.calculated_sleep_duration) : '—';

  const lifestyleChartData = lifestyleLog ? [
    {
      label: 'Exercise',
      value: lifestyleLog.WorkoutTime,
      rawValue: lifestyleLog.WorkoutTime,
      unit: 'h',
      maxValue: 3,
      color: '#5dcf8a',
      tooltipTitle: 'Workout time',
      tooltipValue: `${lifestyleLog.WorkoutTime}h`,
    },
    {
      label: 'Screen',
      value: lifestyleLog.PhoneTime,
      rawValue: lifestyleLog.PhoneTime,
      unit: 'h',
      maxValue: 5,
      color: '#7db8d8',
      tooltipTitle: 'Phone time',
      tooltipValue: `${lifestyleLog.PhoneTime}h`,
    },
    {
      label: 'Caffeine',
      value: lifestyleLog.CaffeineIntake / 100,
      rawValue: lifestyleLog.CaffeineIntake,
      unit: 'mg',
      maxValue: 3,
      color: '#fbbf24',
      tooltipTitle: 'Caffeine intake',
      tooltipValue: `${lifestyleLog.CaffeineIntake}mg`,
    },
    {
      label: 'Relax',
      value: lifestyleLog.RelaxationTime,
      rawValue: lifestyleLog.RelaxationTime,
      unit: 'h',
      maxValue: 2,
      color: '#b070e0',
      tooltipTitle: 'Relaxation time',
      tooltipValue: `${lifestyleLog.RelaxationTime}h`,
    },
    {
      label: 'Work',
      value: lifestyleLog.WorkHours,
      rawValue: lifestyleLog.WorkHours,
      unit: 'h',
      maxValue: 10,
      color: '#fb923c',
      tooltipTitle: 'Work hours',
      tooltipValue: `${lifestyleLog.WorkHours}h`,
    },
  ] : [];

  const CIRC = 2 * Math.PI * 70;

  // ── Recommendations ──────────────────────────────────────────────────────
  const getRecs = () => {
    const recs = [
      {
        title: 'Routine Optimizer',
        desc: 'Build a personalized bedtime routine based on your daily signals',
        icon: Sparkles,
        path: '/routine-optimizer',
        grad: 'linear-gradient(130deg, #1a3d6e, #4682b4)',
      },
      {
        title: 'Audio Therapy',
        desc: sleepPrediction?.prediction === 'insomnia'
          ? 'Therapeutic soundscapes specifically designed to ease insomnia'
          : 'Curated relaxing sounds for deeper, more restorative sleep',
        icon: Moon,
        path: '/audio-therapy',
        grad: 'linear-gradient(130deg, #1a1060, #5040c0)',
      },
    ];
    if (lifestyleLog?.PhoneTime > 3) {
      recs.push({
        title: 'Reduce Screen Time',
        desc: `${lifestyleLog.PhoneTime}h of screen time detected — aim for under 3h before bed`,
        icon: Smartphone,
        path: '/lifestyle',
        grad: 'linear-gradient(130deg, #0e4060, #0891b2)',
      });
    } else {
      recs.push({
        title: 'Boost Physical Activity',
        desc: 'Even 30 minutes of light exercise can significantly improve sleep quality',
        icon: Activity,
        path: '/lifestyle',
        grad: 'linear-gradient(130deg, #0e4060, #0891b2)',
      });
    }
    if (lifestyleLog?.CaffeineIntake > 150) {
      recs.push({
        title: 'Cut Caffeine After 2 PM',
        desc: `${lifestyleLog.CaffeineIntake}mg may delay sleep onset — try cutting intake in the afternoon`,
        icon: Coffee,
        path: '/lifestyle',
        grad: 'linear-gradient(130deg, #3d2200, #a05000)',
      });
    } else {
      recs.push({
        title: 'Weekly Wellness Report',
        desc: 'Review your sleep trends, wins, and recovery targets over time',
        icon: TrendingUp,
        path: '/weekly-report',
        grad: 'linear-gradient(130deg, #1a3d6e, #0891b2)',
      });
    }
    return recs;
  };

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="wellness-shell">
        <FloatingStars />
        <AppSidebar />
        <main className="wellness-content">
          <div className="dash-loading">
            <div className="dash-spinner" />
            <p className="dash-loading-text">Loading your dashboard…</p>
          </div>
        </main>
      </div>
    );
  }

  // ── Incomplete state ─────────────────────────────────────────────────────
  if (!allDone) {
    return (
      <div className="wellness-shell">
        <FloatingStars />
        <AppSidebar />
        <main className="wellness-content">
          <motion.div
            className="dash-wrap"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="dash-header">
              <span className="dash-chip">Dashboard</span>
              <h1 className="dash-title">Your Daily Health Snapshot</h1>
              <p className="dash-sub">
                Complete all 3 daily logs to unlock your personalized sleep insights.
              </p>
            </div>

            <GlassCard className="dash-checklist-card">
              <div className="dash-checklist-top">
                <div className="dash-checklist-icon-wrap">
                  <Sparkles size={19} />
                </div>
                <div className="dash-checklist-copy">
                  <h2 className="dash-checklist-title">Daily Log Progress</h2>
                  <p className="dash-checklist-sub">{doneCount} of 3 steps completed for today</p>
                </div>
                <div className="dash-progress-badge">{doneCount}<span>/3</span></div>
              </div>

              <div className="dash-progress-track">
                <motion.div
                  className="dash-progress-fill"
                  initial={{ width: 0 }}
                  animate={{ width: `${(doneCount / 3) * 100}%` }}
                  transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
                />
              </div>

              <div className="dash-steps-list">
                {STEPS.map((step, i) => {
                  const Icon = step.icon;
                  return (
                    <motion.div
                      key={step.key}
                      className={`dash-step ${step.done ? 'dash-step--done' : 'dash-step--pending'}`}
                      initial={{ opacity: 0, x: -14 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.09, duration: 0.38, ease: [0.22, 1, 0.36, 1] }}
                      onClick={() => !step.done && navigate(step.path)}
                      style={{ cursor: step.done ? 'default' : 'pointer' }}
                    >
                      <div className={`dash-step-icon ${step.done ? 'dash-step-icon--done' : 'dash-step-icon--pending'}`}>
                        <Icon size={17} />
                      </div>
                      <span className="dash-step-label">{step.label}</span>
                      <div className={`dash-step-badge ${step.done ? 'dash-step-badge--done' : 'dash-step-badge--pending'}`}>
                        {step.done
                          ? <><CheckCircle size={13} /> Completed</>
                          : <><Circle size={13} /> Log Now</>
                        }
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              <p className="dash-checklist-note">
                Your Sleep Quality Score and AI-detected insights will appear here once all three logs
                are submitted for today.
              </p>
            </GlassCard>
          </motion.div>
        </main>
      </div>
    );
  }

  // ── Full Dashboard ───────────────────────────────────────────────────────
  return (
    <div className="wellness-shell">
      <FloatingStars />
      <AppSidebar />
      <main className="wellness-content">
        <motion.div
          className="dash-wrap"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
        >
          {/* Header */}
          <div className="dash-header">
            <span className="dash-chip">Dashboard</span>
            <h1 className="dash-title">Sleep &amp; Wellness Snapshot</h1>
            <p className="dash-sub">
              {new Date().toLocaleDateString('en', { weekday: 'long', month: 'long', day: 'numeric' })}
              {' · '}All daily logs complete ✓
            </p>
          </div>

          {/* High-severity alert banner */}
          {issues.some(i => i.severity === 'high') && (
            <motion.div
              className="dash-alert-banner"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <AlertTriangle size={17} />
              <span>
                {issues.filter(i => i.severity === 'high').length} high-priority health issue(s) detected —
                review the details below.
              </span>
            </motion.div>
          )}

          {/* Top row: Score + Metrics */}
          <div className="dash-top-row">
            {/* Sleep Quality Score ring */}
            <motion.div
              initial={{ opacity: 0, scale: 0.88 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
            >
              <GlassCard className="dash-score-card">
                <h3 className="dash-card-title">Sleep Quality Score</h3>
                <div className="dash-ring-wrap">
                  <svg width="160" height="160" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="80" cy="80" r="70"
                      stroke="rgba(100,160,255,0.15)" strokeWidth="12" fill="none" />
                    <circle cx="80" cy="80" r="70"
                      stroke={scoreMeta.color}
                      strokeWidth="12"
                      fill="none"
                      strokeLinecap="round"
                      strokeDasharray={`${(score / 100) * CIRC} ${CIRC}`}
                      style={{
                        filter: `drop-shadow(0 0 10px ${scoreMeta.color})`,
                        transition: 'stroke-dasharray 1s ease',
                      }}
                    />
                  </svg>
                  <div className="dash-ring-center">
                    <span className="dash-ring-num" style={{ color: scoreMeta.color }}>{score}</span>
                    <span className="dash-ring-den">/ 100</span>
                  </div>
                </div>
                <p className="dash-ring-label" style={{ color: scoreMeta.color }}>{scoreMeta.label}</p>
                <p className="dash-ring-desc">Overall sleep quality today</p>
              </GlassCard>
            </motion.div>

            {/* Key Metrics column */}
            <motion.div
              className="dash-metrics-col"
              initial={{ opacity: 0, x: 18 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.18, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
            >
              {/* AI prediction */}
              <GlassCard className={`dash-metric ${sleepPrediction?.prediction === 'insomnia' ? 'dash-metric--danger' : 'dash-metric--good'}`}>
                <div className="dash-metric-row">
                  <div className="dash-metric-icon dash-metric-icon--moon">
                    <Moon size={18} />
                  </div>
                  <div className="dash-metric-body">
                    <p className="dash-metric-lbl">AI Prediction</p>
                    <p className="dash-metric-val">
                      {sleepPrediction
                        ? sleepPrediction.prediction === 'insomnia' ? 'Insomnia Detected' : 'No Insomnia'
                        : 'Pending'}
                    </p>
                    {sleepPrediction?.confidence != null && (
                      <p className="dash-metric-note">{Math.round(sleepPrediction.confidence * 100)}% confidence</p>
                    )}
                  </div>
                  {sleepPrediction?.prediction === 'insomnia'
                    ? <TrendingDown size={16} className="dash-metric-arrow dash-metric-arrow--down" />
                    : <TrendingUp   size={16} className="dash-metric-arrow dash-metric-arrow--up"   />
                  }
                </div>
              </GlassCard>

              {/* Sleep duration */}
              <GlassCard className="dash-metric">
                <div className="dash-metric-row">
                  <div className="dash-metric-icon dash-metric-icon--blue">
                    <Clock size={18} />
                  </div>
                  <div className="dash-metric-body">
                    <p className="dash-metric-lbl">Sleep Duration</p>
                    <p className="dash-metric-val">{sleepHoursFmt}</p>
                    <p className="dash-metric-note">Target: 7–9 hours</p>
                  </div>
                  {sleepHours >= 7 && sleepHours <= 9
                    ? <TrendingUp   size={16} className="dash-metric-arrow dash-metric-arrow--up"   />
                    : <TrendingDown size={16} className="dash-metric-arrow dash-metric-arrow--down" />
                  }
                </div>
              </GlassCard>

              {/* Journal mood */}
              <GlassCard className="dash-metric">
                <div className="dash-metric-row">
                  <div className="dash-metric-icon dash-metric-icon--purple">
                    <BookOpen size={18} />
                  </div>
                  <div className="dash-metric-body">
                    <p className="dash-metric-lbl">Journal Mood</p>
                    <p className="dash-metric-val">
                      {journalEntry?.predicted_mood
                        ? journalEntry.predicted_mood.charAt(0).toUpperCase() + journalEntry.predicted_mood.slice(1)
                        : 'Logged'}
                    </p>
                    <p className="dash-metric-note">Today's emotional state</p>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          </div>

          {/* Detected Issues */}
          {issues.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <GlassCard>
                <h3 className="dash-card-title dash-card-title--icon">
                  <Sparkles size={16} className="dash-card-icon" />
                  AI-Detected Issues
                </h3>
                <div className="dash-issues">
                  {issues.map((issue, i) => {
                    const Icon = issue.icon;
                    return (
                      <motion.div
                        key={i}
                        className={`dash-issue dash-issue--${issue.severity}`}
                        initial={{ opacity: 0, x: -12 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.34 + i * 0.07 }}
                      >
                        <Icon size={15} />
                        <span>{issue.text}</span>
                        {issue.severity === 'high'
                          ? <TrendingDown size={14} className="dash-issue-end" />
                          : <AlertTriangle size={14} className="dash-issue-end" />
                        }
                      </motion.div>
                    );
                  })}
                </div>
              </GlassCard>
            </motion.div>
          )}

          {/* Charts */}
          <div className="dash-charts-row">
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <GlassCard>
                <h3 className="dash-card-title">Sleep History (hours)</h3>
                {sleepHistory.length > 0
                  ? <SleepLineChart data={sleepHistory} />
                  : <p className="dash-empty">Not enough historical data yet.</p>
                }
              </GlassCard>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.48 }}
            >
              <GlassCard>
                <h3 className="dash-card-title">Lifestyle Factors</h3>
                <LifestyleBarChart data={lifestyleChartData} />
                <div className="dash-legend">
                  {lifestyleChartData.map(d => (
                    <span key={d.label} className="dash-legend-item">
                      <span className="dash-legend-dot" style={{ background: d.color }} />
                      {d.label}
                    </span>
                  ))}
                </div>
              </GlassCard>
            </motion.div>
          </div>

          {/* Recommendations */}
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.56 }}
          >
            <h2 className="dash-section-title">Personalized Recommendations</h2>
            <div className="dash-recs-grid">
              {getRecs().map((rec, i) => {
                const Icon = rec.icon;
                return (
                  <GlassCard
                    key={i}
                    className="dash-rec"
                    onClick={() => navigate(rec.path)}
                  >
                    <div className="dash-rec-row">
                      <div className="dash-rec-icon" style={{ background: rec.grad }}>
                        <Icon size={19} />
                      </div>
                      <div className="dash-rec-copy">
                        <p className="dash-rec-title">{rec.title}</p>
                        <p className="dash-rec-desc">{rec.desc}</p>
                      </div>
                      <TrendingUp size={15} className="dash-rec-arrow" />
                    </div>
                  </GlassCard>
                );
              })}
            </div>
          </motion.div>
        </motion.div>
      </main>
    </div>
  );
}
