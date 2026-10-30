#!/usr/bin/env python3
"""
Write the demo site's pages (called by tools/build_site.sh after audio and analysis exist).

    site/index.html      TOC, Part 1 players, Part 2 players, Details (summary + links)
    site/hinge-lab.html  Detail page: the physics model (screenshot + preset players)

The full reference analysis (site/analysis/index.html) is written by squeak_analysis.py;
this script adds the GitHub corner and footer to it as well.

Build info for the footer comes from the environment (set by build_site.sh):
BUILD_HOST, BUILD_SHA, BUILD_DIRTY (1 if the tree had uncommitted changes), BUILD_TIME.
"""

import html
import json
import os
import sys
from pathlib import Path

REPO = 'https://github.com/softwarewrighter/text-to-sfx-gen'
SOURCE_URL = 'https://www.youtube.com/watch?v=TspuiaFX2YQ'
SOURCE_TITLE = 'Squeaky Door Hinge Opening Sound Effects (SoundEffectsFactory, YouTube)'

# Part 1: (file in audio/part1, name, description)
PART1 = [
    ('thud.wav', 'Thud', '0.5 s. Click, a pitch-dropping body and a mid-range knock. Revised 2026-10: '
     'the original was almost all below 100 Hz and silent on laptop speakers.'),
    ('button_click.wav', 'Button click', '50 ms. High-frequency (2–4 kHz) blip with an instant decay.'),
    ('explosion.wav', 'Explosion', 'Low rumble (20–50 Hz) plus broadband noise and a long decay.'),
    ('flying_saucer_doppler.wav', 'Flying saucer', 'Rise-and-fall sweep with a metallic '
     'texture, passing by with Doppler shift.'),
    ('gravel_footsteps.wav', 'Gravel footsteps', 'Stone impacts per step, irregular timing, '
     'panned left to right (use headphones).'),
    ('siren.wav', 'Siren (basic)', 'Two alternating tones, 500/800 Hz.'),
    ('siren_us_wail_doppler.wav', 'Siren (US wail + Doppler)', 'Wail sweep moving past the '
     'listener.'),
    ('siren_eu_hilo_doppler.wav', 'Siren (EU hi-lo + Doppler)', 'European two-tone moving past.'),
    ('door_creak.wav', '"Door creak"', 'The first door creak attempt. It sounds like wind, and '
     'was later renamed "wind whistling".'),
    ('hinge_creak.wav', 'Hinge creak', 'The first stick-slip hinge attempt: noise bursts plus '
     'a separate tone. Not convincing.'),
]

CATEGORY_ORDER = ['stepped squeak', 'gliding squeak', 'squeak → creak', 'creak / ratchet',
                  'low groan']
CATEGORY_HELP = {
    'stepped squeak': 'steady pitches with sudden jumps between them',
    'gliding squeak': 'one continuous pitch slide',
    'squeak → creak': 'a clean squeak that breaks into separate clicks',
    'creak / ratchet': 'mostly individual clicks',
    'low groan': 'low and wobbly',
}

HINGE_PRESETS = ['squeaky', 'oiled', 'horror_slow', 'rusty_groan', 'fast_swing', 'cabinet_tiny']


