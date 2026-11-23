import argparse
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

BASE_DIR = Path(__file__).parent
CATALOG_PATH = BASE_DIR / "catalog.json"
OUT_DIR = BASE_DIR / "sfx_library"


def slugify_id(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "custom_sound"


def unique_sound_id(base_id: str, existing_ids: set[str]) -> str:
    if base_id not in existing_ids:
        return base_id
    counter = 2
    while f"{base_id}_{counter}" in existing_ids:
        counter += 1
    return f"{base_id}_{counter}"


def save_catalog(catalog_path: Path, catalog: dict) -> None:
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


def generate_audio_to_file(client: ElevenLabs, item: dict, out_file: Path) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    audio_stream = client.text_to_sound_effects.convert(
        text=item["prompt"],
        model_id="eleven_text_to_sound_v3",
        duration_seconds=item.get("duration_seconds"),
        loop=item.get("loop", False),
        prompt_influence=item.get("prompt_influence", 0.4),
    )
    with open(out_file, "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)


def prompt_custom_sound(existing_ids: set[str]) -> dict | None:
    print("\n--- Custom Sound Generator ---")
    prompt = input("Sound prompt (blank to cancel): ").strip()
    if not prompt:
        print("Cancelled.")
        return None

    mode_choice = input("Mode - [s] one-shot SFX (default) or [a] looping ambience: ").strip().lower()
    is_ambience = mode_choice == "a"
    kind = "ambience" if is_ambience else "sfx"

    scene = input("Scene [Custom]: ").strip() or "Custom"
    label = input("Label [Custom Sound]: ").strip() or "Custom Sound"

    duration_seconds: float | None = None
    if is_ambience:
        raw_dur = input("Loop duration in seconds (0.1 - 30, default 15): ").strip()
        if not raw_dur:
            duration_seconds = 15.0
        else:
            try:
                parsed = float(raw_dur)
                if not (0.1 <= parsed <= 30.0):
                    print("Duration must be between 0.1 and 30 seconds. Cancelled.")
                    return None
                duration_seconds = parsed
            except ValueError:
                print("Invalid duration. Cancelled.")
                return None
        est_cost = f"~{round(duration_seconds * 40)} credits ({duration_seconds}s @ ~40 credits/s)"
        dur_display = f"{duration_seconds}s (looping)"
    else:
        est_cost = "variable / short one-shot (auto duration)"
        dur_display = "auto (one-shot)"

    print("\nSummary before API call:")
    print(f"  Prompt   : {prompt}")
    print(f"  Mode     : {kind} (loop={is_ambience})")
    print(f"  Duration : {dur_display}")
    print(f"  Est. Cost: {est_cost}")

    confirm = input("Proceed with ElevenLabs API call? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled. Zero credits used.")
        return None

    base_id = slugify_id(f"{scene}_{label}")
    sound_id = unique_sound_id(base_id, existing_ids)

    return {
        "id": sound_id,
        "scene": scene,
        "label": label,
        "kind": kind,
        "loop": is_ambience,
        "duration_seconds": duration_seconds,
        "prompt_influence": 0.4,
        "prompt": prompt,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate DM sound effects via ElevenLabs.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing audio files.")
    parser.add_argument("--custom", action="store_true", help="Interactively generate and catalog a custom sound.")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ELEVENLABS_API_KEY in environment or .env")

    if CATALOG_PATH.exists():
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    else:
        catalog = {"sounds": []}

    items = catalog.setdefault("sounds", [])
    client = ElevenLabs(api_key=api_key)

    if args.custom:
        existing_ids = {entry["id"] for entry in items}
        new_item = prompt_custom_sound(existing_ids)
        if new_item is None:
            return
        out_file = OUT_DIR / f"{new_item['id']}.mp3"
        print(f"[gen]  {new_item['id']} -> {out_file}")
        generate_audio_to_file(client, new_item, out_file)
        items.append(new_item)
        save_catalog(CATALOG_PATH, catalog)
        print(f"[done] Saved {out_file} and added '{new_item['id']}' to catalog.json.")
        return

    for item in items:
        out_file = OUT_DIR / f"{item['id']}.mp3"
        if out_file.exists() and not args.force:
            print(f"[skip] {item['id']} -> already cached")
            continue

        print(f"[gen]  {item['id']} (loop={item['loop']}, duration={item['duration_seconds']})...")
        generate_audio_to_file(client, item, out_file)
        print(f"[done] saved {out_file}")


if __name__ == "__main__":
    main()
