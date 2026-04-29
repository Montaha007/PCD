// src/audio/BrainwaveSynth.js
// Raw Web Audio implementation — bypasses Tone.js routing quirks
import * as Tone from 'tone';

export class BrainwaveSynth {
  constructor() {
    this.isPlaying = false;
    this.technique = 'binaural';
    this.ctx = null;
    this.masterGain = null;
    this.nodes = [];   // track all nodes for cleanup
    this.noise = null;
    this.noiseGain = null;
  }

  async _init() {
    if (this.ctx) return;
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (this.ctx.state === 'suspended') await this.ctx.resume();
    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.value = 0;
    this.masterGain.connect(this.ctx.destination);

    // Tone.js shares the same AudioContext if we hand it ours
    Tone.setContext(this.ctx);
  }

  async start({ carrierHz, brainwaveHz, technique = 'binaural', ambient = false }) {
    if (this.isPlaying) await this.stop();
    await this._init();
    if (this.ctx.state === 'suspended') await this.ctx.resume();

    console.log('🔊 Context state:', this.ctx.state);
    console.log('🔊 Starting:', { carrierHz, brainwaveHz, technique, ambient });

    this.technique = technique;

    if (technique === 'binaural') {
      this._startBinaural(carrierHz, brainwaveHz);
    } else {
      this._startIsochronic(carrierHz, brainwaveHz);
    }

    if (ambient) this._startNoise();

    // Fade in master
    const now = this.ctx.currentTime;
    this.masterGain.gain.cancelScheduledValues(now);
    this.masterGain.gain.setValueAtTime(0, now);
    this.masterGain.gain.linearRampToValueAtTime(0.7, now + 0.8);

    this.isPlaying = true;
  }

  _startBinaural(carrier, brainwave) {
    const ctx = this.ctx;
    const leftFreq = carrier - brainwave / 2;
    const rightFreq = carrier + brainwave / 2;

    const leftOsc = ctx.createOscillator();
    const rightOsc = ctx.createOscillator();
    const leftPan = ctx.createStereoPanner();
    const rightPan = ctx.createStereoPanner();
    const oscGain = ctx.createGain();

    leftOsc.frequency.value = leftFreq;
    rightOsc.frequency.value = rightFreq;
    leftOsc.type = 'sine';
    rightOsc.type = 'sine';
    leftPan.pan.value = -1;
    rightPan.pan.value = 1;
    oscGain.gain.value = 0.5;

    leftOsc.connect(leftPan);
    rightOsc.connect(rightPan);
    leftPan.connect(oscGain);
    rightPan.connect(oscGain);
    oscGain.connect(this.masterGain);

    leftOsc.start();
    rightOsc.start();

    this.nodes.push(leftOsc, rightOsc, leftPan, rightPan, oscGain);
  }

  _startIsochronic(carrier, brainwave) {
    const ctx = this.ctx;
    const osc = ctx.createOscillator();
    const gainNode = ctx.createGain();

    osc.frequency.value = carrier;
    osc.type = 'sine';

    // Use a square wave LFO via setValueCurveAtTime for reliable on/off pulsing
    osc.connect(gainNode);
    gainNode.connect(this.masterGain);

    // Schedule pulses for the next 60 seconds (looped via setInterval if longer)
    const period = 1 / brainwave; // seconds per pulse
    const now = ctx.currentTime;
    gainNode.gain.setValueAtTime(0, now);

    // Build a pulse pattern: gain alternates 0.5 (on) / 0 (off)
    for (let i = 0; i < brainwave * 60; i++) {  // 60 seconds of pulses
      const t = now + i * period;
      gainNode.gain.setValueAtTime(0.5, t);
      gainNode.gain.setValueAtTime(0, t + period * 0.5);
    }

    osc.start();

    // Schedule a refresh in 55s if still playing (loop the pulse pattern)
    this._isoRefreshTimer = setTimeout(() => {
      if (this.isPlaying) {
        this._refreshIsochronicPulses(gainNode, brainwave);
      }
    }, 55000);

    this.nodes.push(osc, gainNode);
  }

  _refreshIsochronicPulses(gainNode, brainwave) {
    const period = 1 / brainwave;
    const now = this.ctx.currentTime;
    for (let i = 0; i < brainwave * 60; i++) {
      const t = now + i * period;
      gainNode.gain.setValueAtTime(0.5, t);
      gainNode.gain.setValueAtTime(0, t + period * 0.5);
    }
    this._isoRefreshTimer = setTimeout(() => {
      if (this.isPlaying) this._refreshIsochronicPulses(gainNode, brainwave);
    }, 55000);
  }

  _startNoise() {
    // Pink noise via Tone (still works because we shared the context)
    this.noiseGain = this.ctx.createGain();
    this.noiseGain.gain.value = 0;
    this.noiseGain.connect(this.masterGain);

    this.noise = new Tone.Noise('pink');
    this.noise.connect(this.noiseGain);
    this.noise.start();

    const now = this.ctx.currentTime;
    this.noiseGain.gain.linearRampToValueAtTime(0.12, now + 1.5);
  }

  setVolume(linear) {
    if (!this.masterGain) return;
    const v = Math.max(0, Math.min(1, linear));
    const now = this.ctx.currentTime;
    this.masterGain.gain.cancelScheduledValues(now);
    this.masterGain.gain.linearRampToValueAtTime(v, now + 0.1);
  }

  setAmbient(enabled) {
    if (enabled && !this.noise) {
      this._startNoise();
    } else if (!enabled && this.noise) {
      const now = this.ctx.currentTime;
      this.noiseGain.gain.linearRampToValueAtTime(0, now + 0.4);
      const oldNoise = this.noise;
      const oldGain = this.noiseGain;
      this.noise = null;
      this.noiseGain = null;
      setTimeout(() => {
        oldNoise?.stop();
        oldNoise?.dispose();
        oldGain?.disconnect();
      }, 500);
    }
  }

  async stop() {
    if (!this.isPlaying) return;

    const now = this.ctx.currentTime;
    this.masterGain.gain.cancelScheduledValues(now);
    this.masterGain.gain.linearRampToValueAtTime(0, now + 0.4);

    await new Promise((r) => setTimeout(r, 500));

    clearTimeout(this._isoRefreshTimer);

    this.nodes.forEach((n) => {
      try { if (n.stop) n.stop(); } catch {}
      try { n.disconnect(); } catch {}
    });
    this.nodes = [];

    if (this.noise) {
      try { this.noise.stop(); this.noise.dispose(); } catch {}
      this.noise = null;
    }
    if (this.noiseGain) {
      try { this.noiseGain.disconnect(); } catch {}
      this.noiseGain = null;
    }

    this.isPlaying = false;
  }

  dispose() {
    this.stop();
    if (this.masterGain) {
      try { this.masterGain.disconnect(); } catch {}
    }
    if (this.ctx && this.ctx.state !== 'closed') {
      this.ctx.close();
    }
  }
}