def page(title, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
{body}
</body>
</html>
"""


# "GitHub Corners" by Tim Holman (MIT), https://github.com/tholman/github-corners
GITHUB_CORNER = f"""<a href="{REPO}" class="github-corner" aria-label="View source on GitHub" target="_blank" rel="noopener"><svg viewBox="0 0 250 250" aria-hidden="true"><path d="M0,0 L115,115 L130,115 L142,142 L250,250 L250,0 Z"></path><path d="M128.3,109.0 C113.8,99.7 119.0,89.6 119.0,89.6 C122.0,82.7 120.5,78.6 120.5,78.6 C119.2,72.0 123.4,76.3 123.4,76.3 C127.3,80.9 125.5,87.3 125.5,87.3 C122.9,97.6 130.6,101.9 134.4,103.2" fill="currentColor" style="transform-origin:130px 106px;" class="octo-arm"></path><path d="M115.0,115.0 C114.9,115.1 118.7,116.5 119.8,115.4 L133.7,101.6 C136.9,99.2 139.9,98.4 142.2,98.6 C133.8,88.0 127.5,74.4 143.8,58.0 C148.5,53.4 154.0,51.2 159.7,51.0 C160.3,49.4 163.2,43.6 171.4,40.1 C171.4,40.1 176.1,42.5 178.8,56.2 C183.1,58.6 187.2,61.8 190.9,65.4 C194.5,69.0 197.7,73.2 200.1,77.6 C213.8,80.2 216.3,84.9 216.3,84.9 C212.7,93.1 206.9,96.0 205.4,96.6 C205.1,102.4 203.0,107.8 198.3,112.5 C181.9,128.9 168.3,122.5 157.7,114.1 C157.9,116.9 156.7,120.9 152.7,124.9 L141.0,136.5 C139.8,137.7 141.6,141.9 141.8,141.8 Z" fill="currentColor" class="octo-body"></path></svg></a>"""


# Corner and footer follow the sw-comp-history/ibm-1130-rs layout: fixed corner top right,
# fixed footer bar (license, copyright, links on the left; host | sha | time on the right).
# Inline so the analysis page (which has its own stylesheet) gets the same look.
CHROME_CSS = """<style>
.github-corner{position:fixed;top:0;right:0;z-index:1000}
.github-corner svg{fill:#24292e;color:#fff;width:60px;height:60px}
.github-corner:hover .octo-arm{animation:octocat-wave 560ms ease-in-out}
@keyframes octocat-wave{0%,100%{transform:rotate(0)}20%,60%{transform:rotate(-25deg)}40%,80%{transform:rotate(10deg)}}
.app-footer{position:fixed;bottom:0;left:0;right:0;background:#f6f8fa;color:#666;padding:4px 10px;
  font-size:12px;display:flex;justify-content:space-between;align-items:center;
  border-top:1px solid #ddd;z-index:100;font-family:system-ui,sans-serif}
.footer-left,.footer-right{display:flex;gap:15px}
.app-footer a{color:#0366d6;text-decoration:none}
.app-footer a:hover{text-decoration:underline}
body{padding-bottom:40px}
</style>"""


def footer():
    host = html.escape(os.environ.get('BUILD_HOST', 'unknown'))
    sha = os.environ.get('BUILD_SHA', 'unknown')
    built = html.escape(os.environ.get('BUILD_TIME', 'unknown'))
    if sha == 'unknown':
        commit = 'unknown'
    elif os.environ.get('BUILD_DIRTY') == '1':
        commit = f'{html.escape(sha[:7])}-dirty'
    else:
        commit = f'<a href="{REPO}/commit/{sha}">{html.escape(sha[:7])}</a>'
    return f"""<footer class="app-footer">
  <div class="footer-left">
    <a href="{REPO}/blob/main/LICENSE">MIT License</a>
    <span>&copy; 2026 Michael A Wright</span>
    <a href="https://software-wrighter-lab.github.io/">Blog</a>
    <a href="https://discord.com/invite/Ctzk5uHggZ">Discord</a>
    <a href="https://www.youtube.com/@SoftwareWrighter">YouTube</a>
  </div>
  <div class="footer-right"><span>{host} | {commit} | {built}</span></div>
</footer>"""


def decorate(page_html):
    """Add the GitHub corner after <body> and the footer before </body>."""
    page_html = page_html.replace('</head>', CHROME_CSS + '</head>', 1)
    page_html = page_html.replace('<body>', '<body>' + GITHUB_CORNER, 1)
    return page_html.replace('</body>', footer() + '</body>', 1)


def player(src):
    return f'<audio controls preload="metadata" src="{src}"></audio>'


def index_page(rows):
    part1 = ''.join(
        f'<tr><td><b>{name}</b><br><span class="desc">{desc}</span></td>'
        f'<td>{player("audio/part1/" + f)}</td></tr>' for f, name, desc in PART1)

    by_cat = {c: [r for r in rows if r['category'] == c] for c in CATEGORY_ORDER}
    part2 = ''
    for cat in CATEGORY_ORDER:
        if not by_cat[cat]:
            continue
        items = ''
        for r in by_cat[cat]:
            n = r['id']
            items += (f'<tr><td>#{n}</td><td>{r["features"]["duration_s"]:.1f} s</td>'
                      f'<td>{player(f"analysis/ev{n}_resynth.wav")}</td>'
                      f'<td><a href="analysis/index.html#ev{n}">analysis</a></td></tr>')
        part2 += (f'<h3>{html.escape(cat)} <span class="desc">— {CATEGORY_HELP[cat]}</span></h3>'
                  f'<table class="compact">{items}</table>')

    body = f"""<header>
  <h1>Text-to-SFX: procedural sound effects</h1>
  <p class="subtitle">Sound effects made by code, not by AI models. AI agents researched the
  sounds and wrote the code; the code uses only math, so every sound here is MIT-licensed.</p>
  <nav class="toc"><b>Contents:</b>
    <a href="#part1">1. First attempt</a>
    <a href="#part2">2. Second attempt</a>
    <a href="#details">3. Details</a>
    <a href="{REPO}">Source on GitHub</a></nav>
</header>

<section id="part1">
<h2>1. First attempt (2026-02)</h2>
<p>An AI coding agent (opencode with GLM-4.7) wrote one Python generator per sound, using sine
waves, noise, filters and envelopes. Simple sounds came out well; the door sounds did not.</p>
<table>{part1}</table>
</section>

<section id="part2">
<h2>2. Second attempt: the squeaky hinge (2026-10)</h2>
<p>With Claude Code (Claude Opus 5.5), we researched friction acoustics, built a physical model,
then measured {len(rows)} real squeaks. Real squeaks turned out to be sequences of parts: steady
pitches with sudden jumps, glides, and clean stretches that break into clicks, all driven by
sharp stick-slip pulses. Each sound below is generated by our code from those measurements.</p>
{part2}
</section>

<section id="details">
<h2>3. Details</h2>
<ul class="details">
  <li><b>Reference recording:</b> <a href="{SOURCE_URL}">{html.escape(SOURCE_TITLE)}</a>.
  It is not redistributed here (unclear provenance); the analysis page links each squeak to its
  timestamp in the video.</li>
  <li><b><a href="analysis/index.html">Full analysis of the {len(rows)} squeaks</a>:</b>
  spectrograms with measured pitch, five categories, a feature table, and how each rebuild
  compares with the original.
  <br><a href="analysis/index.html"><img class="thumb" src="images/analysis-overview.png"
  alt="Category comparison plots"></a></li>
  <li><b><a href="hinge-lab.html">The physics model (Hinge Lab)</a>:</b> a Rust app with
  sliders that simulates stick-slip friction. Physically right (it squeaks only within a speed
  window, and oil silences it) but it sounded too smooth, which is what led to measuring real
  squeaks.</li>
  <li><b><a href="{REPO}/blob/main/docs/domain-expertise.md">Research briefing</a>:</b> the
  physics of squeaks and creaks, with equations and primary sources (Akay 2002; Avanzini,
  Serafin &amp; Rocchesso 2002; Farnell 2010).</li>
  <li><b><a href="{REPO}/blob/main/docs/phases.md">Status and next steps</a>:</b> what remains
  for each part.</li>
</ul>
<p class="desc">All audio on this site is generated by this project's code (MIT).</p>
</section>
"""
    return page('Text-to-SFX: procedural sound effects', body)


def hinge_page():
    rows = ''.join(
        f'<tr><td>{p}</td><td>{player(f"audio/hinge/{p}.wav")}</td>'
        f'<td><a href="audio/hinge/{p}.json">{p}.json</a></td></tr>' for p in HINGE_PRESETS)
    body = f"""<header>
  <h1>The physics model: Hinge Lab</h1>
  <nav class="toc"><a href="index.html">← Back to the demo</a>
  <a href="{REPO}/tree/main/hinge-lab">Source</a></nav>
</header>
<p>Hinge Lab simulates elasto-plastic stick-slip friction between the hinge pin and barrel,
driving hinge and door-leaf resonances, radiated through a wood panel and door frame. Sliders
re-render in about 0.1 s, and the same parameters plus seed always give the same sound.</p>
<img src="images/hinge-lab-ui.png" alt="Hinge Lab UI">
<h2>Presets</h2>
<p>Each JSON file reproduces its sound exactly.</p>
<table>{rows}</table>
<p class="note">These behave correctly physically, but each is one smooth, slowly gliding tone
with few overtones, unlike a real door. Measuring real squeaks
(<a href="analysis/index.html">analysis</a>) showed what was missing.</p>
"""
    return page('Hinge Lab', body)


def main():
    site = Path(sys.argv[1])
    rows = json.loads((site / 'analysis' / 'analysis.json').read_text())
    (site / 'index.html').write_text(decorate(index_page(rows)))
    (site / 'hinge-lab.html').write_text(decorate(hinge_page()))
    analysis = site / 'analysis' / 'index.html'
    analysis.write_text(decorate(analysis.read_text()))


if __name__ == '__main__':
    main()
