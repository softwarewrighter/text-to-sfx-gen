//! Squeaky hinge synthesis: elasto-plastic friction driving a modal resonator.
//!
//! See docs/domain-expertise.md. Signal chain:
//! door swing -> pin sliding speed -> elasto-plastic friction (Dupont et al. 2002,
//! as used by Avanzini/Serafin/Rocchesso DAFx-02) coupled to hinge metal modes and a
//! compliant door-leaf mode -> wood panel bandpasses and frame delays (Farnell,
//! Designing Sound P9) -> small room.
//!
//! The squeak pitch is not an oscillator: it emerges when stick-slip locks to a
//! hinge mode. Same `Params` (including `seed`) always render identical samples.

use rustfft::{FftPlanner, num_complex::Complex};
use serde::{Deserialize, Serialize};
use std::f64::consts::PI;

pub const SAMPLE_RATE: u32 = 44100;
const OVERSAMPLE: usize = 8; // explicit integration of the stiff contact needs oversampling

/// Field names match the sidecar JSON written by squeaky_hinge_generator.py.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Params {
    pub duration: f64,
    pub swing_time: f64,
    pub peak_speed: f64,
    pub swing_shape: f64,
    pub jerkiness: f64,
    pub load: f64,
    pub load_variation: f64,
    pub pitch_bend: f64,
    pub lubrication: f64,
    pub rust: f64,
    pub stribeck_speed: f64,
    pub contact_stiffness: f64,
    pub hinge_freq: f64,
    pub hinge_damping: f64,
    pub leaf_freq: f64,
    pub creak: f64,
    pub panel_size: f64,
    pub room: f64,
    pub volume: f64,
    pub seed: u64,
}

impl Default for Params {
    fn default() -> Self {
        Self {
            duration: 3.0,
            swing_time: 2.6,
            peak_speed: 0.05,
            swing_shape: 1.0,
            jerkiness: 0.15,
            load: 1.0,
            load_variation: 0.5,
            pitch_bend: 0.6,
            lubrication: 0.0,
            rust: 0.2,
            stribeck_speed: 0.02,
            contact_stiffness: 2e4,
            hinge_freq: 750.0,
            hinge_damping: 0.002,
            leaf_freq: 35.0,
            creak: 0.5,
            panel_size: 1.0,
            room: 0.15,
            volume: 0.8,
            seed: 0,
        }
    }
}

/// UI/CLI metadata for one numeric parameter.
pub struct ParamSpec {
    pub name: &'static str,
    pub min: f64,
    pub max: f64,
    pub logarithmic: bool,
    pub help: &'static str,
}

pub const PARAM_SPECS: &[ParamSpec] = &[
    ParamSpec { name: "duration", min: 0.5, max: 8.0, logarithmic: false, help: "Seconds of audio" },
    ParamSpec { name: "swing_time", min: 0.3, max: 8.0, logarithmic: false, help: "Seconds the door is moving" },
    ParamSpec { name: "peak_speed", min: 0.002, max: 0.3, logarithmic: true, help: "Sliding speed at the pin (m/s) at the fastest point" },
    ParamSpec { name: "swing_shape", min: 0.3, max: 4.0, logarithmic: false, help: ">1 = slower start/end, more time in the squeak window" },
    ParamSpec { name: "jerkiness", min: 0.0, max: 1.0, logarithmic: false, help: "Irregular pushes on the door" },
    ParamSpec { name: "load", min: 0.1, max: 6.0, logarithmic: true, help: "Normal force on the pin (N): door weight, sag" },
    ParamSpec { name: "load_variation", min: 0.0, max: 1.0, logarithmic: false, help: "Load changes as the door swings (bent pin, sag)" },
    ParamSpec { name: "pitch_bend", min: 0.0, max: 2.0, logarithmic: false, help: "How much hinge pitch follows the load (joint stiffens under load)" },
    ParamSpec { name: "lubrication", min: 0.0, max: 1.0, logarithmic: false, help: "0 = dry, 1 = oiled (no squeak)" },
    ParamSpec { name: "rust", min: 0.0, max: 1.0, logarithmic: false, help: "Surface roughness noise in the friction force" },
    ParamSpec { name: "stribeck_speed", min: 0.002, max: 0.2, logarithmic: true, help: "Speed (m/s) of the friction dip; squeak window sits near here" },
    ParamSpec { name: "contact_stiffness", min: 2e3, max: 3e5, logarithmic: true, help: "Contact stiffness: higher = pitch bends more with load/speed" },
    ParamSpec { name: "hinge_freq", min: 150.0, max: 4000.0, logarithmic: true, help: "Lowest hinge metal mode (Hz): squeak pitch" },
    ParamSpec { name: "hinge_damping", min: 0.0005, max: 0.05, logarithmic: true, help: "Hinge mode damping: lower = purer squeak" },
    ParamSpec { name: "leaf_freq", min: 8.0, max: 120.0, logarithmic: true, help: "Compliant door-leaf mode (Hz): creak pulse source" },
    ParamSpec { name: "creak", min: 0.0, max: 2.0, logarithmic: false, help: "Level of leaf creak pulses heard through the panel" },
    ParamSpec { name: "panel_size", min: 0.3, max: 3.0, logarithmic: true, help: "Door panel size: larger = lower wood resonances" },
    ParamSpec { name: "room", min: 0.0, max: 1.0, logarithmic: false, help: "Room reverb wet level" },
    ParamSpec { name: "volume", min: 0.05, max: 1.0, logarithmic: false, help: "Peak level of a loud squeak (quiet sounds stay quiet)" },
];

