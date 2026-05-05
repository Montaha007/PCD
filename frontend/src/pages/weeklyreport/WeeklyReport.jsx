import { useState, useEffect, useRef, useMemo } from 'react';
import { GlassCard } from '../../components/GlassCard';
import AppSidebar from '../../components/AppSidebar';
import FloatingStars from '../../components/FloatingStars';
import { motion } from 'motion/react';
import {
  Moon, Activity, BookOpen, TrendingUp, TrendingDown,
  Minus, AlertTriangle, CheckCircle, Award, Calendar, Coffee,
  Smartphone, Zap,
} from 'lucide-react';
import { toast } from 'sonner';
import './WeeklyReport.css';

const API_BASE = import.meta.env.VITE_API_BASE;

const MOOD_META = {
  normal:               { color: '#5dcf8a', label: 'Normal' },
  anxiety:              { color: '#fbbf24', label: 'Anxiety' },
  stress:               { color: '#fb923c', label: 'Stress' },
  depression:           { color: '#f87171', label: 'Depression' },
  bipolar:              { color: '#e879f9', label: 'Bipolar' },
  suicidal:             { color: '#ef4444', label: 'Suicidal' },
  personality_disorder: { color: '#a78bfa', label: 'Personality' },
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function localDateISO(d = new Date()) {
  return [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, '0'),
    String(d.getDate()).padStart(2, '0'),
  ].join('-');
}

function parseDurationToHours(str) {
  if (!str) return 0;
  const dayMatch = str.match(/^(\d+) days?,\s*/);
  const extra = dayMatch ? parseInt(dayMatch[1], 10) * 24 : 0;
  const timePart = str.replace(/^\d+ days?,\s*/, '');
  const [h, m] = timePart.split(':').map(Number);
  return extra + (h || 0) + (m || 0) / 60;
}

function formatHours(h) {
  if (h == null || h === 0) return '—';
  const hrs = Math.floor(h);
  const mins = Math.round((h - hrs) * 60);
  return mins > 0 ? `${hrs}h ${String(mins).padStart(2, '0')}min` : `${hrs}h`;
}

function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }

function calcDayScore(hours, isInsomnia) {
  const base = Math.min((hours / 7) * 100, 100);
  const penalty = isInsomnia ? 20 : 0;
  return Math.round(Math.min(Math.max(base - penalty, 0), 100));
}

function computeStdDev(arr) {
  if (arr.length < 2) return 0;
  const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
  return Math.sqrt(arr.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / arr.length);
}

// ── Tooltip ──────────────────────────────────────────────────────────────────

function ChartTooltip({ tooltip }) {
  if (!tooltip) return null;
  return (
    <div
      className="wr-tooltip"
      style={{ left: tooltip.x, top: tooltip.y, transform: 'translate(-50%, calc(-100% - 12px))' }}
      role="status"
      aria-live="polite"
    >
      <div className="wr-tooltip-title">{tooltip.title}</div>
      {tooltip.lines?.map((l, i) => <div key={i} className="wr-tooltip-line">{l}</div>)}
    </div>
  );
}

// ── Combined Sleep + Score Chart ─────────────────────────────────────────────

