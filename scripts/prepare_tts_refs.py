import json
import subprocess
from collections import defaultdict
from pathlib import Path

MIN_SEGMENT_SECONDS = 2.0
MAX_CLIPS_PER_SPEAKER = 5
TARGET_TOTAL_SECONDS = 20.0


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    diarization = json.loads(Path("diarization.json").read_text(encoding="utf-8"))
    out_dir = Path("tts_refs")
    out_dir.mkdir(exist_ok=True)

    by_speaker = defaultdict(list)
    for row in diarization:
        speaker = row.get("speaker") or "UNKNOWN"
        start = float(row["start"])
        end = float(row["end"])
        duration = end - start
        if duration >= MIN_SEGMENT_SECONDS:
            by_speaker[speaker].append({"start": start, "end": end, "duration": duration})

    manifest = {}
    for speaker, segs in by_speaker.items():
        segs = sorted(segs, key=lambda x: x["duration"], reverse=True)
        chosen = []
        total = 0.0
        for seg in segs:
            if len(chosen) >= MAX_CLIPS_PER_SPEAKER or total >= TARGET_TOTAL_SECONDS:
                break
            chosen.append(seg)
            total += seg["duration"]

        speaker_dir = out_dir / speaker
        speaker_dir.mkdir(exist_ok=True)
        clip_paths = []
        for idx, seg in enumerate(chosen, 1):
            clip_path = speaker_dir / f"clip_{idx:02}.wav"
            run([
                "ffmpeg", "-y",
                "-i", "audio.wav",
                "-ss", str(seg["start"]),
                "-to", str(seg["end"]),
                "-ac", "1",
                "-ar", "24000",
                str(clip_path),
            ])
            clip_paths.append(str(clip_path))

        manifest[speaker] = {
            "clips": clip_paths,
            "selected_seconds": round(total, 3),
            "clip_count": len(clip_paths),
        }

    Path("tts_refs_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