impl Params {
    pub fn get_mut(&mut self, name: &str) -> Option<&mut f64> {
        Some(match name {
            "duration" => &mut self.duration,
            "swing_time" => &mut self.swing_time,
            "peak_speed" => &mut self.peak_speed,
            "swing_shape" => &mut self.swing_shape,
            "jerkiness" => &mut self.jerkiness,
            "load" => &mut self.load,
            "load_variation" => &mut self.load_variation,
            "pitch_bend" => &mut self.pitch_bend,
            "lubrication" => &mut self.lubrication,
            "rust" => &mut self.rust,
            "stribeck_speed" => &mut self.stribeck_speed,
            "contact_stiffness" => &mut self.contact_stiffness,
            "hinge_freq" => &mut self.hinge_freq,
            "hinge_damping" => &mut self.hinge_damping,
            "leaf_freq" => &mut self.leaf_freq,
            "creak" => &mut self.creak,
            "panel_size" => &mut self.panel_size,
            "room" => &mut self.room,
            "volume" => &mut self.volume,
            _ => return None,
        })
    }
}

pub const PRESET_NAMES: &[&str] = &[
    "squeaky", "oiled", "horror_slow", "rusty_groan", "fast_swing", "cabinet_tiny",
];

pub fn preset(name: &str) -> Option<Params> {
    let d = Params::default();
    Some(match name {
        "squeaky" => d,
        "oiled" => Params { lubrication: 1.0, rust: 0.05, ..d },
        "horror_slow" => Params {
            duration: 5.0, swing_time: 4.6, peak_speed: 0.025, swing_shape: 1.5,
            jerkiness: 0.35, hinge_freq: 620.0, panel_size: 1.3, room: 0.3,
            creak: 1.0, ..d
        },
        "rusty_groan" => Params {
            rust: 0.8, load: 2.5, peak_speed: 0.03, hinge_freq: 480.0,
            hinge_damping: 0.006, leaf_freq: 25.0, creak: 1.2, ..d
        },
        "fast_swing" => Params {
            duration: 1.6, swing_time: 1.0, peak_speed: 0.15, hinge_freq: 900.0, ..d
        },
        "cabinet_tiny" => Params {
            duration: 1.5, swing_time: 1.2, load: 0.3, hinge_freq: 1800.0,
            leaf_freq: 60.0, panel_size: 0.4, room: 0.08, ..d
        },
        _ => return None,
    })
}

// Inharmonic metal-part mode ratios (assumption: free-bar-like, not measured)
const HINGE_MODE_RATIOS: [f64; 3] = [1.0, 2.76, 5.40];
const HINGE_MODE_GAINS: [f64; 3] = [1.0, 0.5, 0.25];
// Farnell P9 wood panel (Hz, Q) and frame delays (ms)
const PANEL_MODES: [(f64, f64); 6] =
    [(62.5, 1.0), (125.0, 1.0), (250.0, 2.0), (395.0, 2.0), (560.0, 3.0), (790.0, 3.0)];
const FRAME_DELAYS_MS: [f64; 8] = [4.52, 5.06, 6.27, 8.0, 5.48, 7.14, 10.12, 16.0];
// A squeak at default settings reaches `volume`; weaker excitation stays quieter
const REFERENCE_PEAK: f64 = 0.05;

