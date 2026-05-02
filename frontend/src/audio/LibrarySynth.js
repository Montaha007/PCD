// src/audio/LibrarySynth.js
// Procedural Web Audio engine: white noise, brown noise, rain, forest, beach

export class LibrarySynth {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.nodes = [];
    this.isPlaying = false;
    this.currentType = null;
    this._chirpTimer = null;
  }

  async _init() {
    if (this.ctx) return;
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (this.ctx.state === 'suspended') await this.ctx.resume();
    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.value = 0;
    this.masterGain.connect(this.ctx.destination);
  }

  // ── Buffer factories ──────────────────────────────────────────────────────

  _makeWhiteBuffer(seconds = 3) {
    const sr = this.ctx.sampleRate;
    const buf = this.ctx.createBuffer(2, sr * seconds, sr);
    for (let ch = 0; ch < 2; ch++) {
      const data = buf.getChannelData(ch);
      for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
    }
    return buf;
  }

  _makeBrownBuffer(seconds = 3) {
    const sr = this.ctx.sampleRate;
    const buf = this.ctx.createBuffer(2, sr * seconds, sr);
    for (let ch = 0; ch < 2; ch++) {
      const data = buf.getChannelData(ch);
      let last = 0;
      for (let i = 0; i < data.length; i++) {
        const w = Math.random() * 2 - 1;
        data[i] = (last + 0.02 * w) / 1.02;
        last = data[i];
        data[i] *= 3.5;
      }
    }
    return buf;
  }

  _looping(buffer) {
    const src = this.ctx.createBufferSource();
    src.buffer = buffer;
    src.loop = true;
    return src;
  }

  // ── Sound generators ──────────────────────────────────────────────────────

  _playWhiteNoise() {
    const src = this._looping(this._makeWhiteBuffer());
    src.connect(this.masterGain);
    src.start();
    this.nodes.push(src);
  }

  _playBrownNoise() {
    const src = this._looping(this._makeBrownBuffer());
    src.connect(this.masterGain);
    src.start();
    this.nodes.push(src);
  }

  _playRain() {
    const src = this._looping(this._makeWhiteBuffer(4));
    const lpf = this.ctx.createBiquadFilter();
    lpf.type = 'lowpass';
    lpf.frequency.value = 3500;
    lpf.Q.value = 0.7;

    // Slow LFO gives natural rain intensity variation
    const lfo = this.ctx.createOscillator();
    const lfoGain = this.ctx.createGain();
    const modGain = this.ctx.createGain();
    lfo.frequency.value = 0.18;
    lfoGain.gain.value = 0.18;
    modGain.gain.value = 0.72;

    lfo.connect(lfoGain);
    lfoGain.connect(modGain.gain);
    src.connect(lpf);
    lpf.connect(modGain);
    modGain.connect(this.masterGain);
    lfo.start();
    src.start();
    this.nodes.push(src, lpf, lfo, lfoGain, modGain);
  }

  _playForest() {
    // Wind + leaves layer
    const src = this._looping(this._makeWhiteBuffer(4));
    const bpf = this.ctx.createBiquadFilter();
    bpf.type = 'bandpass';
    bpf.frequency.value = 700;
    bpf.Q.value = 0.35;
    const windGain = this.ctx.createGain();
    windGain.gain.value = 0.45;

    const lfo = this.ctx.createOscillator();
    const lfoG = this.ctx.createGain();
    lfo.frequency.value = 0.12;
    lfoG.gain.value = 0.25;
    lfo.connect(lfoG);
    lfoG.connect(windGain.gain);

    src.connect(bpf);
    bpf.connect(windGain);
    windGain.connect(this.masterGain);
    lfo.start();
    src.start();
    this.nodes.push(src, bpf, windGain, lfo, lfoG);

    this._scheduleBirdChirps();
  }

  _scheduleBirdChirps() {
    const schedule = () => {
      if (!this.isPlaying) return;
      this._chirpTimer = setTimeout(() => {
        if (!this.isPlaying) return;
        this._playChirp();
        schedule();
      }, 2500 + Math.random() * 5500);
    };
    schedule();
  }

  _playChirp() {
    const osc = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    const now = this.ctx.currentTime;
    const f = 1400 + Math.random() * 1800;
    osc.type = 'sine';
    osc.frequency.setValueAtTime(f, now);
    osc.frequency.linearRampToValueAtTime(f * 1.1, now + 0.06);
    osc.frequency.linearRampToValueAtTime(f * 0.95, now + 0.14);
    g.gain.setValueAtTime(0, now);
    g.gain.linearRampToValueAtTime(0.09, now + 0.04);
    g.gain.linearRampToValueAtTime(0, now + 0.16);
    osc.connect(g);
    g.connect(this.masterGain);
    osc.start(now);
    osc.stop(now + 0.2);
  }

  _playBeach() {
    // Low brown rumble + mid hiss, both shaped by a slow wave LFO (~12 s cycle)
    const src1 = this._looping(this._makeBrownBuffer(4));
    const src2 = this._looping(this._makeWhiteBuffer(4));

    const lpf1 = this.ctx.createBiquadFilter();
    lpf1.type = 'lowpass';
    lpf1.frequency.value = 600;
    const g1 = this.ctx.createGain();
    g1.gain.value = 0.5;

    const bpf2 = this.ctx.createBiquadFilter();
    bpf2.type = 'bandpass';
    bpf2.frequency.value = 1800;
    bpf2.Q.value = 0.5;
    const g2 = this.ctx.createGain();
    g2.gain.value = 0.25;

    const lfo = this.ctx.createOscillator();
    const lfoG = this.ctx.createGain();
    const waveBase = this.ctx.createGain();
    lfo.frequency.value = 0.083;
    lfoG.gain.value = 0.4;
    waveBase.gain.value = 0.55;

    lfo.connect(lfoG);
    lfoG.connect(waveBase.gain);
    src1.connect(lpf1); lpf1.connect(g1); g1.connect(waveBase);
    src2.connect(bpf2); bpf2.connect(g2); g2.connect(waveBase);
    waveBase.connect(this.masterGain);

    lfo.start();
    src1.start();
    src2.start();
    this.nodes.push(src1, src2, lpf1, g1, bpf2, g2, lfo, lfoG, waveBase);
  }

  // ── Public API ────────────────────────────────────────────────────────────

  async play(type, volume = 0.7) {
    if (this.isPlaying) await this.stop();
    await this._init();
    if (this.ctx.state === 'suspended') await this.ctx.resume();
    this.currentType = type;

    switch (type) {
      case 'white':  this._playWhiteNoise(); break;
      case 'brown':  this._playBrownNoise(); break;
      case 'rain':   this._playRain();       break;
      case 'forest': this._playForest();     break;
      case 'beach':  this._playBeach();      break;
      default: break;
    }

    const now = this.ctx.currentTime;
    this.masterGain.gain.cancelScheduledValues(now);
    this.masterGain.gain.setValueAtTime(0, now);
    this.masterGain.gain.linearRampToValueAtTime(volume, now + 0.8);
    this.isPlaying = true;
  }

  setVolume(linear) {
    if (!this.masterGain) return;
    const v = Math.max(0, Math.min(1, linear));
    const now = this.ctx.currentTime;
    this.masterGain.gain.cancelScheduledValues(now);
    this.masterGain.gain.linearRampToValueAtTime(v, now + 0.1);
  }

  async stop() {
    if (!this.isPlaying) return;
    clearTimeout(this._chirpTimer);
    const now = this.ctx.currentTime;
    this.masterGain.gain.cancelScheduledValues(now);
    this.masterGain.gain.linearRampToValueAtTime(0, now + 0.4);
    await new Promise(r => setTimeout(r, 500));
    this.nodes.forEach(n => {
      try { if (n.stop) n.stop(); } catch {}
      try { n.disconnect(); } catch {}
    });
    this.nodes = [];
    this.isPlaying = false;
    this.currentType = null;
  }

  dispose() {
    this.stop();
    if (this.masterGain) { try { this.masterGain.disconnect(); } catch {} }
    if (this.ctx && this.ctx.state !== 'closed') this.ctx.close();
  }
}
