//! Hinge Lab: slider UI and CLI for the squeaky-hinge friction synthesizer.
//!
//!   hinge-lab                                   # open the UI
//!   hinge-lab render --preset squeaky --out squeaky.wav
//!   hinge-lab render --params squeaky.json --out again.wav   # exact reproduction
//!   hinge-lab render --preset rusty_groan --set load=3 --seed 7 --out x.wav
//!   hinge-lab screenshot ui.png [preset]                     # save a UI capture, exit

mod analysis;
mod synth;

use eframe::egui;
use egui_plot::{Line, Plot, Points};
use std::num::NonZero;
use std::path::PathBuf;
use std::sync::mpsc::{Receiver, Sender, channel};
use synth::{PARAM_SPECS, PRESET_NAMES, Params, SAMPLE_RATE};

fn main() -> eframe::Result {
    let args: Vec<String> = std::env::args().collect();
    if args.get(1).map(String::as_str) == Some("render") {
        if let Err(e) = cli_render(&args[2..]) {
            eprintln!("error: {e}");
            std::process::exit(1);
        }
        return Ok(());
    }
    let mut app = App::new();
    if args.get(1).map(String::as_str) == Some("screenshot") {
        let Some(path) = args.get(2) else {
            eprintln!("usage: hinge-lab screenshot <out.png> [preset]");
            std::process::exit(1);
        };
        if let Some(name) = args.get(3) {
            app.params = synth::preset(name).unwrap_or_else(|| {
                eprintln!("unknown preset '{name}'");
                std::process::exit(1);
            });
            app.preset = name.clone();
        }
        app.screenshot_path = Some(PathBuf::from(path));
        app.auto_play = false;
    }
    let mut options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([1100.0, 760.0]),
        ..Default::default()
    };
    if app.screenshot_path.is_some() {
        // Capture in the background: never take focus or cover the user's windows
        options.viewport = options
            .viewport
            .with_active(false)
            .with_window_level(egui::WindowLevel::AlwaysOnBottom);
        #[cfg(target_os = "macos")]
        {
            options.event_loop_builder = Some(Box::new(|builder| {
                use winit::platform::macos::{ActivationPolicy, EventLoopBuilderExtMacOS};
                builder
                    .with_activation_policy(ActivationPolicy::Accessory)
                    .with_activate_ignoring_other_apps(false);
            }));
        }
    }
    eframe::run_native("Hinge Lab", options, Box::new(|_cc| Ok(Box::new(app))))
}

fn save_screenshot(image: &egui::ColorImage, path: &std::path::Path) -> Result<(), String> {
    let [width, height] = image.size;
    image::save_buffer(path, image.as_raw(), width as u32, height as u32, image::ColorType::Rgba8)
        .map_err(|e| e.to_string())
}

fn cli_render(args: &[String]) -> Result<(), String> {
    let mut params = Params::default();
    let mut out = PathBuf::from("hinge.wav");
    let mut sets = Vec::new();
    let mut seed = None;
    let mut i = 0;
    while i < args.len() {
        let value = args.get(i + 1).ok_or(format!("missing value for {}", args[i]))?;
        match args[i].as_str() {
            "--preset" => params = synth::preset(value).ok_or(format!("unknown preset '{value}'"))?,
            "--params" => params = synth::load_json(value.as_ref())?,
            "--set" => sets.push(value.clone()),
            "--seed" => seed = Some(value.parse::<u64>().map_err(|e| e.to_string())?),
            "--out" => out = PathBuf::from(value),
            other => return Err(format!("unknown option '{other}'")),
        }
        i += 2;
    }
    for pair in sets {
        let (key, value) = pair.split_once('=').ok_or(format!("--set expects key=value, got '{pair}'"))?;
        let slot = params.get_mut(key).ok_or(format!("unknown parameter '{key}'"))?;
        *slot = value.parse().map_err(|e| format!("{key}: {e}"))?;
    }
    if let Some(seed) = seed {
        params.seed = seed;
    }
    let samples = synth::render(&params);
    let json = synth::save(&params, &samples, &out)?;
    println!("Saved {} (params: {})", out.display(), json.display());
    Ok(())
}

struct Rendered {
    generation: u64,
    samples: Vec<f32>,
    analysis: analysis::Analysis,
    millis: u128,
}

struct Audio {
    // The device sink must stay alive for playback to continue
    _sink: rodio::MixerDeviceSink,
    player: rodio::Player,
}