/// SplitMix64: small, fast, fully deterministic across platforms.
struct Rng(u64);

impl Rng {
    fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    fn uniform(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }
    fn normal(&mut self) -> f64 {
        let u1 = self.uniform().max(1e-300);
        let u2 = self.uniform();
        (-2.0 * u1.ln()).sqrt() * (2.0 * PI * u2).cos()
    }
}

/// Seeded smooth random curve in [-1, 1] changing about `rate_hz` times per second.
fn smooth_noise(rng: &mut Rng, num_samples: usize, rate_hz: f64) -> Vec<f64> {
    let num_points = ((num_samples as f64 / SAMPLE_RATE as f64 * rate_hz) as usize + 2).max(2);
    let points: Vec<f64> = (0..num_points).map(|_| rng.uniform() * 2.0 - 1.0).collect();
    (0..num_samples)
        .map(|n| {
            let pos = n as f64 / (num_samples.max(2) - 1) as f64 * (num_points - 1) as f64;
            let i = (pos as usize).min(num_points - 2);
            let frac = pos - i as f64;
            points[i] * (1.0 - frac) + points[i + 1] * frac
        })
        .collect()
}

/// Door swing -> (pin sliding speed, normal force) per output sample.
fn swing_controls(p: &Params, rng: &mut Rng, num_samples: usize) -> (Vec<f64>, Vec<f64>) {
    let wobble = smooth_noise(rng, num_samples, 6.0);
    let load_wobble = smooth_noise(rng, num_samples, 1.5);
    let mut speed = Vec::with_capacity(num_samples);
    let mut load = Vec::with_capacity(num_samples);
    for n in 0..num_samples {
        let t = n as f64 / SAMPLE_RATE as f64;
        let phase = (t / p.swing_time).clamp(0.0, 1.0);
        let bell = (PI * phase).sin().max(0.0).powf(p.swing_shape);
        speed.push(p.peak_speed * bell * (1.0 + p.jerkiness * wobble[n]).max(0.0));
        // Load rises as the door opens (sag) and wanders (bent pin)
        let sag = 1.0 + p.load_variation * (phase - 0.5);
        load.push(p.load * (sag + 0.5 * p.load_variation * load_wobble[n]).max(0.05));
    }
    (speed, load)
}

struct Mode {
    k: f64,
    k_base: f64,
    r: f64,
    mass: f64,
    gain: f64,
    x: f64,
    xd: f64,
}

/// Elasto-plastic friction between the moving pin surface and the resonator.
/// Returns (hinge pickup velocity, leaf velocity) at SAMPLE_RATE.
fn friction_resonator(p: &Params, speed: &[f64], load: &[f64], rng: &mut Rng) -> (Vec<f64>, Vec<f64>) {
    let dt = 1.0 / (SAMPLE_RATE as f64 * OVERSAMPLE as f64);
    let mu_d = 0.3;
    let mu_s = mu_d + 0.3 * (1.0 - p.lubrication);
    let vs = p.stribeck_speed;
    let sig0 = p.contact_stiffness;
    let sig1 = 0.2 * (sig0 * 0.01).sqrt();
    let sig2 = 0.05;
    let sig3 = 0.3 * p.rust;

    let mode = |freq: f64, zeta: f64, mass: f64, gain: f64| {
        let k = mass * (2.0 * PI * freq).powi(2);
        Mode { k, k_base: k, r: 2.0 * zeta * (k * mass).sqrt(), mass, gain, x: 0.0, xd: 0.0 }
    };
    let mut modes: Vec<Mode> = HINGE_MODE_RATIOS
        .iter()
        .zip(HINGE_MODE_GAINS)
        .map(|(ratio, gain)| mode(p.hinge_freq * ratio, p.hinge_damping, 0.01, gain))
        .collect();
    modes.push(mode(p.leaf_freq, 0.3, 0.05, 0.0)); // leaf: heavy, well damped
    let leaf = modes.len() - 1;

    let mut hinge_out = vec![0.0; speed.len()];
    let mut leaf_out = vec![0.0; speed.len()];
    let mut z = 0.0_f64;

    for n in 0..speed.len() {
        let vb = speed[n];
        // Joint stiffens under load (phenomenological): f ~ load^pitch_bend
        let stiffening = (load[n] / p.load).powf(2.0 * p.pitch_bend);
        for m in modes[..leaf].iter_mut() {
            m.k = m.k_base * stiffening;
        }
        let fc = mu_d * load[n];
        let fs = mu_s * load[n];
        let zba = 0.7 * fc / sig0;
        let noise_force = sig3 * fc * rng.normal();
        for _ in 0..OVERSAMPLE {
            let v = vb - modes.iter().map(|m| m.xd).sum::<f64>();
            let zss = (fc + (fs - fc) * (-(v / vs).powi(2)).exp()) / sig0;
            let az = z.abs();
            let alpha = if (v > 0.0) != (z > 0.0) || az < zba {
                0.0
            } else if az >= zss {
                1.0
            } else {
                0.5 * (1.0 + (PI * (az - 0.5 * (zss + zba)) / (zss - zba)).sin())
            };
            let zd = v * (1.0 - alpha * z * v.signum() / zss);
            z += zd * dt;
            let force = sig0 * z + sig1 * zd + sig2 * v + noise_force;
            for m in modes.iter_mut() {
                let xdd = (force - m.k * m.x - m.r * m.xd) / m.mass;
                m.xd += xdd * dt;
                m.x += m.xd * dt;
            }
        }
        hinge_out[n] = modes[..leaf].iter().map(|m| m.xd * m.gain).sum();
        leaf_out[n] = modes[leaf].xd;
    }
    (hinge_out, leaf_out)
}

