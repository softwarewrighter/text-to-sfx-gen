//! Lightweight descriptors for the UI: waveform envelope, pitch track, speed curve.

use crate::synth::{self, Params, SAMPLE_RATE};

const WINDOW: usize = 1024;
const HOP: usize = 512;
const MIN_PITCH: f64 = 80.0;
const MAX_PITCH: f64 = 4000.0;
const PERIODICITY_THRESHOLD: f64 = 0.7;

#[derive(Default)]
pub struct Analysis {
    pub envelope: Vec<[f64; 2]>,
    pub pitch: Vec<[f64; 2]>,
    pub speed: Vec<[f64; 2]>,
    pub pitched_fraction: f64,
    pub median_pitch: Option<f64>,
    pub peak: f64,
}

pub fn analyze(samples: &[f32], params: &Params) -> Analysis {
    let sr = SAMPLE_RATE as f64;
    let peak = samples.iter().fold(0.0_f32, |m, s| m.max(s.abs())) as f64;

    // Min/max envelope, about 2000 points
    let block = (samples.len() / 1000).max(1);
    let mut envelope = Vec::new();
    for (b, chunk) in samples.chunks(block).enumerate() {
        let t = (b * block) as f64 / sr;
        let (lo, hi) = chunk.iter().fold((0.0_f32, 0.0_f32), |(lo, hi), &s| (lo.min(s), hi.max(s)));
        envelope.push([t, lo as f64]);
        envelope.push([t, hi as f64]);
    }

    // Normalized autocorrelation pitch per frame; only periodic, audible frames count
    let min_lag = (sr / MAX_PITCH) as usize;
    let max_lag = (sr / MIN_PITCH) as usize;
    let swing_end = (params.swing_time * sr) as usize;
    let mut pitch = Vec::new();
    let (mut moving_frames, mut pitched_frames) = (0, 0);
    let mut start = 0;
    while start + WINDOW + max_lag <= samples.len() {
        let frame = &samples[start..start + WINDOW + max_lag];
        let energy: f64 = frame[..WINDOW].iter().map(|&s| (s as f64).powi(2)).sum();
        if start < swing_end {
            moving_frames += 1;
        }
        if energy / WINDOW as f64 > 1e-5 {
            let mut best = (0, 0.0);
            for lag in min_lag..max_lag {
                let mut num = 0.0;
                let mut lagged_energy = 0.0;
                for i in 0..WINDOW {
                    num += frame[i] as f64 * frame[i + lag] as f64;
                    lagged_energy += (frame[i + lag] as f64).powi(2);
                }
                let r = num / (energy * lagged_energy).sqrt().max(1e-12);
                if r > best.1 {
                    best = (lag, r);
                }
            }
            if best.1 > PERIODICITY_THRESHOLD {
                pitch.push([start as f64 / sr, sr / best.0 as f64]);
                if start < swing_end {
                    pitched_frames += 1;
                }
            }
        }
        start += HOP;
    }
    let mut pitches: Vec<f64> = pitch.iter().map(|p| p[1]).collect();
    pitches.sort_by(f64::total_cmp);
    let median_pitch = pitches.get(pitches.len() / 2).copied();

    let speed_samples = synth::speed_curve(params);
    let step = (speed_samples.len() / 1000).max(1);
    let speed = speed_samples
        .iter()
        .enumerate()
        .step_by(step)
        .map(|(i, &v)| [i as f64 / sr, v])
        .collect();

    Analysis {
        envelope,
        pitch,
        speed,
        pitched_fraction: pitched_frames as f64 / moving_frames.max(1) as f64,
        median_pitch,
        peak,
    }
}
