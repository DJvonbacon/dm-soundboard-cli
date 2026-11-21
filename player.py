import json
import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

BASE_DIR = Path(__file__).parent
CATALOG_PATH = BASE_DIR / "catalog.json"
SFX_DIR = BASE_DIR / "sfx_library"


def play_ambience(path: Path, volume: float) -> str:
    pygame.mixer.music.load(str(path))
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(loops=-1, fade_ms=600)
    return path.stem


def main() -> None:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Catalog not found: {CATALOG_PATH}")

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    items = catalog["sounds"]

    missing = [item["id"] for item in items if not (SFX_DIR / f"{item['id']}.mp3").exists()]
    if missing:
        print("Warning: missing audio files for:", ", ".join(missing))
        print("Run `python generate.py` first to generate them.\n")

    pygame.mixer.init()
    ambience_vol = 0.5
    sfx_vol = 0.85
    active_ambience = None
    sfx_cache: dict[str, pygame.mixer.Sound] = {}

    for item in items:
        path = SFX_DIR / f"{item['id']}.mp3"
        if item["kind"] == "sfx" and path.exists():
            snd = pygame.mixer.Sound(str(path))
            snd.set_volume(sfx_vol)
            sfx_cache[item["id"]] = snd

    print("DM Soundboard CLI ready. Enter a number to trigger a sound.")
    print("Commands: [s] stop ambience | [x] stop all SFX | [v] set volumes | [q] quit\n")

    while True:
        print(f"Active Ambience: {active_ambience or 'None'} (vol={ambience_vol:.2f}) | SFX vol={sfx_vol:.2f}")
        print("-" * 58)
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

        if not choice.isdigit():
            print("Unknown command.")
            continue

        idx = int(choice) - 1
        if idx < 0 or idx >= len(items):
            print("Selection out of range.")
            continue

        item = items[idx]
        path = SFX_DIR / f"{item['id']}.mp3"
        if not path.exists():
            print(f"File missing: {path}. Run `python generate.py`.")
            continue

        if item["kind"] == "ambience":
            active_ambience = play_ambience(path, ambience_vol)
            print(f"Looping ambience: {item['label']}")
        else:
            snd = sfx_cache.get(item["id"])
            if snd is None:
                snd = pygame.mixer.Sound(str(path))
                snd.set_volume(sfx_vol)
                sfx_cache[item["id"]] = snd
            snd.play()
            print(f"Played SFX: {item['label']}")


if __name__ == "__main__":
    main()