/// RBJ constant-skirt bandpass (peak gain = Q), Direct Form II Transposed.
fn bandpass(signal: &[f64], center: f64, q: f64) -> Vec<f64> {
    let omega = 2.0 * PI * center / SAMPLE_RATE as f64;
    let alpha = omega.sin() / (2.0 * q);
    let a0 = 1.0 + alpha;
    let (b0, b2) = (alpha / a0, -alpha / a0);
    let (a1, a2) = (-2.0 * omega.cos() / a0, (1.0 - alpha) / a0);
    let (mut z1, mut z2) = (0.0, 0.0);
    signal
        .iter()
        .map(|&s| {
            let y = b0 * s + z1;
            z1 = -a1 * y + z2;
            z2 = b2 * s - a2 * y;
            y
        })
        .collect()
}

/// Farnell wood panel: parallel bandpass resonances + 0.2 dry.
fn door_panel(signal: &[f64], panel_size: f64) -> Vec<f64> {
    let mut out: Vec<f64> = signal.iter().map(|s| 0.2 * s).collect();
    for (freq, q) in PANEL_MODES {
        for (o, b) in out.iter_mut().zip(bandpass(signal, freq / panel_size, q)) {
            *o += b;
        }
    }
    out
}

/// Farnell door frame: mean of short delays, then a one-pole high-pass at 125 Hz.
fn door_frame(signal: &[f64]) -> Vec<f64> {
    let mut out = vec![0.0; signal.len()];
    for ms in FRAME_DELAYS_MS {
        let d = (ms / 1000.0 * SAMPLE_RATE as f64) as usize;
        for i in d..signal.len() {
            out[i] += signal[i - d] / FRAME_DELAYS_MS.len() as f64;
        }
    }
    let a = (-2.0 * PI * 125.0 / SAMPLE_RATE as f64).exp();
    let (mut prev_x, mut prev_y) = (0.0, 0.0);
    for o in out.iter_mut() {
        prev_y = a * (prev_y + *o - prev_x);
        prev_x = *o;
        *o = prev_y;
    }
    out
}

/// Small room: FFT convolution with a seeded exponentially decaying noise tail.
fn room(signal: &[f64], wet: f64, rng: &mut Rng) -> Vec<f64> {
    if wet <= 0.0 {
        return signal.to_vec();
    }
    let ir_len = (0.35 * SAMPLE_RATE as f64) as usize;
    let mut ir: Vec<f64> = (0..ir_len)
        .map(|i| rng.normal() * (-(i as f64) / (0.08 * SAMPLE_RATE as f64)).exp())
        .collect();
    let norm = ir.iter().map(|x| x * x).sum::<f64>().sqrt();
    ir.iter_mut().for_each(|x| *x /= norm);

    let size = (signal.len() + ir_len - 1).next_power_of_two();
    let mut planner = FftPlanner::<f64>::new();
    let fft = planner.plan_fft_forward(size);
    let ifft = planner.plan_fft_inverse(size);
    let to_complex = |x: &[f64]| {
        let mut buf: Vec<Complex<f64>> = x.iter().map(|&r| Complex::new(r, 0.0)).collect();
        buf.resize(size, Complex::new(0.0, 0.0));
        buf
    };
    let mut a = to_complex(signal);
    let mut b = to_complex(&ir);
    fft.process(&mut a);
    fft.process(&mut b);
    a.iter_mut().zip(&b).for_each(|(x, y)| *x *= y);
    ifft.process(&mut a);
    signal
        .iter()
        .zip(&a)
        .map(|(dry, tail)| (1.0 - wet) * dry + wet * tail.re / size as f64)
        .collect()
}

