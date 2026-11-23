# DM Soundboard CLI

A lightweight, credit-conscious command-line soundboard built in Python for tabletop D&D sessions. It pre-caches ambient loops and one-shot sound effects locally via the ElevenLabs Sound Effects API and plays them back with low latency using `pygame-ce`.

## Features
- **Local Audio Caching:** Generated MP3s are stored in `sfx_library/` and indexed in `catalog.json` so you never spend API credits twice on the same sound.
- **Interactive Soundboard (`player.py`):** Trigger one-shot SFX on top of seamless looping ambience, adjust volumes on the fly, and generate new custom sounds mid-session (`[g]`).
- **Batch & Custom CLI Generation (`generate.py`):** Pre-generate everything in `catalog.json` or create one-off custom sounds with `--custom`.
- **Credit Safeguards:** Every interactive generation shows the prompt, mode (`sfx` vs. `ambience`), duration, and estimated credit cost with an explicit `[y/N]` confirmation before calling ElevenLabs.

## Setup (macOS)

1. **Clone the repository and enter the directory:**
   ```bash
   git clone [https://github.com/DJvonbacon/dm-soundboard-cli.git](https://github.com/DJvonbacon/dm-soundboard-cli.git)
   cd dm-soundboard-cli

2. **Create and activate a virtual environment:**
   '''bash
   python3 -m venv .venv
   source .venv/bin/activate

3. **Install dependencies**
   '''bash
   pip install pygame-ce elevenlabs python-dotenv

4. **Configure your ElevenLabs API key:**
   '''bash
   ELEVENLABS_API_KEY=your_api_key_here

##Usage
In-session controls:
1–N: Play a one-shot SFX or switch the active looping ambience
[g]: Generate a new custom sound mid-session (with credit confirmation & immediate playback)
[s]: Fade out and stop active ambience
[x]: Stop all active one-shot SFX
[v]: Adjust ambience and SFX volumes (0.0 – 1.0)
[q]: Quit the soundboard

##Project Structure
player.py — Interactive CLI playback loop and in-session [g] generator
generate.py — Batch catalog generator and --custom interactive helper
catalog.json — Sound metadata (ID, scene, label, mode, duration, prompt)
sfx_library/ — Local MP3 cache (git-ignored)

.env — Local ElevenLabs API key (git-ignored)
