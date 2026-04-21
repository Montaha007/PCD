import { useState } from 'react';
import { GlassCard } from '../../components/GlassCard';
import { OnboardingProgress } from '../../components/OnboardingProgress';
import { Label } from '../../components/ui/label';
import { Button } from '../../components/ui/button';
import { Switch } from '../../components/ui/switch';
import { Moon, Clock, Star, AlertCircle, Check, Timer, CalendarClock } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { toast } from 'sonner';
import AppSidebar from '../../components/AppSidebar';
import './SleepLog.css';

const API_BASE = import.meta.env.VITE_API_BASE;

const DEFAULT_FORM = {
  sleep_time: '',
  wake_up_time: '',
  satisfaction_of_sleep: false,
  late_night_sleep: false,
  wake_up_frequently: false,
  sleep_at_daytime: false,
  drowsiness_tiredness: false,
  recent_psychological_attack: false,
  afraid_of_sleeping: false,
};

// Format Django DurationField string ("H:MM:SS" or "D day(s), H:MM:SS") → "Xh YYmin"
function formatDuration(str) {
  if (!str) return null;
  const dayMatch = str.match(/^(\d+) days?,\s*/);
  const extraHours = dayMatch ? parseInt(dayMatch[1], 10) * 24 : 0;
  const timePart = str.replace(/^\d+ days?,\s*/, '');
  const [h, m] = timePart.split(':').map(Number);
  const total = h + extraHours;
  return `${total}h ${String(m).padStart(2, '0')}min`;
}

export default function SleepLog() {
  const [formData, setFormData] = useState(DEFAULT_FORM);
  const [savedLog, setSavedLog] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const set = (key, val) => setFormData((prev) => ({ ...prev, [key]: val }));

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.sleep_time || !formData.wake_up_time) {
      toast.error('Please fill in both your bedtime and wake-up time.');
      return;
    }
    if (formData.wake_up_time <= formData.sleep_time) {
      toast.error('Wake-up time must be after bedtime.');
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Session expired. Please log in again.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/sleeplog/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const msg = Object.values(err).flat().join(' ') || 'Failed to save sleep log.';
        toast.error(msg);
        return;
      }

      const data = await res.json();
      setSavedLog(data);
      toast.success('Sleep data saved successfully!');
    } catch {
      toast.error('Could not reach the server.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="wellness-shell">
      <AppSidebar />
      <main className="wellness-content">
        <div className="sleep-log-wrap">
          <OnboardingProgress />

          <div className="sleep-log-header" style={{ marginTop: '28px' }}>
            <h1 className="sleep-log-title">
              <Moon size={30} strokeWidth={1.8} />
              Sleep Log
            </h1>
            <p className="sleep-log-sub">
              Track your sleep schedule and night quality
            </p>
          </div>

          {/* Result banner — appears after successful save */}
          <AnimatePresence>
            {savedLog && (
              <motion.div
                className="sl-result-banner"
                initial={{ opacity: 0, y: -12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.3 }}
              >
                <div className="sl-result-row">
                  <Timer size={16} strokeWidth={1.8} className="sl-icon-primary" />
                  <span className="sl-result-label">Sleep duration</span>
                  <strong className="sl-result-value">
                    {formatDuration(savedLog.calculated_sleep_duration)}
                  </strong>
                </div>
                <div className="sl-result-divider" />
                <div className="sl-result-row">
                  <CalendarClock size={16} strokeWidth={1.8} className="sl-icon-accent" />
                  <span className="sl-result-label">Problems for</span>
                  <strong className="sl-result-value">
                    {savedLog.duration_of_problems} year{savedLog.duration_of_problems > 1 ? 's' : ''}
                  </strong>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="sleep-log-form">

            {/* Sleep time + Wake-up time */}
            <GlassCard>
              <div className="sl-time-grid">
                <div className="sl-time-field">
                  <div className="sl-card-label-row">
                    <Moon size={16} strokeWidth={1.8} className="sl-icon-primary" />
                    <Label htmlFor="sleep_time">Bedtime</Label>
                  </div>
                  <input
                    id="sleep_time"
                    type="datetime-local"
                    className="sl-datetime-input"
                    value={formData.sleep_time}
                    onChange={(e) => set('sleep_time', e.target.value)}
                    required
                  />
                </div>
                <div className="sl-time-field">
                  <div className="sl-card-label-row">
                    <Clock size={16} strokeWidth={1.8} className="sl-icon-primary" />
                    <Label htmlFor="wake_up_time">Wake-up time</Label>
                  </div>
                  <input
                    id="wake_up_time"
                    type="datetime-local"
                    className="sl-datetime-input"
                    value={formData.wake_up_time}
                    onChange={(e) => set('wake_up_time', e.target.value)}
                    required
                  />
                </div>
              </div>
            </GlassCard>

            {/* Satisfaction + all boolean switches */}
            <GlassCard>
              <h3 className="sl-problems-header">
                <AlertCircle size={18} strokeWidth={1.8} className="sl-icon-alert" />
                Sleep Quality &amp; Issues
              </h3>
              <div className="sl-switch-rows">
                {[
                  { id: 'satisf',  key: 'satisfaction_of_sleep',      label: 'Satisfied with sleep',          icon: Star },
                  { id: 'lateN',   key: 'late_night_sleep',            label: 'Late-night bedtime' },
                  { id: 'wakeup',  key: 'wake_up_frequently',          label: 'Waking up frequently' },
                  { id: 'daytime', key: 'sleep_at_daytime',            label: 'Sleeping during the day' },
                  { id: 'drowsy',  key: 'drowsiness_tiredness',        label: 'Drowsiness / Fatigue' },
                  { id: 'psych',   key: 'recent_psychological_attack', label: 'Recent psychological episode' },
                  { id: 'afraid',  key: 'afraid_of_sleeping',          label: 'Afraid of falling asleep' },
                ].map(({ id, key, label, icon: Icon }) => (
                  <div key={id} className="sl-switch-row">
                    <div className="sl-switch-label-wrap">
                      {Icon && <Icon size={14} strokeWidth={1.8} className="sl-icon-accent" />}
                      <Label htmlFor={id}>{label}</Label>
                    </div>
                    <Switch
                      id={id}
                      checked={formData[key]}
                      onCheckedChange={(checked) => set(key, checked)}
                    />
                  </div>
                ))}
              </div>
            </GlassCard>

            <div className="sl-submit-wrap">
              <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                <Button type="submit" disabled={submitting}>
                  <Check size={18} strokeWidth={2} />
                  {submitting ? 'Saving…' : 'Save Sleep Data'}
                </Button>
              </motion.div>
            </div>

          </form>
        </div>
      </main>
    </div>
  );
}
