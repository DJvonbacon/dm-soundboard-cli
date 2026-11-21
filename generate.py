import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

BASE_DIR = Path(__file__).parent
CATALOG_PATH = BASE_DIR / "catalog.json"
OUT_DIR = BASE_DIR / "sfx_library"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate DM sound effects via ElevenLabs.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing audio files.")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ELEVENLABS_API_KEY in environment or .env")

    OUT_DIR.mkdir(exist_ok=True)
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    client = ElevenLabs(api_key=api_key)

    for item in catalog["sounds"]:
        out_file = OUT_DIR / f"{item['id']}.mp3"
        if out_file.exists() and not args.force:
            print(f"[skip] {item['id']} -> already cached")
            continue

        print(f"[gen]  {item['id']} (loop={item['loop']}, duration={item['duration_seconds']})...")
        audio_stream = client.text_to_sound_effects.convert(
            text=item["prompt"],
            model_id="eleven_text_to_sound_v3",
            duration_seconds=item.get("duration_seconds"),
            loop=item.get("loop", False),
            prompt_influence=item.get("prompt_influence", 0.3),
        )

        with open(out_file, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        print(f"[done] saved {out_file}")


if __name__ == "__main__":
    main()
