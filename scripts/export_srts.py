import json
from collections import defaultdict
from pathlib import Path


def srt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def write_srt(entries, path: Path):
    lines = []
    for idx, e in enumerate(entries, 1):
        lines.append(str(idx))
        lines.append(f"{srt_ts(e['start'])} --> {srt_ts(e['end'])}")
        lines.append(e['text'].strip())
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    data = json.loads(Path("transcript_speakers.json").read_text(encoding="utf-8"))
    segments = data.get("segments", [])

    general = [
        {"start": s["start"], "end": s["end"], "text": s["text"]}
        for s in segments if s.get("text", "").strip()
    ]
    write_srt(general, Path("original.srt"))

    by_speaker = defaultdict(list)
    for s in segments:
        speaker = s.get("speaker") or "UNKNOWN"
        text = s.get("text", "").strip()
        if not text:
            continue
        by_speaker[speaker].append({"start": s["start"], "end": s["end"], "text": text})

    out_dir = Path("speaker_srts")
    out_dir.mkdir(exist_ok=True)
    manifest = {}
    for speaker, entries in by_speaker.items():
        path = out_dir / f"{speaker}.srt"
        write_srt(entries, path)
        manifest[speaker] = str(path)

    Path("speaker_srts_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
