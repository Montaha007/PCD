import { useState, useEffect } from 'react';
import { GlassCard } from '../../components/GlassCard';
import { OnboardingProgress } from '../../components/OnboardingProgress';
import { Label } from '../../components/ui/label';
import { Button } from '../../components/ui/button';
import { BookOpen, Send, Sparkles, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { toast } from 'sonner';
import AppSidebar from '../../components/AppSidebar';
import FloatingStars from '../../components/FloatingStars';
import './Journal.css';

const API_BASE = import.meta.env.VITE_API_BASE;

export default function Journal() {
  const [content, setContent] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [entries, setEntries] = useState([]);
  const [loadingEntries, setLoadingEntries] = useState(true);

  const getToken = () => localStorage.getItem('access_token');

  const fetchEntries = async () => {
    const token = getToken();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/mood/entries/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setEntries(data);
      }
    } catch {
      // silently ignore — entries will just be empty
    } finally {
      setLoadingEntries(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) {
      toast.error('Veuillez écrire quelque chose dans votre journal');
      return;
    }

    const token = getToken();
    if (!token) {
      toast.error('Session expirée. Veuillez vous reconnecter.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/mood/entries/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content: content.trim() }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const msg = Object.values(err).flat().join(' ') || "Impossible d'enregistrer l'entrée.";
        toast.error(msg);
        return;
      }

      toast.success('Entrée de journal enregistrée avec succès!');
      setContent('');
      fetchEntries();
    } catch {
      toast.error('Impossible de contacter le serveur.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="wellness-shell">
      <FloatingStars />
      <AppSidebar />
      <main className="wellness-content">
        <div className="journal-wrap">
          <OnboardingProgress />

          <div className="journal-header" style={{ marginTop: '28px' }}>
            <h1 className="journal-title">
              <BookOpen size={30} strokeWidth={1.8} />
              Journal Émotionnel
            </h1>
            <p className="journal-sub">
              Exprimez vos pensées, émotions et réflexions quotidiennes
            </p>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <GlassCard className={`journal-card-focus ${isFocused ? 'focused' : ''}`}>
              <form onSubmit={handleSubmit} className="journal-form">
                <div className="journal-label-row">
                  <Sparkles size={18} strokeWidth={1.8} className="journal-icon-primary" />
                  <Label>Comment vous sentez-vous aujourd'hui ?</Label>
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
                    placeholder="Écrivez librement vos pensées, émotions, préoccupations ou ce qui vous a marqué aujourd'hui… L'IA analysera le sentiment de votre texte pour vous aider à mieux comprendre votre état émotionnel."
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
                  <span>L'IA analysera automatiquement le sentiment de votre texte</span>
                </div>

                <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                  <Button type="submit" className="journal-submit-btn" disabled={submitting}>
                    {submitting
                      ? <Loader2 size={18} className="journal-spin" />
                      : <Send size={18} strokeWidth={1.8} />
                    }
                    {submitting ? 'Enregistrement…' : "Enregistrer l'entrée"}
                  </Button>
                </motion.div>
              </form>
            </GlassCard>
          </motion.div>

          {/* Previous entries */}
          {loadingEntries ? (
            <div className="journal-loading">
              <Loader2 size={20} className="journal-spin" />
              <span>Chargement des entrées…</span>
            </div>
          ) : entries.length > 0 && (
            <div className="journal-entries-section">
              <h2 className="journal-entries-title">Entrées précédentes</h2>
              <AnimatePresence>
                {entries.map((entry, index) => (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <GlassCard>
                      <div className="journal-entry-meta">
                        <BookOpen size={14} strokeWidth={1.8} className="journal-icon-accent" />
                        <span>
                          {new Date(entry.created_at).toLocaleDateString('fr-FR', {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                        {entry.status === 'COMPLETED' && entry.predicted_mood && (
                          <span className="journal-mood-badge">{entry.predicted_mood}</span>
                        )}
                        {entry.status === 'PENDING' && (
                          <span className="journal-status-badge pending">En attente d'analyse</span>
                        )}
                      </div>
                      <p className="journal-entry-content">{entry.content}</p>
                      {entry.analysis_text && (
                        <p className="journal-analysis-text">
                          <Sparkles size={13} strokeWidth={1.8} />
                          {entry.analysis_text}
                        </p>
                      )}
                    </GlassCard>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