struct App {
    params: Params,
    preset: String,
    samples: Vec<f32>,
    analysis: analysis::Analysis,
    generation: u64,
    rendering: bool,
    dirty: bool,
    play_when_rendered: bool,
    auto_play: bool,
    status: String,
    audio: Option<Audio>,
    tx: Sender<Rendered>,
    rx: Receiver<Rendered>,
    // Screenshot mode: capture once the first render has been drawn, then exit
    screenshot_path: Option<PathBuf>,
    frames_since_render: u32,
}

impl App {
    fn new() -> Self {
        let (tx, rx) = channel();
        let audio = rodio::DeviceSinkBuilder::open_default_sink().ok().map(|sink| {
            let player = rodio::Player::connect_new(sink.mixer());
            Audio { _sink: sink, player }
        });
        let status = if audio.is_some() { "Ready".into() } else { "No audio output device found".into() };
        Self {
            params: Params::default(),
            preset: "squeaky".into(),
            samples: Vec::new(),
            analysis: analysis::Analysis::default(),
            generation: 0,
            rendering: false,
            dirty: true,
            play_when_rendered: false,
            auto_play: true,
            status,
            audio,
            tx,
            rx,
            screenshot_path: None,
            frames_since_render: 0,
        }
    }

    fn start_render(&mut self, ctx: &egui::Context) {
        self.generation += 1;
        self.rendering = true;
        self.dirty = false;
        let (params, generation, tx, ctx) = (self.params.clone(), self.generation, self.tx.clone(), ctx.clone());
        std::thread::spawn(move || {
            let start = std::time::Instant::now();
            let samples = synth::render(&params);
            let analysis = analysis::analyze(&samples, &params);
            let millis = start.elapsed().as_millis();
            let _ = tx.send(Rendered { generation, samples, analysis, millis });
            ctx.request_repaint();
        });
    }

    fn play(&mut self) {
        if let Some(audio) = &self.audio {
            audio.player.clear();
            let buffer = rodio::buffer::SamplesBuffer::new(
                NonZero::new(1).unwrap(),
                NonZero::new(SAMPLE_RATE).unwrap(),
                self.samples.clone(),
            );
            audio.player.append(buffer);
            audio.player.play();
        }
    }

    fn save_dialog(&mut self) {
        let Some(path) = rfd::FileDialog::new()
            .add_filter("WAV", &["wav"])
            .set_file_name(format!("{}_seed{}.wav", self.preset, self.params.seed))
            .save_file()
        else {
            return;
        };
        self.status = match synth::save(&self.params, &self.samples, &path) {
            Ok(json) => format!("Saved {} and {}", path.display(), json.display()),
            Err(e) => format!("Save failed: {e}"),
        };
    }

    fn load_dialog(&mut self) {
        let Some(path) = rfd::FileDialog::new().add_filter("JSON", &["json"]).pick_file() else {
            return;
        };
        match synth::load_json(&path) {
            Ok(params) => {
                self.params = params;
                self.preset = "custom".into();
                self.dirty = true;
                self.play_when_rendered = self.auto_play;
                self.status = format!("Loaded {}", path.display());
            }
            Err(e) => self.status = format!("Load failed: {e}"),
        }
    }

