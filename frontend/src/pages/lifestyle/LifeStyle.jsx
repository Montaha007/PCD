import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GlassCard } from '../../components/GlassCard';
import { OnboardingProgress } from '../../components/OnboardingProgress';
import { Label } from '../../components/ui/label';
import { Button } from '../../components/ui/button';
import {
  Activity, BookOpen, Smartphone, Briefcase, Coffee, Leaf,
  Calendar, Check, TrendingUp, Moon, Sparkles, Calculator,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { toast } from 'sonner';
import AppSidebar from '../../components/AppSidebar';
import FloatingStars from '../../components/FloatingStars';
import './LifeStyle.css';

const API_BASE = import.meta.env.VITE_API_BASE;

const DEFAULT_FORM = {
  date: new Date().toISOString().split('T')[0],
  WorkoutTime: 0.5,
  ReadingTime: 0.5,
  PhoneTime: 2,
  WorkHours: 8,
  CaffeineIntake: 100,
  RelaxationTime: 1,
};

// Map quality_label → UI copy + color class
const QUALITY_META = {
  insufficient: { text: 'Insufficient sleep',  tone: 'danger'  },
  short:        { text: 'Short sleep',         tone: 'warn'    },
  healthy:      { text: 'Healthy sleep',       tone: 'good'    },
  excessive:    { text: 'Excessive sleep',     tone: 'warn'    },
};

export default function LifestyleForm() {
  const [formData, setFormData] = useState(DEFAULT_FORM);
  const [savedLog, setSavedLog] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const set = (key, val) => setFormData((prev) => ({ ...prev, [key]: val }));

  // Live preview of derived features
  const previewWorkXCaffeine = (
    Number(formData.WorkHours) * Number(formData.CaffeineIntake)
  ).toFixed(0);
  const previewScreenIntensity = (
    Number(formData.PhoneTime) / (Number(formData.RelaxationTime) + 1)
  ).toFixed(2);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Session expired. Please log in again.');
      return;
    }

    setSubmitting(true);
    setPrediction(null);

    const payload = {
      date: formData.date,
      WorkoutTime: Number(formData.WorkoutTime),
      ReadingTime: Number(formData.ReadingTime),
      PhoneTime: Number(formData.PhoneTime),
      WorkHours: Number(formData.WorkHours),
      CaffeineIntake: Number(formData.CaffeineIntake),
      RelaxationTime: Number(formData.RelaxationTime),
    };

    try {
      const res = await fetch(`${API_BASE}/api/lifestyle/logs/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const msg = Object.values(err).flat().join(' ') || 'Failed to save lifestyle log.';
        toast.error(msg);
        return;
      }

      const data = await res.json();
      setSavedLog(data);

      // Auto-fire prediction
      setPredicting(true);
      const predictRes = await fetch(`${API_BASE}/api/lifestyle/logs/${data.id}/predict/`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!predictRes.ok) {
        toast.error('Lifestyle saved, but prediction could not be generated.');
      } else {
        const predictData = await predictRes.json();
        setPrediction(predictData);
        toast.success('Lifestyle saved and sleep prediction generated!');
      }
    } catch {
      toast.error('Could not reach the server.');
    } finally {
      setPredicting(false);
      setSubmitting(false);
    }
  };

  

  // Reusable slider row — matches SleepLog's inner card rhythm
  const SliderRow = ({ icon: Icon, label, name, min, max, step, unit, iconClass = 'sl-icon-primary' }) => (
    <div className="sl-slider-row">
      <div className="sl-card-label-row">
        <Icon size={16} strokeWidth={1.8} className={iconClass} />
        <Label htmlFor={name}>{label}</Label>
      </div>
      <input
        id={name}
        type="range"
        name={name}
        min={min}
        max={max}
        step={step}
        value={formData[name]}
        onChange={(e) => set(name, Number(e.target.value))}
        className="sl-range-input"
      />
      <div className="sl-slider-display">
        <span className="sl-slider-val-sm">{formData[name]}</span>
        <span className="sl-slider-unit">{unit}</span>
      </div>
      <div className="sl-range-labels">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );

  return (
    <div className="wellness-shell">
      <FloatingStars />
      <AppSidebar />
      <main className="wellness-content">
        <div className="sleep-log-wrap">
          <OnboardingProgress />

          <div className="sleep-log-header" style={{ marginTop: '28px' }}>
            <h1 className="sleep-log-title">
              <Activity size={30} strokeWidth={1.8} />
              Lifestyle Log
            </h1>
            <p className="sleep-log-sub">
              Capture today's habits — these signals feed the model that predicts your sleep duration
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
                  <Calculator size={16} strokeWidth={1.8} className="sl-icon-primary" />
                  <span className="sl-result-label">Work × Caffeine</span>
                  <strong className="sl-result-value">
                    {savedLog.Work_x_Caffeine?.toFixed(0) ?? '—'}
                  </strong>
                </div>
                <div className="sl-result-divider" />
                <div className="sl-result-row">
                  <Smartphone size={16} strokeWidth={1.8} className="sl-icon-accent" />
                  <span className="sl-result-label">Screen intensity</span>
                  <strong className="sl-result-value">
                    {savedLog.Screen_Time_Intensity?.toFixed(2) ?? '—'}
                  </strong>
                </div>
                <div className="sl-result-divider" />
                <div className="sl-result-row sl-result-row-wide">
                  <Moon size={16} strokeWidth={1.8} className="sl-icon-accent" />
                  <span className="sl-result-label">Predicted sleep</span>
                  <strong className="sl-result-value">
                    {predicting && 'Generating prediction...'}
                    {!predicting && !prediction && 'Unavailable'}
                    {!predicting && prediction && (
                      <>
                        {prediction.predicted_sleep_hours}h
                        {' '}
                        <span className={`sl-quality-pill sl-quality-${QUALITY_META[prediction.quality_label]?.tone || 'good'}`}>
                          {QUALITY_META[prediction.quality_label]?.text || prediction.quality_label}
                        </span>
                      </>
                    )}
                  </strong>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="sleep-log-form">

            {/* Date */}
            <GlassCard>
              <div className="sl-card-inner">
                <div className="sl-card-label-row">
                  <Calendar size={16} strokeWidth={1.8} className="sl-icon-primary" />
                  <Label htmlFor="date">Date</Label>
                </div>
                <input
                  id="date"
                  type="date"
                  className="sl-datetime-input"
                  value={formData.date}
                  onChange={(e) => set('date', e.target.value)}
                  max={new Date().toISOString().split('T')[0]}
                  required
                />
              </div>
            </GlassCard>

            {/* Activity section */}
            <GlassCard>
              <h3 className="sl-problems-header">
                <Activity size={18} strokeWidth={1.8} className="sl-icon-accent" />
                Activity
              </h3>
              <div className="sl-sliders-stack">
                <SliderRow
                  icon={Activity}  label="Workout time"
                  name="WorkoutTime"  min={0} max={3} step={0.25} unit="h"
                />
                <SliderRow
                  icon={BookOpen}  label="Reading time"
                  name="ReadingTime"  min={0} max={2} step={0.25} unit="h"
                />
                <SliderRow
                  icon={Leaf}  label="Relaxation time"
                  name="RelaxationTime"  min={0} max={2} step={0.25} unit="h"
                />
              </div>
            </GlassCard>

            {/* Screens & Work */}
            <GlassCard>
              <h3 className="sl-problems-header">
                <Briefcase size={18} strokeWidth={1.8} className="sl-icon-accent" />
                Screens &amp; Work
              </h3>
              <div className="sl-sliders-stack">
                <SliderRow
                  icon={Smartphone}  label="Phone time"
                  name="PhoneTime"  min={1} max={5} step={0.25} unit="h"
                />
                <SliderRow
                  icon={Briefcase}  label="Work hours"
                  name="WorkHours"  min={4} max={10} step={0.5} unit="h"
                />
              </div>
            </GlassCard>

            {/* Caffeine */}
            <GlassCard>
              <h3 className="sl-problems-header">
                <Coffee size={18} strokeWidth={1.8} className="sl-icon-alert" />
                Caffeine
              </h3>
              <div className="sl-sliders-stack">
                <SliderRow
                  icon={Coffee}  label="Caffeine intake"
                  name="CaffeineIntake"  min={0} max={300} step={10} unit="mg"
                  iconClass="sl-icon-alert"
                />
                <small className="sl-hint">
                  1 espresso ≈ 65mg • 1 coffee ≈ 95mg • 1 energy drink ≈ 80mg
                </small>
              </div>
            </GlassCard>

            {/* Live preview of derived features */}
            <GlassCard>
              <h3 className="sl-problems-header">
                <Sparkles size={18} strokeWidth={1.8} className="sl-icon-accent" />
                Computed by the AI pipeline
              </h3>
              <div className="sl-preview-grid">
                <div className="sl-preview-card">
                  <div className="sl-card-label-row">
                    <TrendingUp size={14} strokeWidth={1.8} className="sl-icon-primary" />
                    <span className="sl-preview-label">Work × Caffeine</span>
                  </div>
                  <span className="sl-preview-value">{previewWorkXCaffeine}</span>
                  <small className="sl-preview-formula">WorkHours × CaffeineIntake</small>
                </div>
                <div className="sl-preview-card">
                  <div className="sl-card-label-row">
                    <Smartphone size={14} strokeWidth={1.8} className="sl-icon-primary" />
                    <span className="sl-preview-label">Screen Intensity</span>
                  </div>
                  <span className="sl-preview-value">{previewScreenIntensity}</span>
                  <small className="sl-preview-formula">PhoneTime ÷ (RelaxationTime + 1)</small>
                </div>
              </div>
              <small className="sl-hint">
                These are calculated automatically — you don't submit them.
              </small>
            </GlassCard>

            <div className="sl-submit-wrap">
              <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                <Button type="submit" disabled={submitting}>
                  <Check size={18} strokeWidth={2} />
                  {submitting ? 'Saving…' : 'Save Lifestyle Data'}
                </Button>
              </motion.div>
            </div>

          </form>
        </div>
      </main>
    </div>
  );
}