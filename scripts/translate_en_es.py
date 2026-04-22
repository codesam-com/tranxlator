import json
from collections import defaultdict
from pathlib import Path
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_NAME = "Helsinki-NLP/opus-mt-en-es"


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


def batch_translate(texts):
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    out = []
    for i in range(0, len(texts), 8):
        batch = texts[i:i+8]
        enc = tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
        gen = model.generate(**enc, max_length=512)
        out.extend(tokenizer.batch_decode(gen, skip_special_tokens=True))
    return out


def main():
    data = json.loads(Path("transcript_speakers.json").read_text(encoding="utf-8"))
    segments = data.get("segments", [])
    texts = [seg.get("text", "").strip() for seg in segments]
    translations = batch_translate(texts)

    translated_segments = []
    for seg, translated in zip(segments, translations):
        translated_segments.append({"start": seg["start"], "end": seg["end"], "speaker": seg.get("speaker"), "source_text": seg.get("text", ""), "text": translated})

    Path("translated_segments.json").write_text(json.dumps({"segments": translated_segments}, indent=2, ensure_ascii=False), encoding="utf-8")
    write_srt([{"start": s["start"], "end": s["end"], "text": s["text"]} for s in translated_segments if s["text"].strip()], Path("translated_es.srt"))

    by_speaker = defaultdict(list)
    for s in translated_segments:
        if s["text"].strip():
            by_speaker[s.get("speaker") or "UNKNOWN"].append({"start": s["start"], "end": s["end"], "text": s["text"]})

    out_dir = Path("speaker_srts_es")
    out_dir.mkdir(exist_ok=True)
    manifest = {}
    for speaker, entries in by_speaker.items():
        path = out_dir / f"{speaker}.srt"
        write_srt(entries, path)
        manifest[speaker] = str(path)

    Path("speaker_srts_es_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