    fn controls(&mut self, ui: &mut egui::Ui) {
        let mut changed = false;
        ui.heading("Hinge Lab");
        ui.horizontal(|ui| {
            ui.label("Preset");
            egui::ComboBox::from_id_salt("preset")
                .selected_text(&self.preset)
                .show_ui(ui, |ui| {
                    for name in PRESET_NAMES {
                        if ui.selectable_label(self.preset == *name, *name).clicked() {
                            self.preset = name.to_string();
                            self.params = Params { seed: self.params.seed, ..synth::preset(name).unwrap() };
                            changed = true;
                        }
                    }
                });
        });
        ui.horizontal(|ui| {
            ui.label("Seed");
            changed |= ui.add(egui::DragValue::new(&mut self.params.seed)).changed();
            if ui.button("+1").on_hover_text("Next variation, same parameters").clicked() {
                self.params.seed = self.params.seed.wrapping_add(1);
                changed = true;
            }
            if ui.button("Random").clicked() {
                self.params.seed = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_nanos() as u64 % 1_000_000)
                    .unwrap_or(0);
                changed = true;
            }
        });
        ui.separator();
        egui::ScrollArea::vertical().show(ui, |ui| {
            for spec in PARAM_SPECS {
                let value = self.params.get_mut(spec.name).unwrap();
                ui.label(spec.name).on_hover_text(spec.help);
                let slider = egui::Slider::new(value, spec.min..=spec.max)
                    .logarithmic(spec.logarithmic)
                    .clamping(egui::SliderClamping::Never);
                if ui.add(slider).on_hover_text(spec.help).changed() {
                    changed = true;
                }
            }
        });
        if changed {
            if self.preset != "custom" && synth::preset(&self.preset).map(|p| Params { seed: self.params.seed, ..p }) != Some(self.params.clone()) {
                self.preset = "custom".into();
            }
            self.dirty = true;
            self.play_when_rendered = self.auto_play;
        }
    }

    fn plots(&mut self, ui: &mut egui::Ui) {
        ui.horizontal(|ui| {
            let can_play = self.audio.is_some() && !self.samples.is_empty();
            if ui.add_enabled(can_play, egui::Button::new("▶ Play")).clicked() {
                self.play();
            }
            if ui.add_enabled(self.audio.is_some(), egui::Button::new("■ Stop")).clicked()
                && let Some(audio) = &self.audio
            {
                audio.player.clear();
            }
            ui.checkbox(&mut self.auto_play, "Auto-play on change");
            ui.separator();
            if ui.add_enabled(!self.samples.is_empty(), egui::Button::new("Save WAV + JSON…")).clicked() {
                self.save_dialog();
            }
            if ui.button("Load JSON…").clicked() {
                self.load_dialog();
            }
            if self.rendering {
                ui.spinner();
            }
        });
        ui.label(&self.status);
        ui.separator();

        let a = &self.analysis;
        ui.label(format!(
            "Squeak (pitched) {:.0}% of moving time · median pitch {} · peak {:.2}",
            a.pitched_fraction * 100.0,
            a.median_pitch.map(|f| format!("{f:.0} Hz")).unwrap_or("—".into()),
            a.peak,
        ));

        let height = (ui.available_height() - 40.0) / 3.0;
        ui.label("Waveform");
        Plot::new("waveform").height(height).allow_scroll(false).show(ui, |plot| {
            plot.line(Line::new("waveform", a.envelope.clone()));
        });
        ui.label("Squeak pitch (Hz) — dots appear where the sound is periodic");
        Plot::new("pitch").height(height).allow_scroll(false).show(ui, |plot| {
            plot.points(Points::new("pitch", a.pitch.clone()).radius(2.0));
        });
        ui.label("Pin sliding speed (m/s) — squeak window sits near stribeck_speed");
        Plot::new("speed").height(height).allow_scroll(false).show(ui, |plot| {
            plot.line(Line::new("speed", a.speed.clone()));
            plot.hline(egui_plot::HLine::new("stribeck_speed", self.params.stribeck_speed));
        });
    }
}

impl eframe::App for App {
    fn ui(&mut self, ui: &mut egui::Ui, _frame: &mut eframe::Frame) {
        let ctx = ui.ctx().clone();
        while let Ok(result) = self.rx.try_recv() {
            if result.generation == self.generation {
                self.samples = result.samples;
                self.analysis = result.analysis;
                self.rendering = false;
                self.status = format!("Rendered {:.1} s in {} ms", self.params.duration, result.millis);
                if self.play_when_rendered {
                    self.play_when_rendered = false;
                    self.play();
                }
            }
        }
        // Re-render once the slider is released (keeps auto-play from stuttering)
        if self.dirty && !ctx.input(|i| i.pointer.any_down()) {
            self.start_render(&ctx);
        }

        egui::Panel::left("controls").default_size(330.0).resizable(true).show(ui, |ui| {
            self.controls(ui);
        });
        egui::CentralPanel::default().show(ui, |ui| {
            self.plots(ui);
        });

        if let Some(path) = &self.screenshot_path
            && !self.samples.is_empty()
            && !self.rendering
        {
            self.frames_since_render += 1;
            // A few frames lets plots settle their auto-bounds before capturing
            if self.frames_since_render == 5 {
                let path = path.clone();
                ctx.request_screenshot(move |image| {
                    match save_screenshot(&image, &path) {
                        Ok(()) => println!("Saved {}", path.display()),
                        Err(e) => eprintln!("Screenshot failed: {e}"),
                    }
                    std::process::exit(0);
                });
            }
            ctx.request_repaint();
        }
    }
}
