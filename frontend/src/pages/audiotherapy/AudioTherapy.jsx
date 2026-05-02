import { useState, useEffect, useRef } from 'react';
import { GlassCard } from '../../components/GlassCard';
import { OnboardingProgress } from '../../components/OnboardingProgress';
import { Label } from '../../components/ui/label';
import {
  Headphones, Brain, Sparkles, Volume2, Play, Square, Pause,
  Waves, Activity, AlertCircle, CloudRain, Wind, Radio,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { toast } from 'sonner';
import AppSidebar from '../../components/AppSidebar';
import FloatingStars from '../../components/FloatingStars';
import { fetchRecommendation, fetchDisorders } from '../../api/audiotherapy';
import { BrainwaveSynth } from '../../audio/BrainwaveSynth';
import { LibrarySynth } from '../../audio/LibrarySynth';
import './AudioTherapy.css';

// ── Constants ──────────────────────────────────────────────────────────────

const BRAINWAVE_INFO = {
  delta: { name: 'Delta',  range: '0.5–4 Hz',  color: '#9b8df0' },
  theta: { name: 'Theta',  range: '4–8 Hz',    color: '#7c9ae8' },
  alpha: { name: 'Alpha',  range: '8–13 Hz',   color: '#6ea8d8' },
  beta:  { name: 'Beta',   range: '13–30 Hz',  color: '#a7c7e7' },
  gamma: { name: 'Gamma',  range: '30–100 Hz', color: '#e7b9a7' },
};

const LIBRARY_CATEGORIES = [
  {
    id: 'noise',
    label: 'Noise',
    Icon: Radio,
    tracks: [
      {
        id: 'white',
        title: 'White Noise',
        description: 'Full-spectrum masking for focus and sleep',
        benefit: 'Focus · Sleep masking',
        type: 'Broadband',
        colorA: '#6ea8d8',
        colorB: '#a7c7e7',
      },
      {
        id: 'brown',
        title: 'Brown Noise',
        description: 'Deep, warm rumble — gentler than white noise',
        benefit: 'Deep focus · Relaxation',
        type: 'Low-pass',
        colorA: '#c8956c',
        colorB: '#e8c4a0',
      },
    ],
  },
  {
    id: 'nature',
    label: 'Nature Sounds',
    Icon: Wind,
    tracks: [
      {
        id: 'rain',
        title: 'Rain',
        description: 'Soft rainfall to mask distractions and ease sleep',
        benefit: 'Sleep · Stress relief',
        type: 'Nature',
        colorA: '#7c9ae8',
        colorB: '#b0c4f0',
      },
      {
        id: 'forest',
        title: 'Forest',
        description: 'Birds, rustling leaves and gentle woodland wind',
        benefit: 'Calm · Nature connection',
        type: 'Nature',
        colorA: '#4caf7d',
        colorB: '#81c784',
      },
      {
        id: 'beach',
        title: 'Beach',
        description: 'Rolling ocean waves breaking on a quiet shore',
        benefit: 'Relaxation · Anxiety relief',
        type: 'Nature',
        colorA: '#26b5c0',
        colorB: '#80d4da',
      },
    ],
  },
];

// ── Component ──────────────────────────────────────────────────────────────

export default function AudioTherapy() {
  // ── AI Session state ────────────────────────────────────────────────────
  const [disorders, setDisorders] = useState([]);
  const [selectedDisorder, setSelectedDisorder] = useState('normal');
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [technique, setTechnique] = useState('binaural');
  const [ambient, setAmbient] = useState(false);
  const [volume, setVolume] = useState(0.5);

  // ── Library state ───────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState('session');
  const [libraryActiveTrack, setLibraryActiveTrack] = useState(null);
  const [libraryVolume, setLibraryVolume] = useState(0.5);

  // ── Synth refs (one instance per page lifetime) ─────────────────────────
  const synthRef = useRef(null);
  if (!synthRef.current) synthRef.current = new BrainwaveSynth();

  const libSynthRef = useRef(null);
  if (!libSynthRef.current) libSynthRef.current = new LibrarySynth();

  // ── AI Session effects ──────────────────────────────────────────────────
  useEffect(() => {
    fetchDisorders().then(setDisorders).catch(() => {
      toast.error('Could not load disorder list.');
    });
  }, []);

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

  useEffect(() => {
    synthRef.current.setVolume(volume);
  }, [volume]);

  useEffect(() => {
    if (synthRef.current.isPlaying) {
      synthRef.current.setAmbient(ambient);
    }
  }, [ambient]);

  useEffect(() => {
    libSynthRef.current.setVolume(libraryVolume);
  }, [libraryVolume]);

  useEffect(() => {
    return () => {
      synthRef.current?.dispose();
      libSynthRef.current?.dispose();
    };
  }, []);

  // ── Handlers ────────────────────────────────────────────────────────────
  const handleTabSwitch = (tab) => {
    if (tab === activeTab) return;
    if (tab === 'library' && synthRef.current.isPlaying) {
      synthRef.current.stop().then(() => setIsPlaying(false));
    }
    if (tab === 'session' && libSynthRef.current.isPlaying) {
      libSynthRef.current.stop().then(() => setLibraryActiveTrack(null));
    }
    setActiveTab(tab);
  };

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

  const handleLibraryToggle = async (trackId) => {
    if (libraryActiveTrack === trackId) {
      await libSynthRef.current.stop();
      setLibraryActiveTrack(null);
    } else {
      try {
        await libSynthRef.current.play(trackId, libraryVolume);
        setLibraryActiveTrack(trackId);
      } catch (err) {
        toast.error('Could not start audio. Please try again.');
        console.error(err);
      }
    }
  };

  const brainwaveInfo = recommendation ? BRAINWAVE_INFO[recommendation.primary_brainwave] : null;

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="wellness-shell">
      <FloatingStars />
      <AppSidebar />
      <main className="wellness-content">
        <div className="audio-wrap">

          {/* Header */}
          <div className="audio-header" style={{ marginTop: '28px' }}>
            <h1 className="audio-title">
              <Headphones size={30} strokeWidth={1.8} />
              Audio Therapy
            </h1>
            <p className="audio-sub">
              Brainwave-guided sound sessions &amp; ambient soundscapes
            </p>
          </div>

          {/* Tab bar */}
          <div className="audio-tab-bar">
            <button
              className={`audio-tab-btn ${activeTab === 'session' ? 'is-active' : ''}`}
              onClick={() => handleTabSwitch('session')}
            >
              <Brain size={14} strokeWidth={2} />
              AI Session
            </button>
            <button
              className={`audio-tab-btn ${activeTab === 'library' ? 'is-active' : ''}`}
              onClick={() => handleTabSwitch('library')}
            >
              <Headphones size={14} strokeWidth={2} />
              Library
            </button>
          </div>

          {/* ── AI SESSION TAB ─────────────────────────────────────────── */}
          <AnimatePresence mode="wait">
            {activeTab === 'session' && (
              <motion.div
                key="session"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
              >
                <OnboardingProgress />

                {/* Disorder selector */}
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
              </motion.div>
            )}

            {/* ── LIBRARY TAB ──────────────────────────────────────────── */}
            {activeTab === 'library' && (
              <motion.div
                key="library"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="audio-library"
              >
                {/* Library volume */}
                <GlassCard>
                  <div className="audio-volume">
                    <div className="audio-label-row">
                      <Volume2 size={16} strokeWidth={1.8} className="audio-icon-accent" />
                      <Label htmlFor="lib-volume">Volume</Label>
                      <span className="audio-volume-display" style={{ marginLeft: 'auto' }}>
                        {Math.round(libraryVolume * 100)}%
                      </span>
                    </div>
                    <input
                      id="lib-volume"
                      type="range"
                      min={0} max={1} step={0.01}
                      value={libraryVolume}
                      onChange={(e) => setLibraryVolume(Number(e.target.value))}
                      className="audio-range"
                    />
                  </div>
                </GlassCard>

                {/* Categories */}
                {LIBRARY_CATEGORIES.map((cat) => (
                  <div key={cat.id} className="audio-cat-section">
                    <h3 className="audio-cat-title">
                      <cat.Icon size={16} strokeWidth={1.8} />
                      {cat.label}
                    </h3>

                    <div className="audio-track-grid">
                      {cat.tracks.map((track, index) => (
                        <motion.div
                          key={track.id}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: index * 0.08 }}
                          className={`audio-track-card ${libraryActiveTrack === track.id ? 'is-active' : ''}`}
                          onClick={() => handleLibraryToggle(track.id)}
                        >
                          {/* Active glow overlay */}
                          <AnimatePresence>
                            {libraryActiveTrack === track.id && (
                              <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="audio-track-glow"
                                style={{
                                  background: `linear-gradient(135deg, ${track.colorA}28, ${track.colorB}14)`,
                                }}
                              />
                            )}
                          </AnimatePresence>

                          <div className="audio-track-inner">
                            {/* Header row: title + play button */}
                            <div className="audio-track-header">
                              <div className="audio-track-meta">
                                <h4 className="audio-track-title">{track.title}</h4>
                                <p className="audio-track-desc">{track.description}</p>
                              </div>
                              <motion.button
                                className="audio-track-play-btn"
                                style={{
                                  background: `linear-gradient(135deg, ${track.colorA}, ${track.colorB})`,
                                }}
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.92 }}
                                onClick={(e) => { e.stopPropagation(); handleLibraryToggle(track.id); }}
                              >
                                {libraryActiveTrack === track.id
                                  ? <Pause size={17} fill="white" stroke="none" />
                                  : <Play  size={17} fill="white" stroke="none" style={{ marginLeft: 2 }} />
                                }
                              </motion.button>
                            </div>

                            {/* Info chips */}
                            <div className="audio-track-chips">
                              <div className="audio-chip">
                                <span className="audio-chip-label">Type</span>
                                <span className="audio-chip-value" style={{ color: track.colorA }}>{track.type}</span>
                              </div>
                              <div className="audio-chip audio-chip--wide">
                                <span className="audio-chip-label">Benefit</span>
                                <span className="audio-chip-value" style={{ color: track.colorB }}>{track.benefit}</span>
                              </div>
                            </div>

                            {/* Animated wave bars when active */}
                            <AnimatePresence>
                              {libraryActiveTrack === track.id && (
                                <motion.div
                                  className="audio-wave-bars"
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: 40 }}
                                  exit={{ opacity: 0, height: 0 }}
                                  transition={{ duration: 0.3 }}
                                >
                                  {[...Array(18)].map((_, i) => (
                                    <motion.span
                                      key={i}
                                      className="audio-wave-bar"
                                      style={{
                                        background: `linear-gradient(to top, ${track.colorA}, ${track.colorB})`,
                                      }}
                                      animate={{
                                        height: [
                                          Math.random() * 22 + 8,
                                          Math.random() * 38 + 14,
                                          Math.random() * 22 + 8,
                                        ],
                                      }}
                                      transition={{
                                        duration: 0.75 + Math.random() * 0.3,
                                        repeat: Infinity,
                                        delay: i * 0.05,
                                        ease: 'easeInOut',
                                      }}
                                    />
                                  ))}
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Info card */}
                <GlassCard>
                  <div className="audio-info-row">
                    <Headphones size={22} strokeWidth={1.8} className="audio-icon-primary" style={{ flexShrink: 0, marginTop: 2 }} />
                    <div>
                      <h3 className="audio-section-header" style={{ marginBottom: 10 }}>How to use the library</h3>
                      <ul className="audio-info-list">
                        <li>Use quality headphones or speakers for full effect</li>
                        <li>Start at a low volume and adjust gradually</li>
                        <li>Create a quiet, comfortable environment</li>
                        <li>Regular practice delivers better results</li>
                        <li>Brown noise and rain are ideal for deep focus sessions</li>
                        <li>Beach and forest work well for winding down before sleep</li>
                      </ul>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            )}
          </AnimatePresence>

        </div>
      </main>
    </div>
  );
}
