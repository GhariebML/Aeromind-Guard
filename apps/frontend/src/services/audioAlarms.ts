/**
 * AeroMind Physical AI Control Room Web Audio Synthesizer.
 * Generates instant acoustic warnings using the standard Web Audio API without external audio files.
 */

class AudioAlarmService {
  private audioCtx: AudioContext | null = null;
  private isMuted: boolean = false;
  private lastTriggerTime: number = 0;

  constructor() {
    // Lazy initialize AudioContext upon first user interaction
  }

  private getContext(): AudioContext | null {
    if (typeof window === 'undefined') return null;
    if (!this.audioCtx) {
      const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtxClass) {
        this.audioCtx = new AudioCtxClass();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }

  public setMuted(muted: boolean) {
    this.isMuted = muted;
  }

  public getMuted(): boolean {
    return this.isMuted;
  }

  public playCriticalAlarm() {
    if (this.isMuted) return;
    const now = Date.now();
    // Throttle alarms to once every 4 seconds
    if (now - this.lastTriggerTime < 4000) return;
    this.lastTriggerTime = now;

    const ctx = this.getContext();
    if (!ctx) return;

    try {
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.type = 'sawtooth';
      osc2.type = 'square';

      // Urgent dual-tone siren
      osc1.frequency.setValueAtTime(880, ctx.currentTime);
      osc1.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.35);
      osc1.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.7);

      osc2.frequency.setValueAtTime(440, ctx.currentTime);
      osc2.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.35);
      osc2.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.7);

      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.85);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);

      osc1.start(ctx.currentTime);
      osc2.start(ctx.currentTime);
      osc1.stop(ctx.currentTime + 0.85);
      osc2.stop(ctx.currentTime + 0.85);
    } catch (e) {
      console.warn('[AudioAlarm] Play error:', e);
    }
  }

  public playWarningChime() {
    if (this.isMuted) return;
    const now = Date.now();
    if (now - this.lastTriggerTime < 3000) return;
    this.lastTriggerTime = now;

    const ctx = this.getContext();
    if (!ctx) return;

    try {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
      osc.frequency.setValueAtTime(880, ctx.currentTime + 0.15); // A5

      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.4);
    } catch (e) {
      console.warn('[AudioAlarm] Play error:', e);
    }
  }
}

export const audioAlarms = new AudioAlarmService();
