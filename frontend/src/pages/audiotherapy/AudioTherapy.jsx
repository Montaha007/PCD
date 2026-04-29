import { useState, useEffect, useRef } from 'react';
import { GlassCard } from '../../components/GlassCard';
import { OnboardingProgress } from '../../components/OnboardingProgress';
import { Label } from '../../components/ui/label';
import {
  Headphones, Brain, Sparkles, Volume2, Play, Square,
  Waves, Activity, AlertCircle,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { toast } from 'sonner';
import AppSidebar from '../../components/AppSidebar';
import FloatingStars from '../../components/FloatingStars';
import { fetchRecommendation, fetchDisorders } from '../../api/audiotherapy';
import { BrainwaveSynth } from '../../audio/BrainwaveSynth';
import './AudioTherapy.css';

const BRAINWAVE_INFO = {
  delta: { name: 'Delta',  range: '0.5–4 Hz',  color: '#9b8df0' },
  theta: { name: 'Theta',  range: '4–8 Hz',    color: '#7c9ae8' },
  alpha: { name: 'Alpha',  range: '8–13 Hz',   color: '#6ea8d8' },
  beta:  { name: 'Beta',   range: '13–30 Hz',  color: '#a7c7e7' },
  gamma: { name: 'Gamma',  range: '30–100 Hz', color: '#e7b9a7' },
};

export default function AudioTherapy() {
  const [disorders, setDisorders] = useState([]);
  const [selectedDisorder, setSelectedDisorder] = useState('normal');
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [technique, setTechnique] = useState('binaural'); // 'binaural' | 'isochronic'
  const [ambient, setAmbient] = useState(false);
  const [volume, setVolume] = useState(0.5);

  // Persistent synth instance (one per page lifetime)
  const synthRef = useRef(null);
  if (!synthRef.current) synthRef.current = new BrainwaveSynth();

  // Load disorder list once
  useEffect(() => {
    fetchDisorders().then(setDisorders).catch(() => {
      toast.error('Could not load disorder list.');
    });
  }, []);

  // Load recommendation when disorder changes; stop playback if any
  useEffect(() => {
    setLoading(true);
    if (synthRef.current.isPlaying) {
      synthRef.current.stop().then(() => setIsPlaying(false));
    }
    fetchRecommendation(selectedDisorder)
      .then(setRecommendation)
      .catch((err) => toast.error(err.message))
      .finally(() => setLoading(false));
  }, [selectedDisorder]);

  // Volume changes apply live without restarting
  useEffect(() => {
    synthRef.current.setVolume(volume);
  }, [volume]);

  // Ambient toggle applies live
  useEffect(() => {
    if (synthRef.current.isPlaying) {
      synthRef.current.setAmbient(ambient);
    }
  }, [ambient]);

  // Cleanup on unmount
  useEffect(() => {
    return () => synthRef.current?.dispose();
  }, []);

  const handlePlay = async () => {
    if (!recommendation) return;
    try {
      await synthRef.current.start({
        carrierHz: recommendation.carrier_frequency_hz,
        brainwaveHz: recommendation.target_frequency_hz,
        technique,
        ambient,
      });
      synthRef.current.setVolume(volume);
      setIsPlaying(true);
    } catch (err) {
      toast.error('Could not start audio. Please try again.');
      console.error(err);
    }
  };

  const handleStop = async () => {
    await synthRef.current.stop();
    setIsPlaying(false);
  };

  const brainwaveInfo = recommendation
    ? BRAINWAVE_INFO[recommendation.primary_brainwave]
    : null;

  return (
    <div className="wellness-shell">
      <FloatingStars />
      <AppSidebar />
      <main className="wellness-content">
        <div className="audio-wrap">
          <OnboardingProgress />

          <div className="audio-header" style={{ marginTop: '28px' }}>
            <h1 className="audio-title">
              <Headphones size={30} strokeWidth={1.8} />
              Audio Therapy
            </h1>
            <p className="audio-sub">
              Brainwave-guided sound sessions generated in real time
            </p>
          </div>

          {/* Disorder override */}
          <GlassCard>
            <div className="audio-card-inner">
              <div className="audio-label-row">
                <Brain size={16} strokeWidth={1.8} className="audio-icon-primary" />
                <Label htmlFor="disorder">Current state</Label>
              </div>
              <select
                id="disorder"
                className="audio-select"
                value={selectedDisorder}
                onChange={(e) => setSelectedDisorder(e.target.value)}
                disabled={isPlaying}
              >
                {disorders.map((d) => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
              <small className="audio-hint">
                Defaults to your latest assessment. You can override for testing.
              </small>
            </div>
          </GlassCard>

          {/* Recommendation banner */}
          <AnimatePresence mode="wait">
            {recommendation && brainwaveInfo && (
              <motion.div
                key={recommendation.primary_brainwave}
                className="audio-rec-banner"
                style={{ borderColor: `${brainwaveInfo.color}55` }}
                initial={{ opacity: 0, y: -12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.3 }}
              >
                <div className="audio-rec-icon" style={{ background: `${brainwaveInfo.color}22` }}>
                  <Sparkles size={20} strokeWidth={1.8} style={{ color: brainwaveInfo.color }} />
                </div>
                <div className="audio-rec-text">
                  <div className="audio-rec-eyebrow">Recommended brainwave</div>
                  <div className="audio-rec-title" style={{ color: brainwaveInfo.color }}>
                    {brainwaveInfo.name}
                    <span className="audio-rec-range">
                      {recommendation.target_frequency_hz} Hz · carrier {recommendation.carrier_frequency_hz} Hz
                    </span>
                  </div>
                  <p className="audio-rec-rationale">{recommendation.rationale}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {loading && (
            <GlassCard>
              <p className="audio-loading">Loading recommendation...</p>
            </GlassCard>
          )}

          {/* Player card */}
          {!loading && recommendation && (
            <GlassCard>
              <div className="audio-player">
                <h3 className="audio-section-header">
                  <Volume2 size={18} strokeWidth={1.8} className="audio-icon-accent" />
                  Session
                </h3>

                {/* Technique toggle */}
                <div className="audio-segmented">
                  <button
                    type="button"
                    className={`audio-seg-btn ${technique === 'binaural' ? 'is-active' : ''}`}
                    onClick={() => !isPlaying && setTechnique('binaural')}
                    disabled={isPlaying}
                  >
                    <Waves size={14} strokeWidth={2} />
                    Binaural
                    <span className="audio-seg-sub">headphones</span>
                  </button>
                  <button
                    type="button"
                    className={`audio-seg-btn ${technique === 'isochronic' ? 'is-active' : ''}`}
                    onClick={() => !isPlaying && setTechnique('isochronic')}
                    disabled={isPlaying}
                  >
                    <Activity size={14} strokeWidth={2} />
                    Isochronic
                    <span className="audio-seg-sub">speakers ok</span>
                  </button>
                </div>

                {/* Ambient toggle */}
                <label className="audio-switch-row">
                  <span className="audio-switch-label">Pink noise ambience</span>
                  <input
                    type="checkbox"
                    className="audio-switch"
                    checked={ambient}
                    onChange={(e) => setAmbient(e.target.checked)}
                  />
                </label>

                {/* Volume */}
                <div className="audio-volume">
                  <Label htmlFor="volume">Volume</Label>
                  <input
                    id="volume"
                    type="range"
                    min={0} max={1} step={0.01}
                    value={volume}
                    onChange={(e) => setVolume(Number(e.target.value))}
                    className="audio-range"
                  />
                  <div className="audio-volume-display">{Math.round(volume * 100)}%</div>
                </div>

                {/* Play / Stop */}
                <motion.button
                  type="button"
                  className={`audio-btn-primary ${isPlaying ? 'is-playing' : ''}`}
                  onClick={isPlaying ? handleStop : handlePlay}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {isPlaying ? (
                    <>
                      <Square size={18} strokeWidth={2.5} fill="currentColor" />
                      Stop session
                    </>
                  ) : (
                    <>
                      <Play size={18} strokeWidth={2.5} fill="currentColor" />
                      Start session
                    </>
                  )}
                </motion.button>

                {technique === 'binaural' && (
                  <p className="audio-hint">
                    <AlertCircle size={12} /> Binaural beats require stereo headphones to work.
                  </p>
                )}
              </div>
            </GlassCard>
          )}
        </div>
      </main>
    </div>
  );
}