/// The pin sliding speed curve that `render` uses (same seed, same curve).
pub fn speed_curve(p: &Params) -> Vec<f64> {
    let num_samples = (p.duration * SAMPLE_RATE as f64) as usize;
    swing_controls(p, &mut Rng(p.seed), num_samples).0
}

/// Render a mono signal in [-1, 1].
pub fn render(p: &Params) -> Vec<f32> {
    let mut rng = Rng(p.seed);
    let num_samples = (p.duration * SAMPLE_RATE as f64) as usize;
    let (speed, load) = swing_controls(p, &mut rng, num_samples);
    let (hinge, leaf) = friction_resonator(p, &speed, &load, &mut rng);

    // Leaf motion is slow; its stick-slip jolts are heard through the panel.
    let excitation: Vec<f64> = hinge
        .iter()
        .enumerate()
        .map(|(i, h)| {
            let jolt = if i == 0 { 0.0 } else { leaf[i] - leaf[i - 1] };
            h + p.creak * jolt * SAMPLE_RATE as f64 / 200.0
        })
        .collect();
    let panel = door_panel(&excitation, p.panel_size);
    let radiated: Vec<f64> = excitation.iter().zip(&panel).map(|(e, pa)| 0.6 * e + pa).collect();
    let frame = door_frame(&radiated);
    let radiated: Vec<f64> = radiated.iter().zip(&frame).map(|(r, f)| r + 0.5 * f).collect();
    let mut signal = room(&radiated, p.room, &mut rng);

    let fade = ((0.01 * SAMPLE_RATE as f64) as usize).min(signal.len() / 2);
    for i in 0..fade {
        let g = i as f64 / fade as f64;
        signal[i] *= g;
        let j = signal.len() - 1 - i;
        signal[j] *= g;
    }
    let peak = signal.iter().fold(0.0_f64, |m, s| m.max(s.abs()));
    let gain = p.volume / peak.max(REFERENCE_PEAK);
    signal.iter().map(|s| (s * gain).clamp(-1.0, 1.0) as f32).collect()
}

/// Write mono 16-bit PCM WAV plus the sidecar JSON next to it.
pub fn save(p: &Params, samples: &[f32], wav_path: &std::path::Path) -> Result<std::path::PathBuf, String> {
    let spec = hound::WavSpec {
        channels: 1,
        sample_rate: SAMPLE_RATE,
        bits_per_sample: 16,
        sample_format: hound::SampleFormat::Int,
    };
    let mut writer = hound::WavWriter::create(wav_path, spec).map_err(|e| e.to_string())?;
    for s in samples {
        writer.write_sample((s * 32767.0) as i16).map_err(|e| e.to_string())?;
    }
    writer.finalize().map_err(|e| e.to_string())?;
    let json_path = wav_path.with_extension("json");
    let json = serde_json::to_string_pretty(p).map_err(|e| e.to_string())?;
    std::fs::write(&json_path, json).map_err(|e| e.to_string())?;
    Ok(json_path)
}

pub fn load_json(path: &std::path::Path) -> Result<Params, String> {
    let text = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn same_params_same_samples() {
        let p = Params { duration: 0.5, swing_time: 0.4, ..Params::default() };
        assert_eq!(render(&p), render(&p));
    }

    #[test]
    fn different_seed_different_samples() {
        let p = Params { duration: 0.5, swing_time: 0.4, ..Params::default() };
        let q = Params { seed: 1, ..p.clone() };
        assert_ne!(render(&p), render(&q));
    }

    #[test]
    fn oiled_is_much_quieter_than_dry() {
        let dry = render(&preset("squeaky").unwrap());
        let oiled = render(&preset("oiled").unwrap());
        let rms = |x: &[f32]| (x.iter().map(|s| s * s).sum::<f32>() / x.len() as f32).sqrt();
        assert!(rms(&oiled) < 0.2 * rms(&dry));
    }
}
