import json
import os
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from generate import (
    CATALOG_PATH,
    OUT_DIR as SFX_DIR,
    generate_audio_to_file,
    prompt_custom_sound,
    save_catalog,
)

load_dotenv()


def play_ambience(path: Path, volume: float) -> str:
    pygame.mixer.music.load(str(path))
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(loops=-1, fade_ms=600)
    return path.stem


def play_item(
    item: dict,
    ambience_vol: float,
    sfx_vol: float,
    active_ambience: str | None,
    sfx_cache: dict[str, pygame.mixer.Sound],
) -> str | None:
    path = SFX_DIR / f"{item['id']}.mp3"
    if not path.exists():
        print(f"File missing: {path}. Run `python generate.py` or use `[g]`.")
        return active_ambience

    if item["kind"] == "ambience":
        new_ambience = play_ambience(path, ambience_vol)
        print(f"Looping ambience: {item['label']}")
        return new_ambience

    snd = sfx_cache.get(item["id"])
    if snd is None:
        snd = pygame.mixer.Sound(str(path))
        snd.set_volume(sfx_vol)
        sfx_cache[item["id"]] = snd
    snd.play()
    print(f"Played SFX: {item['label']}")
    return active_ambience


def handle_generate_in_session(
    client: ElevenLabs | None,
    catalog: dict,
    items: list[dict],
    sfx_cache: dict[str, pygame.mixer.Sound],
    ambience_vol: float,
    sfx_vol: float,
    active_ambience: str | None,
) -> str | None:
    if client is None:
        print("Missing ELEVENLABS_API_KEY in environment or .env; cannot generate.\n")
        return active_ambience

    existing_ids = {entry["id"] for entry in items}
    new_item = prompt_custom_sound(existing_ids)
    if new_item is None:
        return active_ambience

    out_file = SFX_DIR / f"{new_item['id']}.mp3"
    try:
        print(f"[gen]  {new_item['id']} -> {out_file}")
        generate_audio_to_file(client, new_item, out_file)
    except Exception as exc:
        print(f"Generation failed: {exc}\n")
        return active_ambience

    items.append(new_item)
    catalog["sounds"] = items
    save_catalog(CATALOG_PATH, catalog)

    if new_item["kind"] == "sfx":
        snd = pygame.mixer.Sound(str(out_file))
        snd.set_volume(sfx_vol)
        sfx_cache[new_item["id"]] = snd

    print(f"[done] Saved {out_file} and added '{new_item['id']}' to catalog.json.\n")

    play_now = input("Play newly generated sound right now? [Y/n]: ").strip().lower()
    if play_now != "n":
        active_ambience = play_item(
            new_item,
            ambience_vol=ambience_vol,
            sfx_vol=sfx_vol,
            active_ambience=active_ambience,
            sfx_cache=sfx_cache,
        )

    return active_ambience


def main() -> None:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Catalog not found: {CATALOG_PATH}")

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    items = catalog.setdefault("sounds", [])

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    client = ElevenLabs(api_key=api_key) if api_key else None

    missing = [item["id"] for item in items if not (SFX_DIR / f"{item['id']}.mp3").exists()]
    if missing:
        print("Warning: missing audio files for:", ", ".join(missing))
        print("Run `python generate.py` or use `[g]` to generate them.\n")

    pygame.mixer.init()
    ambience_vol = 0.5
    sfx_vol = 0.85
    active_ambience: str | None = None
    sfx_cache: dict[str, pygame.mixer.Sound] = {}

    for item in items:
        path = SFX_DIR / f"{item['id']}.mp3"
        if item["kind"] == "sfx" and path.exists():
            snd = pygame.mixer.Sound(str(path))
            snd.set_volume(sfx_vol)
            sfx_cache[item["id"]] = snd

    print("DM Soundboard CLI ready. Enter a number to trigger a sound.")
    print("Commands: [g] generate sound | [s] stop ambience | [x] stop all SFX | [v] set volumes | [q] quit\n")

    while True:
        print(f"Active Ambience: {active_ambience or 'None'} (vol={ambience_vol:.2f}) | SFX vol={sfx_vol:.2f}")
        print("-" * 62)
        for idx, item in enumerate(items, start=1):
            exists = (SFX_DIR / f"{item['id']}.mp3").exists()
            status = "" if exists else " [MISSING]"
            tag = "LOOP" if item["kind"] == "ambience" else "1-SHOT"
            print(f"  {idx}. [{tag:6}] {item['scene']} — {item['label']}{status}")

        choice = input("\nSelect #: ").strip().lower()

        if choice == "q":
            pygame.mixer.quit()
            break
        if choice == "s":
            pygame.mixer.music.fadeout(400)
            active_ambience = None
            continue
        if choice == "x":
            pygame.mixer.stop()
            continue
        if choice == "v":
            try:
                ambience_vol = max(0.0, min(1.0, float(input("Ambience volume (0.0 - 1.0): "))))
                sfx_vol = max(0.0, min(1.0, float(input("SFX volume (0.0 - 1.0): "))))
                pygame.mixer.music.set_volume(ambience_vol)
                for snd in sfx_cache.values():
                    snd.set_volume(sfx_vol)
            except ValueError:
                print("Invalid number.")
            continue
        if choice == "g":
            active_ambience = handle_generate_in_session(
                client=client,
                catalog=catalog,
                items=items,
                sfx_cache=sfx_cache,
                ambience_vol=ambience_vol,
                sfx_vol=sfx_vol,
                active_ambience=active_ambience,
            )
            continue

        if not choice.isdigit():
            print("Unknown command.")
            continue

        idx = int(choice) - 1
        if idx < 0 or idx >= len(items):
            print("Selection out of range.")
            continue

        item = items[idx]
        active_ambience = play_item(
            item=item,
            ambience_vol=ambience_vol,
            sfx_vol=sfx_vol,
            active_ambience=active_ambience,
            sfx_cache=sfx_cache,
        )


if __name__ == "__main__":
    main()

