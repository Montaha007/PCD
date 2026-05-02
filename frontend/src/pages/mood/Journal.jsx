import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { GlassCard } from '../../components/GlassCard';
import { OnboardingProgress } from '../../components/OnboardingProgress';
import { Label } from '../../components/ui/label';
import { Button } from '../../components/ui/button';
import {
  BookOpen, Send, Sparkles, Loader2, X, ChevronDown, Brain,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { toast } from 'sonner';
import AppSidebar from '../../components/AppSidebar';
import FloatingStars from '../../components/FloatingStars';
import './Journal.css';

const API_BASE = import.meta.env.VITE_API_BASE;
const IN_PROGRESS_STATUSES = new Set(['PENDING', 'PROCESSING']);
const FAILED_STATUSES = new Set(['FAILED']);

const LABEL_COLORS = {
  normal:                 { bg: 'rgba(40,160,80,0.15)',   border: 'rgba(40,160,80,0.35)',   text: '#5dcf8a' },
  anxiety:                { bg: 'rgba(210,160,30,0.15)',  border: 'rgba(210,160,30,0.35)',  text: '#d4a83a' },
  depression:             { bg: 'rgba(70,100,210,0.15)',  border: 'rgba(70,100,210,0.35)',  text: '#7090e8' },
  stress:                 { bg: 'rgba(220,100,40,0.15)',  border: 'rgba(220,100,40,0.35)',  text: '#e07848' },
  bipolar:                { bg: 'rgba(140,60,210,0.15)',  border: 'rgba(140,60,210,0.35)',  text: '#b070e0' },
  suicidal:               { bg: 'rgba(210,40,60,0.15)',   border: 'rgba(210,40,60,0.35)',   text: '#e06070' },
  'personality disorder': { bg: 'rgba(180,60,140,0.15)', border: 'rgba(180,60,140,0.35)', text: '#d070b0' },
};

function labelStyle(label) {
  return LABEL_COLORS[label?.toLowerCase()] ?? {
    bg: 'rgba(70,130,180,0.15)', border: 'rgba(70,130,180,0.35)', text: '#7db8d8',
  };
}

function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function hasPredictionResult(entry) {
  if (!entry?.predicted_mood) return false;
  if (IN_PROGRESS_STATUSES.has(entry.status)) return false;
  if (FAILED_STATUSES.has(entry.status)) return false;
  return true;
}

export default function Journal() {
  const [content, setContent]           = useState('');
  const [isFocused, setIsFocused]       = useState(false);
  const [submitting, setSubmitting]     = useState(false);
  const [entries, setEntries]           = useState([]);
  const [loadingEntries, setLoadingEntries] = useState(true);
  const [modal, setModal]               = useState(null);   // { label, analysis }
  const [expandedId, setExpandedId]     = useState(null);

  const getToken = () => localStorage.getItem('access_token');

  const fetchEntries = async () => {
    const token = getToken();
    if (!token) return [];
    const res = await fetch(`${API_BASE}/api/mood/entries/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return [];
    return res.json();
  };

  useEffect(() => {
    fetchEntries()
      .then(setEntries)
      .catch(() => {})
      .finally(() => setLoadingEntries(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) { toast.error('Please write something in your journal.'); return; }
    const token = getToken();
    if (!token) { toast.error('Session expired. Please log in again.'); return; }

    setSubmitting(true);
    try {
      const postRes = await fetch(`${API_BASE}/api/mood/entries/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ content: content.trim() }),
      });

      if (!postRes.ok) {
        const err = await postRes.json().catch(() => ({}));
        toast.error(Object.values(err).flat().join(' ') || 'Could not save journal entry.');
        return;
      }

      setContent('');
      const updated = await fetchEntries();
      setEntries(updated);
      window.dispatchEvent(new Event('setup-progress-refresh'));

      const latest = updated[0];
      if (hasPredictionResult(latest)) {
        setModal({ label: latest.predicted_mood, analysis: latest.analysis_text });
      } else {
        toast.success('Journal entry saved!');
      }
    } catch {
      toast.error('Could not reach the server.');
    } finally {
      setSubmitting(false);
    }
  };

  const toggleExpand = (id) => setExpandedId((prev) => (prev === id ? null : id));

  return (
    <div className="wellness-shell">
      <FloatingStars />
      <AppSidebar />
      <main className="wellness-content">
        <div className="journal-wrap">
          <OnboardingProgress currentStep="journal" />

          <div className="journal-header" style={{ marginTop: '28px' }}>
            <h1 className="journal-title">
              <BookOpen size={30} strokeWidth={1.8} />
              Emotional Journal
            </h1>
            <p className="journal-sub">
              Express your thoughts, emotions, and daily reflections
            </p>
          </div>

          {/* ── Write form ── */}
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <GlassCard className={`journal-card-focus ${isFocused ? 'focused' : ''}`}>
              <form onSubmit={handleSubmit} className="journal-form">
                <div className="journal-label-row">
                  <Sparkles size={18} strokeWidth={1.8} className="journal-icon-primary" />
                  <Label>How are you feeling today?</Label>
                </div>

                <div className="journal-textarea-wrap">
                  {isFocused && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="journal-glow"
                    />
                  )}
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    placeholder="Write freely about your thoughts, emotions, concerns, or what stood out to you today… AI will analyze your text to help you better understand your emotional state."
                    className="journal-textarea"
                    style={{
                      background: isFocused
                        ? 'linear-gradient(135deg, rgba(184,169,255,0.05), rgba(102,212,207,0.05))'
                        : undefined,
                    }}
                  />
                </div>

                <div className="journal-hint-row">
                  <Sparkles size={14} strokeWidth={1.8} className="journal-icon-primary" />
                  <span>AI will automatically analyze your text sentiment</span>
                </div>

                <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                  <Button type="submit" className="journal-submit-btn" disabled={submitting}>
                    {submitting
                      ? <Loader2 size={18} className="journal-spin" />
                      : <Send size={18} strokeWidth={1.8} />}
                    {submitting ? 'Analyzing…' : 'Save Entry'}
                  </Button>
                </motion.div>
              </form>
            </GlassCard>
          </motion.div>

          {/* ── History ── */}
          {loadingEntries ? (
            <div className="journal-loading">
              <Loader2 size={20} className="journal-spin" />
              <span>Loading entries…</span>
            </div>
          ) : entries.length > 0 && (
            <div className="journal-entries-section">
              <h2 className="journal-entries-title">Previous Entries</h2>
              <AnimatePresence>
                {entries.map((entry, index) => {
                  const colors = labelStyle(entry.predicted_mood);
                  const isOpen = expandedId === entry.id;
                  return (
                    <motion.div
                      key={entry.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.04 }}
                    >
                      <GlassCard className="journal-entry-card">
                        {/* ── Collapsed header (always visible) ── */}
                        <button
                          className="journal-entry-header"
                          onClick={() => toggleExpand(entry.id)}
                          type="button"
                        >
                          <BookOpen size={14} strokeWidth={1.8} className="journal-icon-accent" />
                          <span className="journal-entry-date">
                            {new Date(entry.created_at).toLocaleDateString('en-US', {
                              weekday: 'short', year: 'numeric', month: 'short', day: 'numeric',
                              hour: '2-digit', minute: '2-digit',
                            })}
                          </span>

                          {hasPredictionResult(entry) && (
                            <span
                              className="journal-mood-badge"
                              style={{
                                background: colors.bg,
                                border: `1px solid ${colors.border}`,
                                color: colors.text,
                              }}
                            >
                              {capitalize(entry.predicted_mood)}
                            </span>
                          )}
                          {IN_PROGRESS_STATUSES.has(entry.status) && (
                            <span className="journal-status-badge pending">Analyzing</span>
                          )}
                          {FAILED_STATUSES.has(entry.status) && (
                            <span className="journal-status-badge failed">Analysis failed</span>
                          )}

                          <ChevronDown
                            size={16}
                            className={`journal-chevron ${isOpen ? 'open' : ''}`}
                          />
                        </button>

                        {/* ── Expanded content ── */}
                        <AnimatePresence initial={false}>
                          {isOpen && (
                            <motion.div
                              key="content"
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.25, ease: 'easeInOut' }}
                              className="journal-entry-body"
                            >
                              <p className="journal-entry-content">{entry.content}</p>
                              {entry.analysis_text && (
                                <p className="journal-analysis-text">
                                  <Sparkles size={13} strokeWidth={1.8} style={{ flexShrink: 0, marginTop: 2 }} />
                                  {entry.analysis_text}
                                </p>
                              )}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </GlassCard>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </div>
      </main>

      {/* ── Analysis result modal (portal → renders at document.body) ── */}
      {createPortal(
        <AnimatePresence>
        {modal && (
          <>
            <motion.div
              className="journal-modal-backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setModal(null)}
            />
            <div className="journal-modal-wrap">
              <motion.div
                className="journal-modal"
                initial={{ opacity: 0, scale: 0.92, y: 24 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.92, y: 24 }}
                transition={{ type: 'spring', damping: 22, stiffness: 280 }}
              >
                <button className="journal-modal-close" onClick={() => setModal(null)}>
                  <X size={18} />
                </button>

                <div className="journal-modal-icon">
                  <Brain size={32} strokeWidth={1.6} />
                </div>

                <p className="journal-modal-eyebrow">Mental Health Analysis</p>

                <div
                  className="journal-modal-label"
                  style={{
                    background: labelStyle(modal.label).bg,
                    border: `1px solid ${labelStyle(modal.label).border}`,
                    color: labelStyle(modal.label).text,
                  }}
                >
                  {capitalize(modal.label)}
                </div>

                {modal.analysis && (
                  <p className="journal-modal-analysis">{modal.analysis}</p>
                )}

                <Button className="journal-modal-btn" onClick={() => setModal(null)}>
                  Got it
                </Button>
              </motion.div>
            </div>
          </>
        )}
        </AnimatePresence>,
        document.body
      )}
    </div>
  );
}