function WeekCombinedChart({ data }) {
  const W = 560, H = 200;
  const pad = { t: 20, b: 32, l: 10, r: 36 };
  const iW = W - pad.l - pad.r;
  const iH = H - pad.t - pad.b;

  const wrapRef  = useRef(null);
  const [tooltip, setTooltip]   = useState(null);
  const [hoverIdx, setHoverIdx] = useState(null);

  const MAX_H  = 10;
  const SLOT   = iW / data.length;
  const bW     = SLOT * 0.46;
  const barX   = i => pad.l + i * SLOT + (SLOT - bW) / 2;
  const xOf    = i => pad.l + i * SLOT + SLOT / 2;
  const yOf    = pct => pad.t + iH - (pct / 100) * iH;
  const REF_Y  = yOf((7 / MAX_H) * 100);

  const scorePoints = data
    .map((d, i) => d.score != null ? { i, x: xOf(i), y: yOf(d.score) } : null)
    .filter(Boolean);

  const scorePath = scorePoints.length > 1
    ? scorePoints.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
    : null;

  const handleLeave = () => { setTooltip(null); setHoverIdx(null); };

  const moveTooltip = e => {
    if (!wrapRef.current) return;
    const r = wrapRef.current.getBoundingClientRect();
    setTooltip(prev => prev
      ? { ...prev, x: clamp(e.clientX - r.left, 40, r.width - 40), y: clamp(e.clientY - r.top, 24, r.height - 24) }
      : prev
    );
  };

  const showTooltip = (e, i) => {
    if (!wrapRef.current) return;
    const r = wrapRef.current.getBoundingClientRect();
    const d = data[i];
    setHoverIdx(i);
    setTooltip({
      x: clamp(e.clientX - r.left, 40, r.width - 40),
      y: clamp(e.clientY - r.top, 24, r.height - 24),
      title: d.label,
      lines: d.hours != null
        ? [`Sleep: ${formatHours(d.hours)}`, `Score: ${d.score}/100`, d.isInsomnia ? 'Insomnia detected' : 'No insomnia']
        : ['No data logged'],
    });
  };

  return (
    <div className="wr-chart-wrap" ref={wrapRef} onPointerLeave={handleLeave}>
      <ChartTooltip tooltip={tooltip} />
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ overflow: 'visible' }}>
        <defs>
          <linearGradient id="wrBarNormal" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6ea8d8" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#6ea8d8" stopOpacity="0.35" />
          </linearGradient>
          <linearGradient id="wrBarShort" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#fbbf24" stopOpacity="0.35" />
          </linearGradient>
          <linearGradient id="wrBarInsomnia" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f87171" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#f87171" stopOpacity="0.35" />
          </linearGradient>
        </defs>

        {[0, 0.25, 0.5, 0.75, 1].map(f => (
          <line key={f}
            x1={pad.l} y1={pad.t + iH * f} x2={W - pad.r} y2={pad.t + iH * f}
            stroke="rgba(100,160,255,0.08)" strokeWidth="1"
          />
        ))}

        {/* 7h reference line */}
        <line x1={pad.l} x2={W - pad.r} y1={REF_Y} y2={REF_Y}
          stroke="rgba(93,207,138,0.35)" strokeWidth="1" strokeDasharray="5 4" />
        <text x={W - pad.r + 5} y={REF_Y + 4} fontSize="9" fill="#5dcf8a" opacity="0.8">7h</text>

        {/* Bars */}
        {data.map((d, i) => {
          const isHovered = i === hoverIdx;
          if (d.hours == null) {
            return (
              <g key={i} onPointerEnter={e => showTooltip(e, i)} onPointerMove={moveTooltip} style={{ cursor: 'default' }}>
                <rect x={barX(i)} y={pad.t} width={bW} height={iH} rx="4" fill="rgba(100,160,255,0.04)" />
                <text x={xOf(i)} y={pad.t + iH / 2 + 4} textAnchor="middle" fontSize="9" fill="#3a4a60">—</text>
              </g>
            );
          }
          const pct  = Math.min((d.hours / MAX_H) * 100, 100);
          const bH   = Math.max((pct / 100) * iH, 3);
          const barY = pad.t + iH - bH;
          const fill = d.isInsomnia ? 'url(#wrBarInsomnia)' : d.hours >= 7 ? 'url(#wrBarNormal)' : 'url(#wrBarShort)';
          return (
            <g key={i} onPointerEnter={e => showTooltip(e, i)} onPointerMove={moveTooltip} style={{ cursor: 'default' }}>
              <rect x={barX(i)} y={pad.t} width={bW} height={iH} rx="4" fill="rgba(100,160,255,0.04)" />
              <rect x={barX(i)} y={barY} width={bW} height={bH} rx="4"
                fill={fill} opacity={isHovered ? 1 : 0.82} className="wr-bar"
              />
              {isHovered && (
                <rect x={barX(i) - 1} y={pad.t - 1} width={bW + 2} height={iH + 2} rx="5"
                  fill="transparent" stroke="rgba(167,199,231,0.3)" strokeWidth="1" />
              )}
            </g>
          );
        })}

        {/* Score line */}
        {scorePath && (
          <path d={scorePath} fill="none" stroke="#c084fc" strokeWidth="2.2"
            strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
        )}
        {scorePoints.map(p => {
          const isHovered = p.i === hoverIdx;
          return (
            <g key={p.i} onPointerEnter={e => showTooltip(e, p.i)} onPointerMove={moveTooltip} style={{ cursor: 'default' }}>
              <circle cx={p.x} cy={p.y} r={isHovered ? 8 : 6} fill="transparent" />
              <circle cx={p.x} cy={p.y} r={isHovered ? 5.5 : 4}
                fill={isHovered ? '#e0a0ff' : '#c084fc'}
                stroke="#040010" strokeWidth={isHovered ? 2.5 : 2}
              />
            </g>
          );
        })}

        {data.map((d, i) => (
          <text key={i} x={xOf(i)} y={H - 8} textAnchor="middle" fill="#8fa8c8" fontSize="10">
            {d.short}
          </text>
        ))}
      </svg>

      <div className="wr-chart-legend">
        {[
          { color: '#6ea8d8', label: '≥7h sleep' },
          { color: '#fbbf24', label: '<7h sleep' },
          { color: '#f87171', label: 'Insomnia' },
          { color: '#c084fc', label: 'Quality score', line: true },
        ].map(item => (
          <span key={item.label} className="wr-legend-item">
            <span className={`wr-legend-dot${item.line ? ' wr-legend-dot--line' : ''}`} style={{ background: item.color }} />
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function WeeklyReport() {
  const [loading, setLoading]               = useState(true);
  const [sleepLogs, setSleepLogs]           = useState([]);
  const [predictions, setPredictions]       = useState({});
  const [lifestyleLogs, setLifestyleLogs]   = useState([]);
  const [journalEntries, setJournalEntries] = useState([]);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      if (!token) { setLoading(false); return; }
      const headers = { Authorization: `Bearer ${token}` };

      const cutoff = (() => {
        const d = new Date();
        d.setDate(d.getDate() - 6);
        return localDateISO(d);
      })();

      try {
        const [sleepRes, journalRes, lifestyleRes] = await Promise.all([
          fetch(`${API_BASE}/api/sleeplog/`,       { headers }),
          fetch(`${API_BASE}/api/mood/entries/`,   { headers }),
          fetch(`${API_BASE}/api/lifestyle/logs/`, { headers }),
        ]);

        if (sleepRes.ok) {
          const all    = await sleepRes.json();
          const recent = all
            .filter(l => (l.created_at || l.sleep_time || '').slice(0, 10) >= cutoff)
            .slice(0, 7);
          setSleepLogs(recent);

          const predResults = await Promise.allSettled(
            recent.map(l =>
              fetch(`${API_BASE}/api/sleeplog/${l.id}/predict/`, { headers })
                .then(r => r.ok ? r.json() : null)
                .catch(() => null)
            )
          );
          const pMap = {};
          recent.forEach((l, idx) => {
            const res = predResults[idx];
            if (res.status === 'fulfilled' && res.value) pMap[l.id] = res.value;
          });
          setPredictions(pMap);
        }

        if (journalRes.ok) {
          const all = await journalRes.json();
          setJournalEntries(all.filter(e => (e.created_at || '').slice(0, 10) >= cutoff));
        }

        if (lifestyleRes.ok) {
          const all = await lifestyleRes.json();
          setLifestyleLogs(all.filter(l => (l.date || '').slice(0, 10) >= cutoff));
        }
      } catch {
        toast.error('Failed to load weekly data.');
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  // ── Week days array ────────────────────────────────────────────────────────
  const weekDays = useMemo(() => (
    Array.from({ length: 7 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      return {
        iso:   localDateISO(d),
        short: d.toLocaleDateString('en', { weekday: 'short' }),
        label: d.toLocaleDateString('en', { month: 'short', day: 'numeric' }),
      };
    })
  ), []);

  // ── Per-day sleep ──────────────────────────────────────────────────────────
  const sleepByDay = useMemo(() => (
    weekDays.map(day => {
      const log  = sleepLogs.find(l => (l.created_at || l.sleep_time || '').slice(0, 10) === day.iso);
      const pred = log ? predictions[log.id] : null;
      const hours = log
        ? parseFloat(parseDurationToHours(log.calculated_sleep_duration).toFixed(1))
        : null;
      const isInsomnia = pred?.prediction === 'insomnia';
      const score = hours != null ? calcDayScore(hours, isInsomnia) : null;
      return { ...day, log, pred, hours, isInsomnia, score };
    })
  ), [weekDays, sleepLogs, predictions]);

  // ── Aggregate stats ────────────────────────────────────────────────────────
  const stats = useMemo(() => {
    const days = sleepByDay.filter(d => d.hours != null);
    if (!days.length) return null;

    const hoursArr  = days.map(d => d.hours);
    const scoresArr = days.map(d => d.score);
    const avgHours  = hoursArr.reduce((a, b) => a + b, 0) / hoursArr.length;
    const avgScore  = Math.round(scoresArr.reduce((a, b) => a + b, 0) / scoresArr.length);
    const sd        = computeStdDev(hoursArr);
    const consistencyPct = Math.round(Math.max(0, 100 - sd * 22));

    const mid      = Math.floor(days.length / 2);
    const firstAvg = mid > 0
      ? days.slice(0, mid).reduce((s, d) => s + d.score, 0) / mid
      : null;
    const lastAvg  = days.length - mid > 0
      ? days.slice(mid).reduce((s, d) => s + d.score, 0) / (days.length - mid)
      : null;
    const trendDelta = firstAvg != null && lastAvg != null
      ? Math.round(lastAvg - firstAvg)
      : null;

    return {
      avgHours,
      avgScore,
      consistencyPct,
      sd,
      trendDelta,
      insomniaCount: days.filter(d => d.isInsomnia).length,
      optimalCount:  days.filter(d => d.hours >= 7 && d.hours <= 9).length,
      daysLogged:    days.length,
    };
  }, [sleepByDay]);

  // ── Lifestyle averages ─────────────────────────────────────────────────────
  const lifestyleStats = useMemo(() => {
    if (!lifestyleLogs.length) return null;
    const avg = arr => arr.reduce((a, b) => a + b, 0) / arr.length;
    return {
      avgCaffeine: Math.round(avg(lifestyleLogs.map(l => l.CaffeineIntake   || 0))),
      avgWorkout:  +(avg(lifestyleLogs.map(l => l.WorkoutTime     || 0))).toFixed(1),
      avgScreen:   +(avg(lifestyleLogs.map(l => l.PhoneTime       || 0))).toFixed(1),
      avgRelax:    +(avg(lifestyleLogs.map(l => l.RelaxationTime  || 0))).toFixed(1),
      days:        lifestyleLogs.length,
    };
  }, [lifestyleLogs]);

  // ── Mood distribution ──────────────────────────────────────────────────────
  const moodStats = useMemo(() => {
    const counts = {};
    journalEntries.forEach(e => {
      if (e.predicted_mood) {
        const m = e.predicted_mood.toLowerCase();
        counts[m] = (counts[m] || 0) + 1;
      }
    });
    return { counts, total: Object.values(counts).reduce((a, b) => a + b, 0), days: journalEntries.length };
  }, [journalEntries]);

  // ── Insights ───────────────────────────────────────────────────────────────
  const insights = useMemo(() => {
    if (!stats) return [];
    const list = [];
    const { avgHours, sd, trendDelta, insomniaCount, daysLogged } = stats;

    if (avgHours >= 7)
      list.push({ type: 'positive', icon: CheckCircle, title: 'Healthy Sleep Duration',    desc: `Average of ${formatHours(avgHours)} per night meets the 7–9 hour recommendation.` });
    else if (avgHours >= 6)
      list.push({ type: 'warning',  icon: AlertTriangle, title: 'Slightly Short on Sleep', desc: `Averaging ${formatHours(avgHours)} — try going to bed 30–45 min earlier to reach 7 hours.` });
    else
      list.push({ type: 'high',     icon: AlertTriangle, title: 'Sleep Deficit Detected',  desc: `Only ${formatHours(avgHours)} average per night. Chronic sleep deprivation affects memory, mood, and immunity.` });

    if (sd < 0.8 && daysLogged >= 4)
      list.push({ type: 'positive', icon: CheckCircle,   title: 'Consistent Sleep Schedule', desc: 'Low variation in duration — a stable circadian rhythm supports deeper, more restorative sleep.' });
    else if (sd > 1.5)
      list.push({ type: 'warning',  icon: AlertTriangle, title: 'Irregular Sleep Pattern',   desc: `Duration varies by ±${sd.toFixed(1)}h across the week, which disrupts your body clock.` });

    if (trendDelta != null && trendDelta > 5)
      list.push({ type: 'positive', icon: TrendingUp,   title: 'Sleep Quality Improving', desc: `Scores rose by ${trendDelta} points in the second half of the week. Keep the momentum.` });
    else if (trendDelta != null && trendDelta < -5)
      list.push({ type: 'warning',  icon: TrendingDown, title: 'Sleep Quality Declining',  desc: `Scores dropped ${Math.abs(trendDelta)} points as the week progressed — review end-of-week habits.` });

    if (insomniaCount > 0)
      list.push({ type: 'high', icon: Zap, title: 'Insomnia Signals Detected', desc: `AI flagged insomnia on ${insomniaCount} of ${daysLogged} logged nights. Try Audio Therapy or the Routine Optimizer.` });

    if (lifestyleStats?.avgCaffeine > 150)
      list.push({ type: 'warning', icon: Coffee,     title: 'High Caffeine Intake', desc: `Average ${lifestyleStats.avgCaffeine}mg/day — avoid caffeine after 2 PM to protect sleep onset.` });
    if (lifestyleStats?.avgScreen > 3)
      list.push({ type: 'warning', icon: Smartphone, title: 'High Screen Time',    desc: `${lifestyleStats.avgScreen}h/day average screen time may suppress melatonin. Try a digital wind-down routine.` });
    if (lifestyleStats?.avgWorkout >= 0.5)
      list.push({ type: 'positive', icon: Activity,  title: 'Active Week',         desc: `Averaging ${lifestyleStats.avgWorkout}h of exercise daily — physical activity is a strong sleep quality predictor.` });

    return list;
  }, [stats, lifestyleStats]);

  // ── Log streak ────────────────────────────────────────────────────────────
  const logStreak = useMemo(() => {
    let streak = 0;
    for (let i = 0; i < 7; i++) {
      const d = new Date(); d.setDate(d.getDate() - i);
      const iso = localDateISO(d);
      const has = sleepLogs.some(l => (l.created_at || l.sleep_time || '').slice(0, 10) === iso)
               || lifestyleLogs.some(l => (l.date || '').slice(0, 10) === iso)
               || journalEntries.some(e => (e.created_at || '').slice(0, 10) === iso);
      if (has) streak++; else break;
    }
    return streak;
  }, [sleepLogs, lifestyleLogs, journalEntries]);

  const weekRangeLabel = (() => {
    const start = new Date(); start.setDate(start.getDate() - 6);
    const end   = new Date();
    return `${start.toLocaleDateString('en', { month: 'short', day: 'numeric' })} – ${end.toLocaleDateString('en', { month: 'short', day: 'numeric', year: 'numeric' })}`;
  })();

  const hasAnyData = sleepLogs.length > 0 || lifestyleLogs.length > 0 || journalEntries.length > 0;

  // ── Loading ────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="wellness-shell">
        <FloatingStars />
        <AppSidebar />
        <main className="wellness-content">
          <div className="dash-loading">
            <div className="dash-spinner" />
            <p className="dash-loading-text">Building your weekly report…</p>
          </div>
        </main>
      </div>
    );
  }

  // ── No data ────────────────────────────────────────────────────────────────
  if (!hasAnyData) {
    return (
      <div className="wellness-shell">
        <FloatingStars />
        <AppSidebar />
        <main className="wellness-content">
          <div className="dash-prefill-shell">
            <div className="dash-prefill-inner">
              <div className="dash-header" style={{ textAlign: 'center' }}>
                <span className="dash-chip">Weekly Report</span>
                <h1 className="dash-title">No Data Yet</h1>
                <p className="dash-sub">
                  Start logging Sleep, Lifestyle, and Journal entries to generate your weekly report.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // ── Full Report ────────────────────────────────────────────────────────────
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
            <span className="dash-chip">Weekly Report</span>
            <h1 className="dash-title">Your Week in Review</h1>
            <p className="dash-sub">{weekRangeLabel}</p>
          </div>

          {/* 4-stat row */}
          <div className="wr-stats-row">
            {[
              {
                icon: Moon, delay: 0.1,
                iconBg: 'linear-gradient(130deg, #1a1060, #4682b4)',
                label: 'Avg Sleep / Night',
                value: stats ? formatHours(stats.avgHours) : '—',
                note:  stats ? `${stats.daysLogged}/7 days logged` : 'No sleep data this week',
                valueColor: null,
              },
              {
                icon: Calendar, delay: 0.18,
                iconBg: 'linear-gradient(130deg, #1a3d6e, #0891b2)',
                label: 'Sleep Consistency',
                value: stats ? `${stats.consistencyPct}%` : '—',
                note:  stats ? `±${stats.sd.toFixed(1)}h variation` : 'Log more days',
                valueColor: stats?.consistencyPct >= 75 ? '#5dcf8a' : stats?.consistencyPct >= 50 ? '#fbbf24' : '#f87171',
              },
              {
                icon: stats?.trendDelta > 0 ? TrendingUp : stats?.trendDelta < 0 ? TrendingDown : Minus,
                delay: 0.26,
                iconBg: stats?.trendDelta > 0
                  ? 'linear-gradient(130deg, #0e3d20, #1a7a40)'
                  : stats?.trendDelta < 0
                    ? 'linear-gradient(130deg, #3d0e0e, #7a1a1a)'
                    : 'linear-gradient(130deg, #1a2540, #2a3d5a)',
                label: 'Week Trend',
                value: stats?.trendDelta != null ? `${stats.trendDelta > 0 ? '+' : ''}${stats.trendDelta} pts` : '—',
                note:  'Score: first half vs second half',
                valueColor: stats?.trendDelta > 0 ? '#5dcf8a' : stats?.trendDelta < 0 ? '#f87171' : '#9bb0cc',
              },
              {
                icon: Award, delay: 0.34,
                iconBg: 'linear-gradient(130deg, #3a1060, #8040c0)',
                label: 'Avg Quality Score',
                value: stats ? `${stats.avgScore}/100` : '—',
                note:  stats?.optimalCount ? `${stats.optimalCount} optimal night${stats.optimalCount !== 1 ? 's' : ''}` : 'No optimal nights yet',
                valueColor: null,
              },
            ].map(({ icon: Icon, delay, iconBg, label, value, note, valueColor }) => (
              <motion.div key={label} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}>
                <GlassCard className="wr-stat-card">
                  <div className="wr-stat-icon" style={{ background: iconBg }}>
                    <Icon size={18} />
                  </div>
                  <div className="wr-stat-body">
                    <p className="wr-stat-lbl">{label}</p>
                    <p className="wr-stat-val" style={valueColor ? { color: valueColor } : {}}>{value}</p>
                    <p className="wr-stat-note">{note}</p>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>

          {/* Combined chart */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.38 }}>
            <GlassCard>
              <div className="wr-chart-header">
                <h3 className="dash-card-title" style={{ margin: 0 }}>Sleep Duration &amp; Quality Score</h3>
                <span className="wr-chart-sub">Bars = hours slept · Purple line = quality score</span>
              </div>
              <WeekCombinedChart data={sleepByDay} />
            </GlassCard>
          </motion.div>

          {/* Lifestyle + Mood */}
          <div className="wr-two-col">
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.44 }}>
              <GlassCard>
                <h3 className="dash-card-title dash-card-title--icon">
                  <Activity size={16} className="dash-card-icon" />
                  Lifestyle Averages
                </h3>
                {lifestyleStats ? (
                  <div className="wr-bar-list">
                    {[
                      { label: 'Workout',    value: lifestyleStats.avgWorkout,  display: `${lifestyleStats.avgWorkout}h`,         max: 3,   color: '#5dcf8a' },
                      { label: 'Screen',     value: lifestyleStats.avgScreen,   display: `${lifestyleStats.avgScreen}h`,           max: 8,   color: lifestyleStats.avgScreen > 3 ? '#f87171' : '#7db8d8' },
                      { label: 'Caffeine',   value: lifestyleStats.avgCaffeine, display: `${lifestyleStats.avgCaffeine}mg`,        max: 400, color: lifestyleStats.avgCaffeine > 150 ? '#fbbf24' : '#5dcf8a' },
                      { label: 'Relaxation', value: lifestyleStats.avgRelax,    display: `${lifestyleStats.avgRelax}h`,            max: 3,   color: '#b070e0' },
                    ].map(item => (
                      <div key={item.label} className="wr-bar-row">
                        <span className="wr-bar-label">{item.label}</span>
                        <div className="wr-bar-track">
                          <motion.div
                            className="wr-bar-fill"
                            style={{ background: item.color }}
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min((item.value / item.max) * 100, 100)}%` }}
                            transition={{ duration: 0.8, delay: 0.5 }}
                          />
                        </div>
                        <span className="wr-bar-val">{item.display}<span className="wr-bar-unit">/day</span></span>
                      </div>
                    ))}
                    <p className="wr-sub-note">Based on {lifestyleStats.days} day{lifestyleStats.days !== 1 ? 's' : ''} logged</p>
                  </div>
                ) : (
                  <p className="dash-empty">No lifestyle data logged this week.</p>
                )}
              </GlassCard>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.48 }}>
              <GlassCard>
                <h3 className="dash-card-title dash-card-title--icon">
                  <BookOpen size={16} className="dash-card-icon" />
                  Mood This Week
                </h3>
                {moodStats.total > 0 ? (
                  <div className="wr-bar-list">
                    {Object.entries(moodStats.counts)
                      .sort((a, b) => b[1] - a[1])
                      .map(([mood, count]) => {
                        const meta = MOOD_META[mood] || { color: '#9bb0cc', label: mood };
                        const pct  = Math.round((count / moodStats.total) * 100);
                        return (
                          <div key={mood} className="wr-bar-row">
                            <span className="wr-bar-label">{meta.label}</span>
                            <div className="wr-bar-track">
                              <motion.div
                                className="wr-bar-fill"
                                style={{ background: meta.color }}
                                initial={{ width: 0 }}
                                animate={{ width: `${pct}%` }}
                                transition={{ duration: 0.75, delay: 0.55 }}
                              />
                            </div>
                            <span className="wr-bar-val" style={{ color: meta.color }}>{count}×</span>
                          </div>
                        );
                      })}
                    <p className="wr-sub-note">{moodStats.days} journal entr{moodStats.days !== 1 ? 'ies' : 'y'} this week</p>
                  </div>
                ) : (
                  <p className="dash-empty">No journal entries logged this week.</p>
                )}
              </GlassCard>
            </motion.div>
          </div>

          {/* Insights */}
          {insights.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.54 }}>
              <GlassCard>
                <h3 className="dash-card-title dash-card-title--icon">
                  <Zap size={16} className="dash-card-icon" />
                  Weekly Insights
                </h3>
                <div className="wr-insights">
                  {insights.map((item, i) => {
                    const Icon = item.icon;
                    return (
                      <motion.div
                        key={i}
                        className={`wr-insight wr-insight--${item.type}`}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.58 + i * 0.06 }}
                      >
                        <Icon size={15} className="wr-insight-icon" />
                        <div>
                          <p className="wr-insight-title">{item.title}</p>
                          <p className="wr-insight-desc">{item.desc}</p>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </GlassCard>
            </motion.div>
          )}

          {/* Achievements */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
            <h2 className="dash-section-title">Weekly Achievements</h2>
            <div className="wr-achievements">
              {[
                { icon: Moon,     color: '#5dcf8a', label: 'Optimal Sleep Nights', desc: '7–9 hours',          value: stats?.optimalCount ?? 0,   total: 7 },
                { icon: BookOpen, color: '#b070e0', label: 'Journal Entries',      desc: 'days logged',        value: moodStats.days,             total: 7 },
                { icon: Activity, color: '#7db8d8', label: 'Lifestyle Logs',       desc: 'days logged',        value: lifestyleStats?.days ?? 0,  total: 7 },
                { icon: Award,    color: '#fbbf24', label: 'Current Log Streak',   desc: 'consecutive days',   value: logStreak,                  total: 7 },
              ].map((ach, i) => {
                const Icon = ach.icon;
                const pct  = Math.round((ach.value / ach.total) * 100);
                return (
                  <GlassCard key={i} className="wr-ach-card">
                    <div className="wr-ach-top">
                      <div className="wr-ach-icon" style={{ color: ach.color }}><Icon size={17} /></div>
                      <span className="wr-ach-val" style={{ color: ach.color }}>
                        {ach.value}<span className="wr-ach-total">/{ach.total}</span>
                      </span>
                    </div>
                    <p className="wr-ach-label">{ach.label}</p>
                    <p className="wr-ach-desc">{ach.desc}</p>
                    <div className="wr-ach-track">
                      <motion.div
                        className="wr-ach-fill"
                        style={{ background: ach.color }}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.9, delay: 0.65 + i * 0.08, ease: [0.22, 1, 0.36, 1] }}
                      />
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
