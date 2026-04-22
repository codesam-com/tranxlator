import json
from collections import defaultdict
from pathlib import Path

from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

MODEL_NAME = "facebook/m2m100_418M"
LANG_MAP = {
    "en": "en",
    "es": "es",
}


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


def batch_translate(texts, src_lang: str, tgt_lang: str):
    tokenizer = M2M100Tokenizer.from_pretrained(MODEL_NAME)
    model = M2M100ForConditionalGeneration.from_pretrained(MODEL_NAME)
    tokenizer.src_lang = src_lang
    translated = []
    batch_size = 8
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        encoded = tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
        generated = model.generate(**encoded, forced_bos_token_id=tokenizer.get_lang_id(tgt_lang), max_length=512)
        translated.extend(tokenizer.batch_decode(generated, skip_special_tokens=True))
    return translated


def main():
    speakers_data = json.loads(Path("transcript_speakers.json").read_text(encoding="utf-8"))
    metrics = json.loads(Path("metrics_transcribe.json").read_text(encoding="utf-8"))

    src = LANG_MAP.get(metrics.get("language"))
    tgt = "es"
    if src is None:
        raise SystemExit(f"Unsupported source language for translation: {metrics.get('language')}")

    segments = speakers_data.get("segments", [])
    texts = [seg.get("text", "").strip() for seg in segments]
    translations = batch_translate(texts, src, tgt)

    translated_segments = []
    for seg, translated in zip(segments, translations):
        translated_segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "speaker": seg.get("speaker"),
            "source_text": seg.get("text", ""),
            "text": translated,
        })

    Path("translated_segments.json").write_text(
        json.dumps({"segments": translated_segments}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    general = [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in translated_segments if s["text"].strip()]
    write_srt(general, Path("translated_es.srt"))

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

    Path("speaker_srts_es_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
